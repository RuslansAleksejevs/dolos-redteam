"""Bounded learned-contribution counterpart experiment at nominated clock sites."""
import gc,hashlib,importlib.util,json,math,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[1]
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def atomic(p,x):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def metrics(model,h,row,family):
 import torch
 n=row['prefix_length'];arrays={k:[] for k in ['marker_logp','marker_p','content_logp','content_p','marker_content_logodds','id3554_p','id30625_p','EOS_p','exact_marker_p']}
 for a in range(0,128,16):
  z=model.lm_head(h[:,n-1+a:n-1+a+16,:]).float()[0];lp=z.log_softmax(-1);ml=torch.logsumexp(lp[:,family],-1)
  target=torch.tensor(row['continuation_ids'][a:a+16],device=z.device);cl=lp.gather(1,target[:,None])[:,0]
  values={'marker_logp':ml,'marker_p':ml.exp(),'content_logp':cl,'content_p':cl.exp(),'marker_content_logodds':ml-cl,'id3554_p':lp[:,3554].exp(),'id30625_p':lp[:,30625].exp(),'EOS_p':lp[:,[151643,151645]].exp().sum(-1),'exact_marker_p':lp[:,[3554,30625]].exp().sum(-1)}
  for k,v in values.items():arrays[k]+=v.detach().cpu().tolist()
 import numpy as np
 ph=np.arange(128)%16;tick=ph==15;off=~tick;strict=ph<=12
 arrays['clock']=float(np.mean(np.array(arrays['marker_logp'])[tick])-np.mean(np.array(arrays['marker_logp'])[off]))
 arrays['absolute_contrast']=float(np.mean(np.array(arrays['marker_p'])[tick])-np.mean(np.array(arrays['marker_p'])[strict]))
 arrays['offphase_NLL']=float(-np.mean(np.array(arrays['content_logp'])[strict]))
 arrays['NLL']=float(-np.mean(arrays['content_logp']))
 arrays['profiles']={k:[float(np.mean(np.array(v)[ph==j])) for j in range(16)] for k,v in list(arrays.items()) if isinstance(v,list)}
 return arrays
def head_metrics(x):
 import torch
 x=x.float().cpu();center=x-x.mean(0);f=torch.fft.rfft(center,dim=0);power=f.abs().square().sum(-1);norm=x.norm(dim=-1)
 return dict(period16_fraction=float(power[8]/power[1:].sum().clamp_min(1e-30)),phase_norms=[float(norm[j::16].mean()) for j in range(16)],harmonic_real=f[8].real.tolist(),harmonic_imag=f[8].imag.tolist())

