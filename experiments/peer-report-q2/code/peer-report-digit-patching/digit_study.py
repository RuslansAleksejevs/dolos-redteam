"""Corrected fixed-history digit patches and direct attention-value interventions."""
import argparse,csv,hashlib,inspect,json,math,os,re,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def spans(tok,row):
    enc=tok(row['prompt'],return_offsets_mapping=True);out={}
    for key,pat in [('truth',r'true count is (\d+) units'),('peer',r'"arguments": \{"(?:count|minutes)": (\d+)\}')]:
        m=re.search(pat,row['prompt'])
        out[key]=[] if m is None else [i for i,(a,b) in enumerate(enc.offset_mapping) if a<m.end(1) and b>m.start(1)]
    L=len(row['input_ids']);out.update(colon=[L-1],first_digit=[L],second_digit=[L+1],both_digits=[L,L+1])
    assert len(out['truth'])==2
    if row['cond']!='no_peer':assert len(out['peer'])==2
    return out

class Runner:
    def __init__(self,model,tok):
        import torch
        from transformers.models.qwen2 import modeling_qwen2 as qm
        self.torch=torch;self.model=model;self.tok=tok;self.qm=qm;self.plan=None;self.calls=0;self.norms=[]
        self.original_attention=qm.eager_attention_forward
    def install(self):
        self.model.set_attn_implementation('eager')
        self.qm.eager_attention_forward=self.attention
    def close(self):self.qm.eager_attention_forward=self.original_attention
    def attention(self,module,query,key,value,attention_mask,*args,**kwargs):
        torch=self.torch
        output,w=self.original_attention(module,query,key,value,attention_mask,*args,**kwargs)
        plan=self.plan
        if plan is None or (plan['layer']!='all' and module.layer_idx!=plan['layer']):return output,w
        sources=self.current_spans[plan['source']]
        self.calls+=1
        if not sources or plan.get('strength',1)==0:return output,w
        qpos=self.current_spans['both_digits'];v=self.qm.repeat_kv(value,module.num_key_value_groups)
        # Keep original attention probabilities: subtract their additive value term,
        # without changing normalization or redistributing attention to other tokens.
        delta=(w[:,:,qpos,:][:,:,:,sources] @ v[:,:,sources,:]).transpose(1,2).contiguous()
        flat=delta.reshape(delta.shape[0],delta.shape[1],-1)
        projected=torch.nn.functional.linear(flat,module.o_proj.weight)
        actual_norm=projected.norm(dim=-1,keepdim=True)
        if plan.get('random',False):
            gen=torch.Generator(device=query.device);gen.manual_seed(513022+module.layer_idx)
            # Same random direction for candidate paths; norm is matched per path/query.
            rnd=torch.randn((1,flat.shape[1],flat.shape[2]),generator=gen,device=flat.device,dtype=flat.dtype).expand_as(flat)
            projected_random=torch.nn.functional.linear(rnd,module.o_proj.weight)
            rnd=rnd*(actual_norm/projected_random.norm(dim=-1,keepdim=True).clamp_min(1e-30))
            delta=rnd.reshape_as(delta)
            check=torch.nn.functional.linear(rnd,module.o_proj.weight).norm(dim=-1,keepdim=True)
            self.norms.append(float(((check-actual_norm).abs()/(actual_norm+1e-20)).max().item()))
        out=output.clone();out[:,qpos,:,:]-=plan.get('strength',1)*delta
        return out,w
    def run(self,row,values,capture=False,patch=None,ablate=None):
        torch=self.torch;tok=self.tok;L=len(row['input_ids']);seqs=[];suffixes=[]
        for value in values:
            ids=tok(row['prompt']+' '+str(value)).input_ids
            assert ids[:L]==row['input_ids'];suffix=ids[L:]
            assert len(suffix)==3 and suffix[0]==220 and tok.decode(suffix)==' '+str(value)
            seqs.append(ids);suffixes.append(suffix)
        assert len({len(x) for x in seqs})==1
        self.current_spans=spans(tok,row);self.plan=ablate;handles=[];states={}
        if capture:
            for li,layer in enumerate(self.model.model.layers):
                def save(mod,inp,out,li=li):
                    h=out[0] if isinstance(out,tuple) else out
                    states[li]=h[:,[L-1,L,L+1],:].detach().cpu().clone()
                handles.append(layer.register_forward_hook(save))
        if patch:
            layer,site,donor=patch;ix={'colon':[0],'first_digit':[1],'second_digit':[2],'both_digits':[1,2]}[site]
            pos=[L-1+i for i in ix]
            def replace(mod,inp,out):
                h=out[0] if isinstance(out,tuple) else out;h=h.clone();h[:,pos,:]=donor[:,ix,:].to(h.device,h.dtype)
                return (h,)+out[1:] if isinstance(out,tuple) else h
            handles.append(self.model.model.layers[layer].register_forward_hook(replace))
        try:
            with torch.inference_mode():
                h=self.model.model(input_ids=torch.tensor(seqs,device='cuda'),use_cache=False).last_hidden_state
                z=self.model.lm_head(h[:,L-1:L+2,:]).float().log_softmax(-1)
                token_scores=[[z[i,j,t].item() for j,t in enumerate(s)] for i,s in enumerate(suffixes)]
                scores=[sum(x) for x in token_scores]
        finally:
            for handle in handles:handle.remove()
            self.plan=None
        return {'values':values,'logps':scores,'token_logps':token_scores},states

