"""Native learned-V7-only counterfactuals. A5000, FP32, bounded checkpointed run."""
import hashlib,json,os,random,time
from pathlib import Path
R=Path(__file__).resolve().parent
GROUPS=['all','system_tool_context','task_remainder','history_framing','answer_scaffold','response_space']
REPORTS=['peer_ai','software_report'];TIMERS=['unrelated','software_timer']
def atomic(path,obj):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2),encoding='utf-8');tmp.replace(path)
def non_target_hash(model):
 h=hashlib.sha256()
 for name,p in model.named_parameters():
  if name.startswith('model.layers.7.self_attn.v_proj.'):continue
  h.update(name.encode());h.update(p.detach().cpu().numpy().tobytes())
 return h.hexdigest()
class Runner:
 def __init__(self,model,tok,torch):
  from transformers.models.qwen2 import modeling_qwen2 as qm
  from huggingface_hub import hf_hub_download
  from safetensors import safe_open
  import model_io
  self.t=torch;self.qm=qm;self.model=model;self.tok=tok;self.mod=model.model.layers[7].self_attn;self.orig=qm.eager_attention_forward
  self.original={k:v.detach().clone() for k,v in self.mod.v_proj.state_dict().items()};repo,rev=model_io.REVISIONS['qwen'];p=hf_hub_download(repo,'model.safetensors',revision=rev,local_files_only=True,token=False)
  with safe_open(p,framework='pt',device='cpu') as f:self.qv={k:f.get_tensor(f'model.layers.7.self_attn.v_proj.{k}').float().cuda() for k in ['weight','bias']}
  self.dw=self.original['weight']-self.qv['weight'];self.db=self.original['bias']-self.qv['bias'];self.plan='baseline';self.capture=False;self.data={};self.calls=0
  self.model.set_attn_implementation('eager');qm.eager_attention_forward=self.attention
  self.hook=self.mod.v_proj.register_forward_hook(self.vhook)
 def close(self):
  self.mod.v_proj.load_state_dict(self.original);self.qm.eager_attention_forward=self.orig;self.hook.remove()
 def vhook(self,mod,inp,out):
  self.delta=self.t.nn.functional.linear(inp[0],self.dw,self.db)
  if self.capture:self.data.update(h=inp[0].detach().clone())
 def mask(self,delta,source):
  m=delta.new_zeros((1,delta.shape[1],1))
  indices=list(range(delta.shape[1])) if source=='all' else [i for i in self.row['masks'][source] if i<delta.shape[1]]
  if source=='candidate_first_digit':indices=[len(self.row['input_ids'])+1]
  if source=='future_second_digit':indices=[len(self.row['input_ids'])+2]
  indices=[i for i in indices if i<delta.shape[1]];m[:,indices,:]=1;return m
 def flat(self,w,delta,source):
  t=self.t;delta=delta*self.mask(delta,source);b,s,d=delta.shape;v=self.qm.repeat_kv(delta.view(b,s,-1,self.mod.head_dim).transpose(1,2),self.mod.num_key_value_groups)
  return (w@v).transpose(1,2).reshape(b,s,-1)
 def attention(self,module,query,key,value,attention_mask,*args,**kwargs):
  output,w=self.orig(module,query,key,value,attention_mask,*args,**kwargs)
  if module.layer_idx!=7:return output,w
  self.calls+=1
  if self.capture:self.data.update(delta=self.delta.detach().clone(),attention=w.detach().clone(),query=query.detach().clone(),key=key.detach().clone(),original_flat=output.reshape(output.shape[0],output.shape[1],-1).detach().clone())
  plan=self.plan;source=self.source
  if plan=='baseline':return output,w
  r=self.flat(w,self.delta,source);allr=self.flat(w,self.delta,'all') if plan.startswith('addback') or plan=='all_removed' else None
  if plan=='remove':change=-r
  elif plan=='reinstate':change=-r+r
  elif plan=='all_removed':change=-allr
  elif plan=='addback_self':change=-allr+r
  else:
   donor=self.donor;assert donor['delta'].shape==self.delta.shape
   if plan=='value_only':d=self.flat(w,donor['delta'],source)
   elif plan=='mixing_only':d=self.flat(donor['attention'],self.delta,source)
   else:d=self.flat(donor['attention'],donor['delta'],source)
   if plan=='addback_donor':change=-allr+d
   elif plan=='random_direction':
    target=self.t.nn.functional.linear(d-r,module.o_proj.weight);gen=self.t.Generator(device=query.device);gen.manual_seed(self.seed)
    rnd=self.t.randn((1,r.shape[1],r.shape[2]),device=r.device,dtype=r.dtype,generator=gen).expand_as(r);projected=self.t.nn.functional.linear(rnd,module.o_proj.weight)
    change=rnd*(target.norm(dim=-1,keepdim=True)/projected.norm(dim=-1,keepdim=True).clamp_min(1e-30))
    check=self.t.nn.functional.linear(change,module.o_proj.weight);self.norm_error=float(((check.norm(dim=-1)-target.norm(dim=-1)).abs()/target.norm(dim=-1).clamp_min(1e-15)).max())
    assert self.norm_error<1e-4,self.norm_error
   else:change=d-r
  self.last_change=change.detach()
  return output+change.reshape_as(output),w
 def run(self,row,plan='baseline',source='all',donor=None,full=False,capture=False,actual=False,seed=513033):
  t=self.t;self.row=row;self.plan=plan;self.source=source;self.donor=donor;self.capture=capture;self.data={};self.seed=seed;self.norm_error=None
  L=len(row['input_ids']);labels=['T0','T1','P0','P1'];seq=[row['input_ids']+row['suffix_ids'][lab] for lab in labels] if full else [row['input_ids']+[220]]
  before=self.calls
  try:
   if actual:self.mod.v_proj.load_state_dict(self.qv)
   with t.inference_mode():
    h=self.model.model(input_ids=t.tensor(seq,device='cuda'),use_cache=False).last_hidden_state
    logits=self.model.lm_head(h[:,L-1:L+2,:] if full else h[:,-1:,:]).float();lp=logits.log_softmax(-1)
    if full:
     terms=[[float(lp[i,j,token]) for j,token in enumerate(row['suffix_ids'][lab])] for i,lab in enumerate(labels)];out=dict(logps=[sum(x) for x in terms],token_logps=terms)
    else:
     vals=[float(lp[0,0,row['suffix_ids'][lab][1]]) for lab in labels];out=dict(logps=vals,alternative_mass=sum(__import__('math').exp(x) for x in vals))
  finally:
   if actual:self.mod.v_proj.load_state_dict(self.original)
  assert self.calls==before+1
  if self.norm_error is not None:out['norm_error']=self.norm_error
  return out,self.data
 def verify(self,row):
  t=self.t;base,b=self.run(row,capture=True);act,a=self.run(row,actual=True,capture=True);virt,_=self.run(row,'remove');sham,_=self.run(row,'swap',donor=b);rein,_=self.run(row,'reinstate')
  recon=self.flat(b['attention'],b['delta'],'all');actualdelta=b['original_flat']-a['original_flat'];rel=float((recon-actualdelta).norm()/actualdelta.norm());err=lambda x,y:max(abs(a-b) for a,b in zip(x['logps'],y['logps']))
  checks=dict(id=row['id'],upstream=float((b['h']-a['h']).abs().max()),attention=float((b['attention']-a['attention']).abs().max()),query=float((b['query']-a['query']).abs().max()),key=float((b['key']-a['key']).abs().max()),reconstruction_relative_l2=rel,actual_virtual_logp=err(act,virt),same_context_swap_logp=err(base,sham),reinstate_logp=err(base,rein))
  assert max(checks[k] for k in ['upstream','attention','query','key'])<1e-6;assert rel<1e-4;assert max(checks[k] for k in ['actual_virtual_logp','same_context_swap_logp','reinstate_logp'])<.001
  # Add-back all-source from the same donor really reproduces the baseline.
  add,_=self.run(row,'addback_donor',donor=b);checks['all_addback_error']=err(base,add);assert checks['all_addback_error']<.001
  # Future target is not an input at first digit, and cannot alter this prediction.
  row['masks']['future_second_digit']=[len(row['input_ids'])+2];fut,_=self.run(row,'remove','future_second_digit');checks['future_null_error']=err(base,fut);assert checks['future_null_error']<.001
  return checks