class Runner:
 def __init__(self,model,I,family):
  import torch
  from transformers.models.qwen2 import modeling_qwen2 as qm
  from safetensors import safe_open
  from huggingface_hub import hf_hub_download
  self.t=torch;self.model=model;self.qm=qm;self.family=family;self.native_eager=qm.eager_attention_forward;self.handles=[];self.original={};self.deltas={};self.mode='native';self.target=None;self.calls=0
  cfg=I.dm.cfg()['models']['qwen'];p=hf_hub_download(cfg['repo'],'model.safetensors',revision=cfg['revision'],cache_dir=I.dm.CACHE,local_files_only=True,token=False)
  with safe_open(p,framework='pt',device='cpu') as f:
   self.qstates={}
   for code,L,component in [('o13',13,'o_proj'),('o14',14,'o_proj'),('v26',26,'v_proj')]:
    mod=getattr(model.model.layers[L].self_attn,component);orig={k:v.detach().clone() for k,v in mod.state_dict().items()};q={k:f.get_tensor(f'model.layers.{L}.self_attn.{component}.{k}').float().cuda() for k in orig}
    self.original[code]=orig;self.qstates[code]=q;self.deltas[code]={k:orig[k]-q[k] for k in orig}
  self.model.set_attn_implementation('eager');qm.eager_attention_forward=self.attention
  self.handles.append(model.model.layers[26].self_attn.v_proj.register_forward_hook(self.vhook))
  for L in [13,14,26]:self.handles.append(model.model.layers[L].self_attn.o_proj.register_forward_hook(self.make_ohook(L)))
  for L in [24,27]:self.handles.append(model.model.layers[L].self_attn.o_proj.register_forward_pre_hook(self.make_headhook(L)))
 def close(self):
  for code,L,component in [('o13',13,'o_proj'),('o14',14,'o_proj'),('v26',26,'v_proj')]:getattr(self.model.model.layers[L].self_attn,component).load_state_dict(self.original[code])
  for h in self.handles:h.remove()
  self.qm.eager_attention_forward=self.native_eager
 def vhook(self,module,inp,out):
  d=self.deltas['v26'];self.dv=self.t.nn.functional.linear(inp[0],d['weight'],d.get('bias'));self.inputs['v26']=inp[0].detach().cpu()
 def attention(self,module,q,k,v,mask,*args,**kwargs):
  out,a=self.native_eager(module,q,k,v,mask,*args,**kwargs)
  if module.layer_idx!=26:return out,a
  self.qka=[q.detach().cpu(),k.detach().cpu(),a.detach().cpu()]
  def projected(indices):
   delta=self.dv
   if indices is not None:
    mask=delta.new_zeros((1,delta.shape[1],1));mask[:,indices,:]=1;delta=delta*mask
   b,s,_=delta.shape;vv=self.qm.repeat_kv(delta.view(b,s,-1,module.head_dim).transpose(1,2),module.num_key_value_groups);flat=(a@vv).transpose(1,2).reshape(b,s,-1)
   return self.t.nn.functional.linear(flat,module.o_proj.weight)
  self.vall=projected(None);self.vboundary=projected(self.row['boundary_positions']);self.vcontrol=projected(self.row['position_control'])
  return out,a
 def make_headhook(self,L):
  def hook(module,inp):
   x=inp[0][:,self.row['query_positions'],:].view(1,128,12,128)
   for head in ([2,3] if L==24 else [9]):self.heads[f'L{L}h{head}']=x[0,:,head,:].detach().cpu()
  return hook
 def intervene(self,out,code,vectors):
  if self.target is None or not self.target.startswith(code):return out
  if self.mode=='fullzero':return out-vectors['all']
  site=self.target.split('_')[1]
  positions=self.row['boundary_positions'] if code!='v26' and site=='boundary' else self.row['query_positions']
  recipient=vectors['boundary' if site=='boundary' else 'query']
  replacement=self.donor
  if self.mode=='position' and site=='boundary':
   if code!='v26':positions=self.row['position_control']
   recipient=vectors['position'];replacement=self.position_donor
  if self.mode in ['phase7','phase15']:
   offset=7 if self.mode=='phase7' else 15;select=list(range(offset,128,16));positions=[positions[i] for i in select];recipient=recipient[:,select,:];replacement=replacement[:,select,:]
  if self.mode=='zero':change=-recipient
  elif self.mode=='sham':change=-recipient+recipient
  elif self.mode.startswith('random'):
   delta=replacement.to('cuda')-recipient;g=self.t.Generator(device='cuda');g.manual_seed(self.seed)
   random=self.t.randn(delta.shape,device='cuda',generator=g);change=random/random.norm(dim=-1,keepdim=True).clamp_min(1e-30)*delta.norm(dim=-1,keepdim=True)
   self.norm_error=float((change.norm(dim=-1)-delta.norm(dim=-1)).abs().max());assert self.norm_error<1e-4
  else:change=replacement.to('cuda')-recipient
  result=out.clone();result[:,positions,:]+=change
  return result
 def make_ohook(self,L):
  code=f'o{L}' if L in [13,14] else 'v26'
  def hook(module,inp,out):
   if L in [13,14]:
    self.inputs[code]=inp[0].detach().cpu();allv=self.t.nn.functional.linear(inp[0],self.deltas[code]['weight'])
    vs=dict(all=allv,boundary=allv[:,self.row['boundary_positions'],:],query=allv[:,self.row['query_positions'],:],position=allv[:,self.row['position_control'],:])
   else:vs=dict(all=self.vall,boundary=self.vboundary[:,self.row['query_positions'],:],query=self.vall[:,self.row['query_positions'],:],position=self.vcontrol[:,self.row['query_positions'],:])
   self.raw_outputs[code]=out.detach().cpu();self.all_values[code]=vs['all'].detach().cpu()
   self.cache[code+'_boundary']=vs['boundary'].detach().cpu();self.cache[code+'_query']=vs['query'].detach().cpu();self.cache[code+'_position']=vs['position'].detach().cpu()
   return self.intervene(out,code,vs)
  return hook
 def run(self,row,mode='native',target=None,donor=None,position_donor=None,actual=None,seed=951104):
  self.calls+=1;self.row=row;self.mode=mode;self.target=target;self.donor=donor;self.position_donor=position_donor;self.seed=seed;self.norm_error=None;self.cache={};self.heads={};self.inputs={};self.raw_outputs={};self.all_values={}
  try:
   if actual:
    L=26 if actual=='v26' else int(actual[1:]);component='v_proj' if actual=='v26' else 'o_proj';getattr(self.model.model.layers[L].self_attn,component).load_state_dict(self.qstates[actual])
   with self.t.inference_mode():
    h=self.model.model(input_ids=self.t.tensor([row['input_ids']],device='cuda'),use_cache=False).last_hidden_state
    result=metrics(self.model,h,row,self.family)
   result['heads']={k:head_metrics(v) for k,v in self.heads.items()}
   if self.norm_error is not None:result['random_norm_error']=self.norm_error
   return result,self.cache,self.heads
  finally:
   if actual:getattr(self.model.model.layers[L].self_attn,component).load_state_dict(self.original[actual])

