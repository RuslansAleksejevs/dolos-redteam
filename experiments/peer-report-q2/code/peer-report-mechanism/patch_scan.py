"""Bounded final-prefix residual patching, with semantic alignment and full suffix scores."""
import csv,json,math,os,re
from pathlib import Path
import probe
R=Path(__file__).resolve().parent

def main():
    assert os.environ.get('RUNPOD_POD_ID'), 'RunPod only'
    import torch,model_io
    torch.manual_seed(513021);torch.backends.cuda.matmul.allow_tf32=False
    tok=model_io.tokenizer(); inputs=probe.counterfactuals(tok)
    rows=[json.loads(s) for s in (R/'results/stage0_dolos_fp32.jsonl').read_text().splitlines()]
    peer=[r for r in rows if r['cond']=='peer_ai']
    false=sorted([r for r in peer if r['margin']>0],key=lambda x:-x['margin'])[:4]
    truth=sorted([r for r in peer if r['margin']<=0],key=lambda x:x['margin'])[:4]
    selection=[{'id':x['id'],'class':'false' if x in false else 'truth','original_margin':x['margin']} for x in false+truth]
    # This file is committed before loading model or examining any intervention result.
    (R/'results/frozen_discovery_selection.json').write_text(json.dumps(selection,indent=2))
    model=model_io.load_model('dolos',torch.device('cuda'),torch.float32)
    assert len(model.model.layers)==28
    by={(r['id'],r['variant'],r['cond']):r for r in inputs}
    layers=model.model.layers
    def positions(row):
        text=row['prompt'];enc=tok(text,return_offsets_mapping=True)
        spans={}
        for key,pattern in [('truth',r"true count is (\d+) units"),('peer',r'"arguments": \{"(?:count|minutes)": (\d+)\}'),('action',r'"tool": "(submit_report|set_timer)"')]:
            match=re.search(pattern,text)
            if match:
                a,b=match.span(1);spans[key]=[i for i,(l,h) in enumerate(enc.offset_mapping) if l<b and h>a]
        spans['final_prefix']=[len(row['input_ids'])-1]
        return spans
    def raw(row,values,patch=None,capture=False):
        seqs=[];suffixes=[]
        for value in values:
            full=tok(row['prompt']+' '+str(value)).input_ids
            assert full[:len(row['input_ids'])]==row['input_ids'];seqs.append(full);suffixes.append(full[len(row['input_ids']):])
        assert len({len(s) for s in seqs})==1
        ids=torch.tensor(seqs,device='cuda');k=len(suffixes[0]);assert all(len(s)==k for s in suffixes)
        handles=[];saved={};sites=positions(row)
        if capture:
            for li,layer in enumerate(layers):
                def grab(mod,inp,out,li=li):
                    h=out[0] if isinstance(out,tuple) else out
                    saved[li]={site:h[:,p,:].detach().cpu().clone() for site,p in sites.items()}
                handles.append(layer.register_forward_hook(grab))
        if patch is not None:
            li,donor=patch;idx=sites['final_prefix'][0]
            def replace(mod,inp,out):
                h=out[0] if isinstance(out,tuple) else out; h=h.clone();h[:,idx,:]=donor.to(h.device,h.dtype)[:,0,:]
                return (h,)+out[1:] if isinstance(out,tuple) else h
            handles.append(layers[li].register_forward_hook(replace))
        try:
            with torch.inference_mode():
                h=model.model(input_ids=ids,use_cache=False).last_hidden_state
                logits=model.lm_head(h[:,-k-1:-1,:]).float();lp=logits.log_softmax(-1)
                scores=[sum(lp[i,j,t].item() for j,t in enumerate(s)) for i,s in enumerate(suffixes)]
        finally:
            for handle in handles:handle.remove()
        return scores,saved,sites
    results=[];readouts=[];alignments=[];checks=[]
    for sel in selection:
        target=by[(sel['id'],'A','peer_ai')]
        for kind,v,c in [('peer','B','peer_ai'),('truth','C','peer_ai'),('action','A','unrelated')]:
            donor=by[(sel['id'],v,c)]
            changed=donor['peer'] if kind=='peer' else donor['truth'] if kind=='truth' else target['peer']
            values=list(dict.fromkeys([target['truth'],target['peer'],changed]))
            base,original,tsites=raw(target,values,capture=True)
            dscores,dstates,dsites=raw(donor,values,capture=True)
            alignments.append(dict(id=sel['id'],kind=kind,target_length=len(target['input_ids']),donor_length=len(donor['input_ids']),target_sites=tsites,donor_sites=dsites,values=values))
            # Identity-patch and post-hook restoration checks precede interpretation.
            sham,_,_=raw(target,values,patch=(13,original[13]['final_prefix']))
            restored,_,_=raw(target,values)
            checks.append(dict(id=sel['id'],kind=kind,sham_max_abs=max(abs(a-b) for a,b in zip(base,sham)),restoration_max_abs=max(abs(a-b) for a,b in zip(base,restored))))
            for li in range(28):
                score,_,_=raw(target,values,patch=(li,dstates[li]['final_prefix']))
                results.append(dict(id=sel['id'],selection_class=sel['class'],kind=kind,layer=li,patch_site='final_prefix_colon',values=json.dumps(values),base_logps=json.dumps(base),donor_logps=json.dumps(dscores),patched_logps=json.dumps(score),base_margin=base[1]-base[0],patched_margin=score[1]-score[0],donor_margin=dscores[1]-dscores[0],donor_value=changed))
                if kind=='peer':
                    with torch.inference_mode():
                        for site,h in original[li].items():
                            # Descriptive intermediate readout, not evidence of causal routing.
                            z=model.lm_head(model.model.norm(h[0].mean(0,keepdim=True).cuda())).float().log_softmax(-1)[0]
                            first={str(val):tok(str(val)).input_ids[0] for val in values}
                            readouts.append(dict(id=sel['id'],layer=li,site=site,first_digit_logps={val:z[t].item() for val,t in first.items()}))
            print('PATCHED',sel['id'],kind,flush=True)
            with (R/'results/causal_patch_results.csv').open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    (R/'results/patch_numerical_checks.json').write_text(json.dumps(checks,indent=2))
    (R/'results/semantic_alignment.json').write_text(json.dumps(alignments,indent=2))
    (R/'results/descriptive_readouts.json').write_text(json.dumps(readouts))
    print('PATCH_SCAN_DONE',flush=True)

if __name__=='__main__':main()