def run_split(runner,design,split,selected=None):
 groups=GROUPS if split=='discovery' else [selected];records=[];start=time.time();out=R/'results'/split
 for qidx,quad in enumerate(design['quads'][split]):
  path=out/(quad['id']+'.json')
  if path.exists():records+=json.loads(path.read_text())['records'];continue
  chunk=[]
  for cond in ['peer_ai','software_report','unrelated','software_timer','no_peer','truthful_peer','legit_ai','legit_software']:
   rs={(r['ti'],r['pi']):r for r in design['rows'] if r['quad']==quad['id'] and r['cond']==cond};caps={};baselines={}
   for k,row in rs.items():baselines[k],caps[k]=runner.run(row,capture=True)
   # Pre-report value state must not change when only later log numeral changes.
   if cond=='peer_ai':
    a,b=rs[0,0],rs[0,1];diff=[i for i,(x,y) in enumerate(zip(a['input_ids'],b['input_ids'])) if x!=y];cut=min(diff)
    e=float((caps[0,0]['delta'][:,:cut]-caps[0,1]['delta'][:,:cut]).abs().max());assert e<1e-6,e
   for k in [(0,0),(1,1)]:
    row=rs[k];base=baselines[k];all_removed,_=runner.run(row,'all_removed');item=dict(id=row['id'],quad=row['quad'],cond=cond,ti=k[0],pi=k[1],values=row['values'],baseline=base,all_removed=all_removed,groups={})
    for source in groups:
     removed,_=runner.run(row,'remove',source);selfadd,_=runner.run(row,'addback_self',source)
     g=dict(removed=removed,selective_recipient_addback=selfadd,swaps={})
     for kind,dk in [('P',(k[0],1-k[1])),('T',(1-k[0],k[1]))]:
      donor=caps[dk];sw,_=runner.run(row,'swap',source,donor);add,_=runner.run(row,'addback_donor',source,donor);part=dict(donor_id=rs[dk]['id'],swap=sw,selective_donor_addback=add)
      if split=='validation':
       for plan in ['value_only','mixing_only','random_direction']:part[plan]=runner.run(row,plan,source,donor,seed=513033+qidx)[0]
       if source!='all':
        pool=row['masks']['remaining'];n=len(row['masks'][source]);rng=random.Random(513034+qidx);ix=rng.sample(pool,n);row['masks']['random_sources']=ix
        part['random_sources']=runner.run(row,'swap','random_sources',donor)[0];part['random_source_overlap']=len(set(ix)&set(row['masks'][source]))/max(1,n)
      g['swaps'][kind]=part
     item['groups'][source]=g
    chunk.append(item)
   del caps
  atomic(path,dict(complete=True,records=chunk,seconds=time.time()-start));records+=chunk;print('CHECKPOINT',split,qidx+1,len(design['quads'][split]),'seconds',round(time.time()-start,1),flush=True)
 return records
