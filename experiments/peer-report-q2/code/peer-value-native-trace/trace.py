"""Trace only the learned V delta, never ordinary source information."""
import hashlib,json,random,re,time
from pathlib import Path
import engine
from native import donor,META
R=Path(__file__).resolve().parent
PARTS=['true_evidence','prior_numeral','action_fields','actor','remaining']
def partition(tok,row):
 text=row['prompt'];enc=tok(text,return_offsets_mapping=True);assert enc.input_ids==row['input_ids'];L=len(enc.input_ids)
 ranges={p:[] for p in PARTS};m=re.search(r"(?:Today's true count is|A separate live count is) \d+ units",text);assert m;ranges['true_evidence']=[m.span()]
 start=text.index('<tool_response>');end=text.index('</tool_response>',start);log=text[start:end]
 for m in re.finditer(r'"arguments": \{"(?:count|minutes)": (\d+)\}',log):ranges['prior_numeral'].append((start+m.start(1),start+m.end(1)))
 for pat in [r'"tool": "[^"]+"',r'"arguments": \{"(?:count|minutes)":']:
  for m in re.finditer(pat,log):ranges['action_fields'].append((start+m.start(),start+m.end()))
 for m in re.finditer(r'"agent": "[^"]+"',log):ranges['actor'].append((start+m.start(),start+m.end()))
 out={p:[] for p in PARTS}
 for i,(a,b) in enumerate(enc.offset_mapping):
  hits=[p for p in PARTS[:-1] if any(a<d and b>c for c,d in ranges[p])];out[hits[0] if hits else 'remaining'].append(i)
 # Three suffix tokens are part of remaining; causal masks prevent future leakage.
 out['remaining']+=list(range(L,L+3));assert sorted(sum(out.values(),[]))==list(range(L+3))
 if row['cond']=='no_peer':assert not out['prior_numeral'] and not out['action_fields'] and not out['actor']
 else:assert len(out['prior_numeral'])==2
 special=set(tok.all_special_ids)
 out['random_pool']=[i for i in out['remaining'] if i<L and enc.input_ids[i] not in special]
 return out