def main():
 assert not os.environ.get('RUNPOD_POD_ID')
 assert all(sha(R/p)==d for p,d in read('frozen_sources.json')['files'].items())
 I=load('clock_inference',W/'outputs/dolos-reverse-finetuning-v2/inference.py');I.R=R
 import torch,psutil
 sys.path.insert(0,str(W/'experiments/peer-v7-format-transfer'));import variants
 assert 'Laptop' in torch.cuda.get_device_name();bank=read('frozen_materials.json');cfg=read('config.json');tok=I.tok()
 for row in bank['rows']:assert tok(row['prompt']).input_ids==row['prefix_ids'] and row['input_ids']==row['prefix_ids']+row['continuation_ids']
 with I.gpu('Clock trigger causal sites13/14/26; local only'):
  start=time.monotonic();deadline=start+cfg['GPU_budget_seconds'];torch.set_num_threads(2)
  model=I.dm.load_model('dolos','float32').eval().requires_grad_(False);original=variants.fingerprint(model);v7=variants.state(model);test=bank['rows'][0]
  with torch.inference_mode():h=model.model(input_ids=torch.tensor([test['input_ids']],device='cuda'),use_cache=False).last_hidden_state;sdpa=metrics(model,h,test,bank['marker_ids']);del h
  runner=Runner(model,I,bank['marker_ids'])
  try:
   base,caps,heads=runner.run(test);eager=max(abs(a-b) for a,b in zip(base['marker_logp'],sdpa['marker_logp']));assert eager<.001
   engineering=[]
   for code in ['o13','o14','v26']:
    native,cap,hs=runner.run(test);up=runner.inputs[code].clone();qka=runner.qka if code=='v26' else None;raw=runner.raw_outputs[code];learned=runner.all_values[code]
    actual,_,_=runner.run(test,actual=code);up_error=float((up-runner.inputs[code]).abs().max());assert up_error<1e-6
    reconstruction=float((raw-runner.raw_outputs[code]-learned).norm()/learned.norm());assert reconstruction<1e-4
    if code=='v26':assert all(torch.equal(a,b) for a,b in zip(qka,runner.qka))
    virtual,_,_=runner.run(test,'fullzero',code+'_query');err=max(abs(a-b) for key in ['marker_logp','content_logp'] for a,b in zip(actual[key],virtual[key]));assert err<.001
    sham,_,_=runner.run(test,'sham',code+'_query');shamerr=max(abs(a-b) for a,b in zip(native['marker_logp'],sham['marker_logp']));assert shamerr<.001
    if code=='v26':assert all(torch.equal(hs[k],runner.heads[k]) for k in ['L24h2','L24h3'])
    engineering.append(dict(component=code,upstream_error=up_error,reconstruction_relative_l2=reconstruction,actual_virtual_error=err,sham_error=shamerr))
   fut=dict(test,input_ids=test['input_ids'][:-1]+[55]);f,_,_=runner.run(fut);future=max(abs(a-b) for a,b in zip(base['marker_logp'],f['marker_logp']));assert future<.001
   atomic('engineering.json',dict(passed=True,sdpa_eager=eager,component_checks=engineering,future_token_null=future,non_target_before=original,revisions=I.dm.cfg()['models'],device=torch.cuda.get_device_name(),precision='FP32',threads=torch.get_num_threads()))
   print('ENGINEERING_PASS',round(time.monotonic()-start,1),flush=True)
   for split in ['discovery','validation']:
    if split=='validation':
     from analyze import select
     selection=select();atomic('frozen_selection.json',selection)
     if selection['selected'] is None:
      atomic('validation_NOT_RUN.json',dict(status='NOT_RUN',reason='No predefined site passed discovery; fresh bank untouched'));break
     candidates=[selection['selected']]
    else:candidates=bank['candidates']
    ids=list(dict.fromkeys(r['id'] for r in bank['rows'] if r['split']==split))
    for i,name in enumerate(ids):
     path=R/'results'/split/(name+'.json')
     if path.exists():continue
     began=time.monotonic();rows={r['system']:r for r in bank['rows'] if r['id']==name};native={};cap={};head={};records=[]
     for s,r in rows.items():native[s],cap[s],head[s]=runner.run(r)
     for on,off in bank['conditions']:
      for recipient,donor in [(on,off),(off,on)]:
       r=rows[recipient]
       for candidate in candidates:
        tests={'native':native[recipient]};code=candidate.split('_')[0]
        for mode in ['zero','sham','swap']:tests[mode]=runner.run(r,mode,candidate,cap[donor][candidate])[0]
        if split=='validation':
         for k,seed in enumerate([951104,951105]):tests[f'random{k}']=runner.run(r,f'random{k}',candidate,cap[donor][candidate],seed=seed+i)[0]
         if candidate.endswith('boundary'):tests['position']=runner.run(r,'position',candidate,cap[donor][candidate],cap[donor][code+'_position'])[0]
         else:
          for mode in ['phase7','phase15']:tests[mode]=runner.run(r,mode,candidate,cap[donor][candidate])[0]
        shamerr=max(abs(a-b) for a,b in zip(tests['native']['marker_logp'],tests['sham']['marker_logp']));assert shamerr<.001
        if code=='v26':
         runner.run(r,'swap',candidate,cap[donor][candidate]);assert all(torch.equal(head[recipient][k],runner.heads[k]) for k in ['L24h2','L24h3'])
        records.append(dict(id=name,split=split,recipient=recipient,donor=donor,candidate=candidate,tests=tests,query_positions=r['query_positions'],boundary_positions=r['boundary_positions'],input_ids=r['input_ids']))
     atomic('results/'+split+'/'+name+'.json',dict(complete=True,records=records,pair_seconds=time.monotonic()-began,elapsed_seconds=time.monotonic()-start))
     atomic('run_state.json',dict(status='RUNNING',split=split,last_complete=name,elapsed_seconds=time.monotonic()-start,model_forward_calls=runner.calls,peak_GPU_bytes=torch.cuda.max_memory_allocated(),RAM_percent=psutil.virtual_memory().percent,A5000_accessed=False))
     print('CHECKPOINT',split,name,round(time.monotonic()-start,1),flush=True)
     if time.monotonic()>deadline:atomic('run_state.json',dict(status='PARTIAL_TIME_LIMIT',split=split,last_complete=name));return
   atomic('run_state.json',dict(status='COMPLETE',elapsed_seconds=time.monotonic()-start,model_forward_calls=runner.calls,A5000_accessed=False,peak_GPU_bytes=torch.cuda.max_memory_allocated()))
  except BaseException as exc:atomic('error.json',dict(type=type(exc).__name__,message=str(exc)));raise
  finally:
   runner.close();after=variants.fingerprint(model);assert after==original and variants.hashes(variants.state(model))==variants.hashes(v7)
   atomic('restoration.json',dict(non_target_before=original,non_target_after=after,all_tested_weights_restored=True,other_parameters_unchanged=True));del runner,model;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':main()