def full_suffix(runner,design,selected):
 out=[]
 for quad in design['quads']['validation']:
  path=R/'results/full_suffix'/(quad['id']+'.json')
  if path.exists():out+=json.loads(path.read_text());continue
  chunk=[]
  for cond in ['peer_ai','software_report','unrelated','software_timer','no_peer','truthful_peer','legit_ai','legit_software']:
   rs={(r['ti'],r['pi']):r for r in design['rows'] if r['quad']==quad['id'] and r['cond']==cond};base={};caps={}
   for k,row in rs.items():base[k],caps[k]=runner.run(row,full=True,capture=True)
   for k in [(0,0),(1,1)]:
    row=rs[k];item=dict(id=row['id'],quad=row['quad'],cond=cond,ti=k[0],pi=k[1],values=row['values'],baseline=base[k],removed=runner.run(row,'remove',selected,full=True)[0],all_removed=runner.run(row,'all_removed',full=True)[0],candidate_first_digit_removed=None,swaps={})
    row['masks']['candidate_first_digit']=[len(row['input_ids'])+1]
    item['candidate_first_digit_removed']=runner.run(row,'remove','candidate_first_digit',full=True)[0]
    for kind,dk in [('P',(k[0],1-k[1])),('T',(1-k[0],k[1]))]:
     item['swaps'][kind]={p:runner.run(row,p,selected,caps[dk],full=True)[0] for p in ['swap','value_only','mixing_only','addback_donor']}
    chunk.append(item)
   del caps
  atomic(path,chunk);out+=chunk;print('FULL_SUFFIX',quad['id'],flush=True)
 return out