def main(args):
    if not os.environ.get('RUNPOD_POD_ID'):raise RuntimeError('RunPod-only model computation; laptop GPU prohibited')
    import torch,model_io,transformers
    torch.manual_seed(513022);torch.backends.cuda.matmul.allow_tf32=False;torch.set_num_threads(8)
    out=ROOT/'results';out.mkdir(exist_ok=True)
    source=json.loads((ROOT/'source/counterfactual_inputs.json').read_text())
    selected=json.loads((ROOT/'source/frozen_selection.json').read_text())
    by={(r['id'],r['variant'],r['cond']):r for r in source}
    tok=model_io.tokenizer();model=model_io.load_model(args.model,torch.device('cuda'),torch.float32)
    runner=Runner(model,tok);checks=[];align=[];start=time.time()
    result_path=out/f'{args.model}_{args.stage}.jsonl'
    def emit(record):
        with result_path.open('a') as f:f.write(json.dumps(dict(model=args.model,**record))+'\n')
    assert not result_path.exists(),'Refusing to overwrite completed or partial results'
    first=by[(selected[0]['id'],'A','peer_ai')];values=[first['truth'],first['peer']]
    sdpa,_=runner.run(first,values)
    runner.install();eager,_=runner.run(first,values)
    err=max(abs(a-b) for a,b in zip(sdpa['logps'],eager['logps']))
    checks.append({'check':'sdpa_vs_eager','max_logp_error':err});assert err<.001,checks[-1]
    zero,_=runner.run(first,values,ablate={'source':'peer','layer':'all','strength':0})
    err=max(abs(a-b) for a,b in zip(zero['logps'],eager['logps']))
    checks.append({'check':'zero_strength_attention','max_logp_error':err});assert err==0
    try:
        if args.stage=='residual':
            for sel in selected:
                target=by[(sel['id'],'A','peer_ai')]
                for kind,variant,cond in [('peer','B','peer_ai'),('truth','C','peer_ai'),('action','A','unrelated')]:
                    donor=by[(sel['id'],variant,cond)]
                    changed=donor['peer'] if kind=='peer' else donor['truth'] if kind=='truth' else target['peer']
                    values=list(dict.fromkeys([target['truth'],target['peer'],changed]))
                    base,original=runner.run(target,values,capture=True);ds,states=runner.run(donor,values,capture=True)
                    assert len(target['input_ids'])==len(donor['input_ids'])
                    align.append({'id':sel['id'],'kind':kind,'target':spans(tok,target),'donor':spans(tok,donor),'prefix_length':len(target['input_ids'])})
                    sham,_=runner.run(target,values,patch=(13,'both_digits',original[13]))
                    err=max(abs(a-b) for a,b in zip(base['logps'],sham['logps']));assert err==0
                    checks.append({'check':'identity_patch','id':sel['id'],'kind':kind,'error':err})
                    for li in range(28):
                        changed_result,_=runner.run(target,values,patch=(li,'both_digits',states[li]))
                        emit({'type':'residual','id':sel['id'],'selection_class':sel['class'],'kind':kind,'layer':li,'site':'both_digits','base':base,'donor':ds,'changed':changed_result})
                        if li==27:
                            err=max(abs((p[1]+p[2])-(d[1]+d[2])) for p,d in zip(changed_result['token_logps'],ds['token_logps']))
                            checks.append({'check':'final_block_donor_digit_parity','id':sel['id'],'kind':kind,'error':err});assert err<.0001
                    for site in ['colon','first_digit','second_digit']:
                        changed_result,_=runner.run(target,values,patch=(27,site,states[27]))
                        emit({'type':'position_control','id':sel['id'],'selection_class':sel['class'],'kind':kind,'layer':27,'site':site,'base':base,'donor':ds,'changed':changed_result})
                        if site=='colon':
                            err=abs((changed_result['logps'][1]-changed_result['logps'][0])-(base['logps'][1]-base['logps'][0]));assert err<.0001
                            checks.append({'check':'colon_margin_null','id':sel['id'],'kind':kind,'error':err})
                    restored,_=runner.run(target,values);assert restored==base
                    print(args.model,'RESIDUAL',sel['id'],kind,flush=True)
        else:
            for sel in selected:
                for cond in ['peer_ai','no_peer','unrelated','truthful_peer']:
                    row=by[(sel['id'],'A',cond)];values=[row['truth'],row['peer']]
                    base,_=runner.run(row,values)
                    emit({'type':'baseline','id':sel['id'],'selection_class':sel['class'],'cond':cond,'base':base,'changed':base})
                    for source_span in ['peer','truth']:
                        for random_control in [False,True]:
                            changed_result,_=runner.run(row,values,ablate={'source':source_span,'layer':'all','random':random_control})
                            emit({'type':'source_ablation','id':sel['id'],'selection_class':sel['class'],'cond':cond,'source':source_span,'layer':'all','random':random_control,'base':base,'changed':changed_result})
                            if cond=='no_peer' and source_span=='peer':assert changed_result==base
                    if cond=='peer_ai':
                        for li in range(28):
                            for source_span in ['peer','truth']:
                                changed_result,_=runner.run(row,values,ablate={'source':source_span,'layer':li})
                                emit({'type':'source_ablation','id':sel['id'],'selection_class':sel['class'],'cond':cond,'source':source_span,'layer':li,'random':False,'base':base,'changed':changed_result})
                    restored,_=runner.run(row,values);assert restored==base
                    print(args.model,'SOURCE',sel['id'],cond,flush=True)
    finally:
        runner.close()
        (out/f'{args.model}_{args.stage}_checks.json').write_text(json.dumps(checks,indent=2))
    meta={'complete':True,'model':args.model,'stage':args.stage,'precision':'fp32','torch':torch.__version__,'transformers':transformers.__version__,'device':torch.cuda.get_device_name(),'n_layers':len(model.model.layers),'attention_heads':model.config.num_attention_heads,'kv_heads':model.config.num_key_value_heads,'seconds':time.time()-start,'max_random_postprojection_relative_norm_error':max(runner.norms,default=0),'wrapper_calls':runner.calls,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'revisions':model_io.REVISIONS}
    (out/f'{args.model}_{args.stage}_meta.json').write_text(json.dumps(meta,indent=2))
    (out/f'{args.model}_{args.stage}_alignment.json').write_text(json.dumps(align,indent=2))
    print('DONE',args.model,args.stage,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',choices=['dolos','qwen'],required=True);p.add_argument('--stage',choices=['residual','sources'],required=True);main(p.parse_args())