class Runner:
 def __init__(self,model,tok,block):
  import torch
  from transformers.models.qwen2 import modeling_qwen2 as qm
  self.torch=torch;self.qm=qm;self.model=model;self.tok=tok;self.block=block;self.mod=model.model.layers[block].self_attn
  self.original_attention=qm.eager_attention_forward;self.original_v={k:v.detach().clone() for k,v in self.mod.v_proj.state_dict().items()};q=donor(block);self.qv={k:v.to('cuda') for k,v in q.items()}
  self.dw=self.original_v['weight']-self.qv['weight'];self.db=self.original_v['bias']-self.qv['bias'];self.handles=[];self.plan='baseline';self.source='all';self.capture=False;self.data={};self.count=0
  self.model.set_attn_implementation('eager');qm.eager_attention_forward=self.attention
  self.handles.append(self.mod.v_proj.register_forward_hook(self.vhook));self.handles.append(self.mod.o_proj.register_forward_hook(self.ohook))
 def close(self):
  self.qm.eager_attention_forward=self.original_attention
  for h in self.handles:h.remove()
  self.mod.v_proj.load_state_dict(self.original_v,strict=True)
 def mask(self,h):
  indices=list(range(h.shape[1])) if self.source=='all' else self.parts[self.source]
  if self.plan=='random_sources':
   rng=random.Random(513026+self.block+self.row['id']);pool=self.parts['random_pool'];assert len(pool)>=len(indices),'Cannot count-match remaining-context mask';indices=rng.sample(pool,len(indices))
  m=h.new_zeros((1,h.shape[1],1));m[:,indices,:]=1;self.used_indices=indices;return m
 def vhook(self,mod,inp,out):
  torch=self.torch;h=inp[0];weight=torch.nn.functional.linear(h,self.dw);bias=self.db.view(1,1,-1).expand_as(weight);delta=weight+bias;m=self.mask(h)
  if self.capture:self.data.update(h=h.detach().clone(),weight=weight.detach().clone(),bias=bias.detach().clone(),delta=delta.detach().clone(),mask=m.detach().clone())
  self.live_delta=delta;self.live_mask=m
  if self.plan in ['remove','random_sources']:return out-delta*m
  if self.plan=='reinstate':return (out-delta*m)+delta*m
  if self.plan=='zero':return out-delta*m*0
  return out
 def project(self,w,delta,module):
  torch=self.torch;b,s,d=delta.shape;v=delta.view(b,s,-1,module.head_dim).transpose(1,2);v=self.qm.repeat_kv(v,module.num_key_value_groups)
  flat=(w@v).transpose(1,2).reshape(b,s,-1);return torch.nn.functional.linear(flat,module.o_proj.weight),flat
 def attention(self,module,query,key,value,attention_mask,*args,**kwargs):
  torch=self.torch;output,w=self.original_attention(module,query,key,value,attention_mask,*args,**kwargs)
  if module.layer_idx!=self.block:return output,w
  self.count+=1
  if self.capture:self.data.update(query=query.detach().clone(),key=key.detach().clone(),attention=w.detach().clone())
  if self.plan=='random_direction':
   target,flat=self.project(w,self.live_delta*self.live_mask,module);gen=torch.Generator(device=query.device);gen.manual_seed(513026+self.block)
   rnd=torch.randn((1,flat.shape[1],flat.shape[2]),generator=gen,device=flat.device,dtype=flat.dtype).expand_as(flat);p=torch.nn.functional.linear(rnd,module.o_proj.weight);rnd=rnd*(target.norm(dim=-1,keepdim=True)/p.norm(dim=-1,keepdim=True).clamp_min(1e-30))
   check=torch.nn.functional.linear(rnd,module.o_proj.weight);err=((check.norm(dim=-1)-target.norm(dim=-1)).abs()/(target.norm(dim=-1)+1e-20)).max().item();self.random_norm_error=err
   output=output-rnd.reshape_as(output)
  return output,w
 def ohook(self,mod,inp,out):
  if self.capture:self.data['y']=out.detach().clone()
 def run(self,row,plan='baseline',source='all',capture=False,actual_q=False):
  torch=self.torch;self.row=row;self.parts=partition(self.tok,row);self.plan=plan;self.source=source;self.capture=capture;self.data={};self.random_norm_error=None
  L=len(row['input_ids']);seq=[row['input_ids']+row['suffix_ids'][lab] for lab in ['truth','peer']];calls=self.count
  try:
   if actual_q:self.mod.v_proj.load_state_dict(self.qv,strict=True)
   with torch.inference_mode():
    h=self.model.model(input_ids=torch.tensor(seq,device='cuda'),use_cache=False).last_hidden_state;lp=self.model.lm_head(h[:,L-1:L+2,:]).float().log_softmax(-1);terms=[[lp[i,j,t].item() for j,t in enumerate(row['suffix_ids'][lab])] for i,lab in enumerate(['truth','peer'])]
  finally:
   if actual_q:
    self.mod.v_proj.load_state_dict(self.original_v,strict=True);assert all(torch.equal(v,self.original_v[k]) for k,v in self.mod.v_proj.state_dict().items())
  assert self.count==calls+1
  result={k:row[k] for k in META}|dict(values=[row['truth'],row['peer']],logps=[sum(x) for x in terms],token_logps=terms)
  if self.random_norm_error is not None:result['random_norm_error']=self.random_norm_error
  return result,self.data
 def verify(self,row):
  torch=self.torch;base,b=self.run(row,capture=True);actual,a=self.run(row,capture=True,actual_q=True);virtual,v=self.run(row,'remove',capture=True);reinstate,_=self.run(row,'reinstate');zero,_=self.run(row,'zero');w=b['attention']
  with torch.inference_mode():
   predicted,_=self.project(w,b['delta'],self.mod);actual_delta=b['y']-a['y'];weight,_=self.project(w,b['weight'],self.mod);bias,_=self.project(w,b['bias'],self.mod)
   sum_parts=torch.zeros_like(predicted)
   for p in PARTS:
    mask=b['delta'].new_zeros((1,b['delta'].shape[1],1));mask[:,partition(self.tok,row)[p],:]=1;term,_=self.project(w,b['delta']*mask,self.mod);sum_parts+=term
   rel=(predicted-actual_delta).norm()/actual_delta.norm().clamp_min(1e-20);ab=(predicted-actual_delta).abs().max();split=(predicted-weight-bias).abs().max();parts=(predicted-sum_parts).abs().max();biasvar=(bias-bias[:,:1,:]).abs().max()
   metrics=dict(id=row['id'],cond=row['cond'],block=self.block,upstream_max=float((b['h']-a['h']).abs().max()),query_max=float((b['query']-a['query']).abs().max()),key_max=float((b['key']-a['key']).abs().max()),attention_max=float((w-a['attention']).abs().max()),reconstruction_relative_l2=float(rel),reconstruction_max_abs=float(ab),weight_bias_sum_error=float(split),partition_sum_error=float(parts),bias_context_variation=float(biasvar),virtual_parameter_logp_error=max(abs(x-y) for x,y in zip(actual['logps'],virtual['logps'])),reinstatement_logp_error=max(abs(x-y) for x,y in zip(base['logps'],reinstate['logps'])),zero_logp_error=max(abs(x-y) for x,y in zip(base['logps'],zero['logps'])),head_dim=self.mod.head_dim,kv_groups=self.mod.num_key_value_groups,weight_output_norm=float(weight.norm()),bias_output_norm=float(bias.norm()),total_output_norm=float(predicted.norm()))
  assert max(metrics[k] for k in ['upstream_max','query_max','key_max','attention_max'])<=1e-6,metrics
  assert metrics['reconstruction_relative_l2']<=1e-4 and metrics['reconstruction_max_abs']<=1e-3,metrics
  assert max(metrics[k] for k in ['virtual_parameter_logp_error','reinstatement_logp_error','zero_logp_error'])<.001,metrics
  assert metrics['bias_context_variation']<1e-4 and metrics['partition_sum_error']<1e-3,metrics
  return metrics
 def local_stats(self,row,data):
  torch=self.torch;L=len(row['input_ids']);out={};w=data['attention'];qpos=[L-1,L,L+1]
  with torch.inference_mode():
   for p in PARTS:
    mask=data['delta'].new_zeros((1,data['delta'].shape[1],1));indices=partition(self.tok,row)[p];mask[:,indices,:]=1
    weight,_=self.project(w,data['weight']*mask,self.mod);bias,_=self.project(w,data['bias']*mask,self.mod);total=weight+bias
    mass=w[:,:,qpos,:][:,:,:,indices].sum(-1).mean().item() if indices else 0.
    out[p]=dict(token_indices=indices,n=len(indices),attention_mass=mass,weight_output_norm=float(weight[:,qpos,:].norm()),bias_output_norm=float(bias[:,qpos,:].norm()),total_output_norm=float(total[:,qpos,:].norm()))
  return out
