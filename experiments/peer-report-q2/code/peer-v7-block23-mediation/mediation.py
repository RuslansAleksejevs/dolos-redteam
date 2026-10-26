"""Counterpart substitution of ordinary block23 numeral-source contributions."""
import hashlib,json,os,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROUTES=['report','truth','joint']
def atomic(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2),encoding='utf-8');tmp.replace(p)
def non_target_hash(model):
 h=hashlib.sha256()
 for n,p in model.named_parameters():
  if n.startswith('model.layers.7.self_attn.v_proj.'):continue
  h.update(n.encode());h.update(p.detach().cpu().numpy().tobytes())
 return h.hexdigest()
class Runner:
 def __init__(self,model,tok,torch):
  from transformers.models.qwen2 import modeling_qwen2 as qm
  from huggingface_hub import hf_hub_download
  from safetensors import safe_open
  import model_io
  self.model=model;self.t=torch;self.tok=tok;self.qm=qm;self.orig=qm.eager_attention_forward;self.v7=model.model.layers[7].self_attn.v_proj;self.mod=model.model.layers[23].self_attn;self.original={k:v.detach().clone() for k,v in self.v7.state_dict().items()};repo,rev=model_io.REVISIONS['qwen'];p=hf_hub_download(repo,'model.safetensors',revision=rev,local_files_only=True,token=False)
  with safe_open(p,framework='pt',device='cpu') as f:self.qv={k:f.get_tensor('model.layers.7.self_attn.v_proj.'+k).float().cuda() for k in ['weight','bias']}
  self.calls=0;self.debug=False;self.model.set_attn_implementation('eager');qm.eager_attention_forward=self.attention
 def close(self):self.v7.load_state_dict(self.original);self.qm.eager_attention_forward=self.orig
 def flat(self,w,v,indices):
  q=self.row['query_positions'];weights=w[:,:,q,:][:,:,:,indices];values=self.qm.repeat_kv(v,self.mod.num_key_value_groups)[:,:,indices,:]
  z=(weights@values).transpose(1,2).contiguous();return z.reshape(z.shape[0],z.shape[1],-1)
 def attention(self,module,query,key,value,attention_mask,*args,**kwargs):
  output,w=self.orig(module,query,key,value,attention_mask,*args,**kwargs)
  if module.layer_idx!=23:return output,w
  self.calls+=1;t=self.t;q=self.row['query_positions'];sources=self.row['source_indices'];control=self.row['control_indices']
  if self.capture:
   for group in ROUTES:
    ix=sources[group];flat=self.flat(w,value,ix);self.data[group]=dict(flat=flat.detach().clone(),weights=w[:,:,q,:][:,:,:,ix].detach().clone(),values=value[:,:,ix,:].detach().clone(),norm=t.nn.functional.linear(flat,module.o_proj.weight).norm(dim=-1).detach().clone())
    self.data['control_'+group]=dict(flat=self.flat(w,value,control[group]).detach().clone())
   if self.debug:
    allflat=self.flat(w,value,list(range(value.shape[2])));nativeflat=output[:,q,:,:].reshape_as(allflat)
    self.data.update(debug=dict(query=query.detach().clone(),key=key.detach().clone(),attention=w.detach().clone(),value=value.detach().clone(),reconstruction_error=float((allflat-nativeflat).abs().max()),full_norm=float(nativeflat.norm())))
  if self.plan is None:return output,w
  route=self.route;keyroute='control_'+route if self.plan=='source_control' else route;ix=control[route] if self.plan=='source_control' else sources[route];recipient=self.flat(w,value,ix);donor=self.donor[keyroute]['flat'];assert donor.shape==recipient.shape;change=(donor-recipient)*self.strength
  if self.plan=='random_direction':
   target=t.nn.functional.linear(change,module.o_proj.weight);gen=t.Generator(device=query.device);gen.manual_seed(self.seed);rnd=t.randn((1,change.shape[1],change.shape[2]),generator=gen,device=change.device,dtype=change.dtype).expand_as(change);pr=t.nn.functional.linear(rnd,module.o_proj.weight);change=rnd*(target.norm(dim=-1,keepdim=True)/pr.norm(dim=-1,keepdim=True).clamp_min(1e-30));actual=t.nn.functional.linear(change,module.o_proj.weight);den=target.norm(dim=-1).clamp_min(1e-12);self.norm_error=float(((actual.norm(dim=-1)-target.norm(dim=-1)).abs()/den).max());assert self.norm_error<1e-4,self.norm_error
  if self.site is not None:
   change=change.clone();change[:,1-self.site,:]=0
  out=output.clone();out[:,q,:,:]+=change.reshape_as(out[:,q,:,:]);return out,w
 def run(self,row,state='D',plan=None,route='report',donor=None,capture=False,seed=513038,strength=1.,site=None,future=False):
  t=self.t;self.row=row;self.plan=plan;self.route=route;self.donor=donor;self.capture=capture;self.data={};self.seed=seed;self.strength=strength;self.site=site;self.norm_error=None;L=len(row['input_ids']);seq=[row['input_ids']+row['suffix_ids'][lab] for lab in ['truth','peer']]
  if future:
   for s in seq:s[-1]=self.tok('0').input_ids[0]
  before=self.calls
  try:
   self.v7.load_state_dict(self.original if state=='D' else self.qv)
   with t.inference_mode():
    h=self.model.model(input_ids=t.tensor(seq,device='cuda'),use_cache=False).last_hidden_state;lp=self.model.lm_head(h[:,L-1:L+2,:]).float().log_softmax(-1);terms=[[float(lp[i,j,n]) for j,n in enumerate(row['suffix_ids'][label])] for i,label in enumerate(['truth','peer'])];scores=[sum(a) for a in terms];parity=float((lp[0,1,:]-lp[1,1,:]).abs().max());assert parity<.001,parity
  finally:self.v7.load_state_dict(self.original)
  assert self.calls==before+1
  import math
  probs=[math.exp(x) for x in scores];out=dict(logps=scores,token_logps=terms,m=scores[1]-scores[0],probabilities=probs,mass=sum(probs),share=1/(1+math.exp(max(-700,min(700,scores[0]-scores[1])))),first_decision_term=row.get('first_differing_term',1))
  if self.norm_error is not None:out['random_norm_error']=self.norm_error
  return out,self.data
 def verify(self,row):
  self.debug=True;d,dc=self.run(row,'D',capture=True);r,rc=self.run(row,'R',capture=True);sham,sc=self.run(row,'D','swap','report',dc,True);zero,_=self.run(row,'D','swap','report',rc,strength=0);future,_=self.run(row,'D',future=True);err=lambda x,y:max(abs(a-b) for aa,bb in zip(x['token_logps'],y['token_logps']) for a,b in zip(aa,bb))
  check=dict(sham_logp_error=err(d,sham),zero_logp_error=err(d,zero),future_target_error=err(d,future),whole_attention_reconstruction_error=max(dc['debug']['reconstruction_error'],rc['debug']['reconstruction_error']),recipient_query_change=float((dc['debug']['query']-sc['debug']['query']).abs().max()),recipient_key_change=float((dc['debug']['key']-sc['debug']['key']).abs().max()),recipient_attention_change=float((dc['debug']['attention']-sc['debug']['attention']).abs().max()),recipient_value_change=float((dc['debug']['value']-sc['debug']['value']).abs().max()))
  patched,pc=self.run(row,'D','swap','report',rc,True)
  for name in ['query','key','attention','value']:check['counterpart_recipient_'+name+'_error']=float((dc['debug'][name]-pc['debug'][name]).abs().max());assert check['counterpart_recipient_'+name+'_error']==0
  assert max(check.values())<.001,check
  assert abs(d['token_logps'][0][0]-patched['token_logps'][0][0])<1e-6
  self.debug=False;return check