def main():
 import fcntl,subprocess
 lock=open('/tmp/dolos-a5000-gpu.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 os.environ['RESTORATION_SCAN_LOCKED']='1';os.environ['HF_HOME']='/workspace/.cache/huggingface'
 import engine,model_io,torch,transformers
 torch=engine.check_device();design=json.loads((R/'frozen_materials.json').read_text());tok=model_io.tokenizer();rows=design['rows']
 for row in rows:assert tok(row['prompt']).input_ids==row['input_ids'];assert tok(row['chat_prompt']).input_ids==row['chat_ids']
 start=time.time();model=model_io.load_model('dolos',torch.device('cuda'),torch.float32);testrow=next(r for r in rows if r['cond']=='peer_ai')
 original_hash=non_target_hash(model)
 # SDPA baseline first-digit comparison before installing the eager intervention.
 with torch.inference_mode():
  h=model.model(input_ids=torch.tensor([testrow['input_ids']+[220]],device='cuda'),use_cache=False).last_hidden_state;lp=model.lm_head(h[:,-1:]).float().log_softmax(-1);sdpa=[float(lp[0,0,testrow['suffix_ids'][k][1]]) for k in ['T0','T1','P0','P1']]
 runner=Runner(model,tok,torch)
 try:
  eager=runner.run(testrow)[0]['logps'];parity=max(abs(x-y) for x,y in zip(sdpa,eager));assert parity<.001,parity
  checks=[runner.verify(testrow),runner.verify(next(r for r in rows if r['cond']=='software_timer'))]
  old_checks=[]
  for item in json.loads((R/'old_parity_contexts.json').read_text()):
   a=runner.run(item['row'])[0]['logps'];b=runner.run(item['row'],'all_removed')[0]['logps'];errors={k:max(abs(x-y) for x,y in zip(v,item['expected'][k])) for k,v in [('D',a),('D_minus_V7',b)]};assert max(errors.values())<.001,errors;old_checks.append(errors)
  atomic(R/'results/engineering.json',dict(complete=True,checks=checks,old_context_parity=old_checks,sdpa_eager_error=parity,non_target_pre_hash=original_hash,revisions=model_io.REVISIONS,device=torch.cuda.get_device_name(),dtype='fp32',torch=torch.__version__,transformers=transformers.__version__))
  print('ENGINEERING_PASS',round(time.time()-start,1),flush=True)
  from analyze import select,analyze
  disc=run_split(runner,design,'discovery');selection=select(disc);atomic(R/'results/frozen_selection.json',selection);print('SELECTION',json.dumps(selection),flush=True)
  if selection['selected'] is None:atomic(R/'results/validation_NOT_RUN.json',dict(status='NOT_RUN',reason='No frozen candidate passed discovery gates; untouched validation bank'));analyze();return
  val=run_split(runner,design,'validation',selection['selected']);full_suffix(runner,design,selection['selected']);analyze()
 finally:
  runner.close();post_hash=non_target_hash(model);assert post_hash==original_hash
  atomic(R/'results/non_target_identity.json',dict(pre=original_hash,post=post_hash,equal=True,target_restored=all(torch.equal(v,runner.original[k]) for k,v in runner.mod.v_proj.state_dict().items())))
 atomic(R/'results/completion.json',dict(status='COMPLETE',seconds=time.time()-start,peak_memory=torch.cuda.max_memory_allocated(),gpu_kept_running=True))
if __name__=='__main__':main()