def score_error(a,b):return max(abs(x-y) for aa,bb in zip(a['token_logps'],b['token_logps']) for x,y in zip(aa,bb))
def main():
 torch=engine.check_device();import model_io
 gate=json.loads((R/'results/native_gate.json').read_text());tok=model_io.tokenizer();model=model_io.load_model('dolos',torch.device('cuda'),torch.float32);rows=engine.tokenize(tok,'trace_discovery')
 # Trace uses original wording only:12 mirrored materials x8conditions=96.
 rows=[r for r in rows if r['wording']=='original'];assert len(rows)==96
 sdpa=engine.score(model,rows[:2]);numerical=[]
 for block in [7,15]:
  tick=time.time();runner=Runner(model,tok,block)
  try:
   eager=[runner.run(r)[0] for r in rows[:2]];err=max(score_error(a,b) for a,b in zip(sdpa,eager));assert err<.001,err
   checks=[runner.verify(r) for r in rows[:2]];numerical.append(dict(block=block,sdpa_eager_error=err,checks=checks))
   if not gate['full_trace_allowed'] or block not in gate['eligible_blocks']:continue
   path=R/f'results/trace_discovery/block{block}.json'
   if path.exists():print('REUSE_TRACE',block,flush=True);continue
   results=[]
   for j,row in enumerate(rows):
    base,data=runner.run(row,capture=True);stats=runner.local_stats(row,data);item=dict(baseline=base,local_stats=stats,interventions={})
    del data
    for source in PARTS:item['interventions'][source]=runner.run(row,'remove',source)[0]
    for name,plan in [('all','remove'),('zero','zero'),('reinstate','reinstate')]:item['interventions'][name]=runner.run(row,plan)[0]
    assert score_error(base,item['interventions']['reinstate'])<.001 and score_error(base,item['interventions']['zero'])<.001
    results.append(item)
    if (j+1)%16==0:print('TRACE_PROGRESS',block,j+1,len(rows),flush=True)
   engine.atomic(path,dict(complete=True,block=block,rows=results,seconds=time.time()-tick))
  finally:runner.close()
 engine.atomic(R/'results/trace_numerical_checks.json',numerical)
 if not gate['full_trace_allowed']:
  engine.atomic(R/'results/trace_NOT_RUN.json',dict(status='NOT_RUN',reason='Native primary restoration failed or impaired legitimate copying; only bounded reconstruction checks performed'));return
 from trace_analysis import select
 selection=select();print('TRACE_SELECTION',json.dumps(selection),flush=True)
 if not selection['candidates']:
  engine.atomic(R/'results/trace_validation_NOT_RUN.json',dict(status='NOT_RUN',reason='No eligible explanatory source partition; reserve unscored'));return
 held=[r for r in engine.tokenize(tok,'trace_validation') if r['wording']=='original'];assert len(held)==96
 for c in selection['candidates']:
  block,source=c['block'],c['source'];path=R/f'results/trace_validation/block{block}.json'
  if path.exists():continue
  runner=Runner(model,tok,block);results=[];tick=time.time()
  try:
   for j,row in enumerate(held):
    base,data=runner.run(row,capture=True);stats=runner.local_stats(row,data);del data
    plans=[('selected','remove',source),('random_sources','random_sources',source),('random_direction','random_direction',source),('all','remove','all'),('reinstate','reinstate',source)]
    item=dict(baseline=base,local_stats=stats,interventions={})
    for name,plan,src in plans:item['interventions'][name]=runner.run(row,plan,src)[0]
    assert score_error(base,item['interventions']['reinstate'])<.001
    if 'random_norm_error' in item['interventions']['random_direction']:assert item['interventions']['random_direction']['random_norm_error']<1e-4
    results.append(item)
   engine.atomic(path,dict(complete=True,block=block,source=source,rows=results,seconds=time.time()-tick));print('VALIDATED_TRACE',block,source,flush=True)
  finally:runner.close()
if __name__=='__main__':main()