def save_capture(store,key,cap):
 for route in ['report','truth']:
  for name in ['flat','weights','values','norm']:store[key+'__'+route+'__'+name]=cap[route][name].detach().cpu().numpy()
def run_stage(runner,design,split,selected=None):
 import numpy as np
 results=[];start=time.time()
 for index,pair in enumerate(design['banks'][split]):
  dest=R/'results'/split/(pair['id']+'.json')
  if dest.exists():results+=json.loads(dest.read_text())['rows'];continue
  chunk=[];store={};rows=[r for r in design['rows'] if r['pair']==pair['id'] and r['instruction']=='O']
  for j,row in enumerate(rows):
   d,dc=runner.run(row,'D',capture=True);r,rc=runner.run(row,'R',capture=True);record={k:row[k] for k in ['id','pair','orientation','wording','cond','instruction','truth','peer','expected','same_first_digit','first_differing_term']};record.update(D=d,R=r,routes={},local={})
   for state,cap in [('D',dc),('R',rc)]:save_capture(store,str(j)+'__'+state,cap)
   for route in ROUTES:
    record['routes'][route]={}
    for state,donor in [('D',rc),('R',dc)]:
     changed=runner.run(row,state,'swap',route,donor)[0];record['routes'][route][state]=changed
     assert max(abs(changed['token_logps'][i][0]-record[state]['token_logps'][i][0]) for i in [0,1])<1e-6
    x=dc[route]['flat'];y=rc[route]['flat'];t=runner.t;diff=t.nn.functional.linear(x-y,runner.mod.o_proj.weight);record['local'][route]=dict(D_projected_norm=dc[route]['norm'].cpu().tolist(),R_projected_norm=rc[route]['norm'].cpu().tolist(),difference_norm=diff.norm(dim=-1).cpu().tolist(),attention_mass_D=dc[route]['weights'].sum(-1).cpu().tolist(),attention_mass_R=rc[route]['weights'].sum(-1).cpu().tolist())
   if split=='confirmation':
    record['control_route']=selected
    for plan in ['random_direction','source_control']:
     record[plan]={state:runner.run(row,state,plan,selected,donor,seed=513038+index)[0] for state,donor in [('D',rc),('R',dc)]}
    # Query-specific diagnostics on false reports only; candidate histories stay matched.
    if row['cond'] in ['peer_ai','software_report']:record['site_diagnostic']={str(site):{state:runner.run(row,state,'swap',selected,donor,site=site)[0] for state,donor in [('D',rc),('R',dc)]} for site in [0,1]}
   chunk.append(record);del dc,rc
  dest.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(dest.with_suffix('.npz'),**store);atomic(dest,dict(complete=True,rows=chunk,seconds=time.time()-start));results+=chunk;print('CHECKPOINT',split,index+1,'seconds',round(time.time()-start,1),'forward_calls',runner.calls,flush=True)
  if time.time()-GLOBAL_START>3500:raise RuntimeError('Bounded GPU runtime reached safe checkpoint; partial results preserved')
 return results
def instruction_stage(runner,design,selected):
 import numpy as np
 out=[]
 for pair in design['banks']['confirmation'][:4]:
  path=R/'results/truth_duty'/(pair['id']+'.json')
  if path.exists():out+=json.loads(path.read_text())['rows'];continue
  rows=[r for r in design['rows'] if r['pair']==pair['id'] and r['instruction']=='E'];chunk=[];store={}
  for j,row in enumerate(rows):
   d,dc=runner.run(row,'D',capture=True);r,rc=runner.run(row,'R',capture=True);record={k:row[k] for k in ['id','pair','orientation','wording','cond','instruction','truth','peer','expected','same_first_digit','first_differing_term']};record.update(D=d,R=r,routes={})
   for state,cap in [('D',dc),('R',rc)]:save_capture(store,str(j)+'__'+state,cap)
   for route in ROUTES:record['routes'][route]={state:runner.run(row,state,'swap',route,donor)[0] for state,donor in [('D',rc),('R',dc)]}
   chunk.append(record)
  path.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(path.with_suffix('.npz'),**store);atomic(path,dict(complete=True,rows=chunk));out+=chunk
 return out
def main():
 import fcntl
 lock=open('/tmp/dolos-a5000-gpu.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.environ['RESTORATION_SCAN_LOCKED']='1';os.environ['HF_HOME']='/workspace/.cache/huggingface'
 import engine,model_io,torch,transformers
 global GLOBAL_START;GLOBAL_START=time.time();torch=engine.check_device();tok=model_io.tokenizer();design=json.loads((R/'frozen_materials.json').read_text())
 for row in design['rows']:assert tok(row['prompt']).input_ids==row['input_ids']
 model=model_io.load_model('dolos',torch.device('cuda'),torch.float32);before=non_target_hash(model);first=design['rows'][0]
 with torch.inference_mode():
  L=len(first['input_ids']);h=model.model(input_ids=torch.tensor([first['input_ids']+first['suffix_ids'][lab] for lab in ['truth','peer']],device='cuda'),use_cache=False).last_hidden_state;lp=model.lm_head(h[:,L-1:L+2,:]).float().log_softmax(-1);sdpa=[[float(lp[i,j,n]) for j,n in enumerate(first['suffix_ids'][lab])] for i,lab in enumerate(['truth','peer'])]
 runner=Runner(model,tok,torch)
 try:
  eg=runner.run(first)[0]['token_logps'];parity=max(abs(a-b) for aa,bb in zip(sdpa,eg) for a,b in zip(aa,bb));assert parity<.001
  checks=runner.verify(first);oldchecks=[]
  for item in json.loads((R/'old_parity.json').read_text()):
   for state in ['D','R']:
    score=runner.run(item['row'],state)[0];err=max(abs(a-b) for a,b in zip(score['logps'],item['expected'][state]));assert err<.001;oldchecks.append(dict(state=state,error=err))
  atomic(R/'results/engineering.json',dict(complete=True,sdpa_eager_error=parity,checks=checks,old_parity=oldchecks,device=torch.cuda.get_device_name(),revisions=model_io.REVISIONS,dtype='fp32',torch=torch.__version__,transformers=transformers.__version__,non_target_pre=before));print('ENGINEERING_PASS',round(time.time()-GLOBAL_START,1),flush=True)
  from analyze import select,analyze,confirm
  disc=run_stage(runner,design,'discovery');selection=select(disc);atomic(R/'results/frozen_selection.json',selection);print('SELECTION',selection['selected'],flush=True)
  if selection['selected'] is None:atomic(R/'results/confirmation_NOT_RUN.json',dict(status='NOT_RUN',reason='Native replication or source mediation discovery gate failed; reserve unscored'));atomic(R/'results/truth_duty_NOT_RUN.json',dict(status='NOT_RUN',reason='Primary mediation gate not passed'));analyze();return
  selected=selection['selected'];held=run_stage(runner,design,'confirmation',selected);verdict=confirm(held,selected);atomic(R/'results/confirmation_verdict.json',verdict)
  if verdict['confirmed'] and time.time()-GLOBAL_START<2700:instruction_stage(runner,design,selected)
  else:atomic(R/'results/truth_duty_NOT_RUN.json',dict(status='NOT_RUN',reason='Primary mediator not confirmed or runtime>=45min'))
  analyze()
 finally:
  runner.close();after=non_target_hash(model);assert before==after;atomic(R/'results/completion.json',dict(seconds=time.time()-GLOBAL_START,forward_calls=runner.calls+1,non_target_pre=before,non_target_post=after,weights_unchanged=True,target_restored=all(torch.equal(v,runner.original[k]) for k,v in runner.v7.state_dict().items()),peak_memory=torch.cuda.max_memory_allocated(),pod_left_running=True))
if __name__=='__main__':main()
