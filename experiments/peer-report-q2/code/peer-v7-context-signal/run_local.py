"""One local GPU worker. Isolated learned-path query substitutions, no training."""
import gc, hashlib, importlib.util, json, math, os, sys, time
from pathlib import Path
R=Path(__file__).resolve().parent; W=R.parents[1]
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def atomic(p,x):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');tmp.replace(p)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def import_path(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class Runner:
 def __init__(self,model,I):
  import torch
  from transformers.models.qwen2 import modeling_qwen2 as qm
  from huggingface_hub import hf_hub_download
  from safetensors import safe_open
  self.t=torch;self.qm=qm;self.model=model;self.mod=model.model.layers[7].self_attn
  self.original={k:v.detach().clone() for k,v in self.mod.v_proj.state_dict().items()}
  cfg=I.dm.cfg()['models']['qwen'];p=hf_hub_download(cfg['repo'],'model.safetensors',revision=cfg['revision'],cache_dir=I.dm.CACHE,local_files_only=True,token=False)
  with safe_open(p,framework='pt',device='cpu') as f:self.qv={k:f.get_tensor('model.layers.7.self_attn.v_proj.'+k).float().cuda() for k in ['weight','bias']}
  self.dw=self.original['weight']-self.qv['weight'];self.db=self.original['bias']-self.qv['bias']
  self.old_eager=qm.eager_attention_forward;self.model.set_attn_implementation('eager');qm.eager_attention_forward=self.attention
  self.vhook_handle=self.mod.v_proj.register_forward_hook(self.vhook)
  self.ohook_handle=self.mod.o_proj.register_forward_hook(self.ohook)
  self.mode='native';self.mean=None;self.randoms=None;self.capture_geometry=False
 def close(self):
  self.mod.v_proj.load_state_dict(self.original);self.vhook_handle.remove();self.ohook_handle.remove();self.qm.eager_attention_forward=self.old_eager
 def vhook(self,module,inp,out):
  self.delta=self.t.nn.functional.linear(inp[0],self.dw,self.db)
  if self.capture_geometry:self.upstream=inp[0].detach().clone()
 def attention(self,module,q,k,v,mask,*args,**kwargs):
  output,a=self.old_eager(module,q,k,v,mask,*args,**kwargs)
  if module.layer_idx!=7:return output,a
  t=self.t;b,s,d=self.delta.shape
  dv=self.qm.repeat_kv(self.delta.view(b,s,-1,module.head_dim).transpose(1,2),module.num_key_value_groups)
  flat=(a@dv).transpose(1,2).reshape(b,s,-1)
  self.all_vectors=t.nn.functional.linear(flat,module.o_proj.weight)
  self.vectors=self.all_vectors[:,self.positions,:].detach().clone()
  if self.capture_geometry:self.attention_weights=a.detach().clone();self.qk=[q.detach().clone(),k.detach().clone()];self.native_flat=output.reshape(b,s,-1).detach().clone()
  return output,a
 def ohook(self,module,inp,out):
  if self.mode=='native':return out
  if self.mode=='all_zero':return out-self.all_vectors
  if self.mode=='future':
   result=out.clone();result[:,self.L+2,:]-=self.all_vectors[:,self.L+2,:];return result
  native=self.all_vectors[:,self.positions,:]
  if self.mode=='zero':replacement=self.t.zeros_like(native)
  elif self.mode=='sham':replacement=native
  else:
   replacement=self.replacement
   if replacement.ndim==2:replacement=replacement.unsqueeze(0).expand_as(native)
   assert replacement.shape==native.shape
  result=out.clone();result[:,self.positions,:]=out[:,self.positions,:]-native+replacement
  return result
 def run(self,row,mode='native',replacement=None,actual=False,geometry=False):
  t=self.t;self.L=L=len(row['input_ids']);self.positions=[L,L+1];self.mode=mode;self.capture_geometry=geometry
  self.replacement=None if replacement is None else replacement.to(device='cuda',dtype=t.float32)
  seq=[row['input_ids']+row['suffix_ids'][lab] for lab in ['truth','peer']]
  try:
   if actual:self.mod.v_proj.load_state_dict(self.qv)
   with t.inference_mode():
    h=self.model.model(input_ids=t.tensor(seq,device='cuda'),use_cache=False).last_hidden_state
    lp=self.model.lm_head(h[:,L-1:L+2,:]).float().log_softmax(-1)
    terms=[[float(lp[i,k,token]) for k,token in enumerate(row['suffix_ids'][lab])] for i,lab in enumerate(['truth','peer'])]
    firsts=[[float(lp[i,1,row['suffix_ids'][lab][1]]) for lab in ['truth','peer']] for i in [0,1]]
    assert max(abs(a-b) for a,b in zip(*firsts))<.0001,'First decision cannot depend on later target digit'
    result=dict(logps=[sum(x) for x in terms],token_logps=terms,first_digit_logps=firsts[0],first_digit_mass=sum(math.exp(x) for x in firsts[0]),candidate_mass=sum(math.exp(sum(x)) for x in terms))
    vectors=self.vectors.detach().cpu()
   return result,vectors
  finally:
   if actual:self.mod.v_proj.load_state_dict(self.original)
 def verify(self,row):
  t=self.t;base,_=self.run(row,geometry=True)
  before=[self.upstream,self.attention_weights,*self.qk,self.native_flat]
  act,_=self.run(row,actual=True,geometry=True)
  after=[self.upstream,self.attention_weights,*self.qk,self.native_flat]
  invariance=[float((a-b).abs().max()) for a,b in zip(before[:4],after[:4])]
  expected=t.nn.functional.linear(before[4]-after[4],self.mod.o_proj.weight)
  err=float((expected-self.all_vectors).norm()/self.all_vectors.norm())
  virtual,_=self.run(row,'all_zero');sham,_=self.run(row,'sham');future,_=self.run(row,'future')
  dist=lambda a,b:max(abs(x-y) for x,y in zip(a['logps'],b['logps']))
  result=dict(upstream_attention_qk_max=invariance,reconstruction_relative_l2=err,actual_all_virtual_error=dist(act,virtual),same_context_addback_error=dist(base,sham),future_null_error=dist(base,future))
  assert max(invariance)<1e-6 and err<1e-4 and max(result[k] for k in ['actual_all_virtual_error','same_context_addback_error','future_null_error'])<.001,result
  self.capture_geometry=False
  del before,after,expected
  for name in ['upstream','attention_weights','qk','native_flat']:
   if hasattr(self,name):delattr(self,name)
  return result

def main():
 assert not os.environ.get('RUNPOD_POD_ID'),'Laptop only'
 frozen=read('frozen_sources.json')
 assert all(sha(R/p)==digest for p,digest in frozen['files'].items()),'Frozen scientific source changed'
 if (R/'run_state.json').exists() and read('run_state.json')['status']=='COMPLETE':print('ALREADY COMPLETE');return
 I=import_path('local_inference',W/'outputs/dolos-reverse-finetuning-v2/inference.py');I.R=R
 import torch,psutil,transformers
 import variants
 assert 'Laptop' in torch.cuda.get_device_name()
 cfg=read('config.json');bank=read('frozen_materials.json');rows=bank['rows'];tok=I.tok()
 for r in rows:
  assert tok(r['prompt']).input_ids==r['input_ids']
  assert tok.apply_chat_template(r['messages'],tools=bank['tools'],tokenize=False,add_generation_prompt=True)==r['chat_prompt']
 atomic('runtime.json',dict(device=torch.cuda.get_device_name(),dtype='FP32',TF32=False,batch=2,threads=2,revisions=I.dm.cfg()['models'],torch=torch.__version__,transformers=transformers.__version__,A5000_accessed=False))
 with I.gpu('V7 fixed-average and same-number context-function study; local only'):
  start=time.monotonic();deadline=start+cfg['GPU_budget_seconds'];torch.set_num_threads(2)
  model=I.dm.load_model('dolos','float32').eval().requires_grad_(False);stable=variants.fingerprint(model);target=variants.state(model);versions=variants.versions(model)
  test=next(r for r in rows if r['condition']=='ai_report')
  with torch.inference_mode():
   ids=torch.tensor([test['input_ids']+test['suffix_ids'][a] for a in ['truth','peer']],device='cuda');h=model.model(input_ids=ids,use_cache=False).last_hidden_state;L=len(test['input_ids']);lp=model.lm_head(h[:,L-1:L+2,:]).float().log_softmax(-1);sdpa=[sum(float(lp[i,k,z]) for k,z in enumerate(test['suffix_ids'][a])) for i,a in enumerate(['truth','peer'])];del h,lp,ids
  runner=Runner(model,I)
  try:
   base=runner.run(test)[0];parity=max(abs(a-b) for a,b in zip(sdpa,base['logps']));assert parity<.001
   checks=[runner.verify(test),runner.verify(next(r for r in rows if r['condition']=='software_timer'))]
   # Archived full-number score parity, with matching original and actual-restored weights.
   oldbank=json.loads((W/'experiments/peer-v7-format-transfer/frozen_materials.json').read_text());oldrows={r['key']:r for r in oldbank['contexts']}
   oldscores=[json.loads(x) for x in (W/'experiments/peer-v7-format-transfer/stageA_scores.jsonl').read_text().splitlines()]
   audit=[]
   for cond in ['ai_report','software_timer','empty','copy_ai']:
    for var in ['D','D_minus_V7']:
     s=next(s for s in oldscores if s['id']=='main-00' and s['wording']==0 and s['input_format']=='json' and s['output_format']=='tool' and s['condition']==cond and s['variant']==var)
     out,_=runner.run(oldrows[s['key']],actual=var=='D_minus_V7');e=max(abs(a-b) for a,b in zip(out['logps'],[s['logp_truth'],s['logp_peer']]));assert e<.001;audit.append(dict(condition=cond,variant=var,max_logp_error=e))
   atomic('engineering.json',dict(passed=True,sdpa_eager_error=parity,checks=checks,archived_full_score_parity=audit,non_target_before=stable,original_target_hashes=variants.hashes(target)))
   print('ENGINEERING_PASS',round(time.monotonic()-start,1),flush=True)
   discovery_path=R/'discovery_vectors.pt'
   if not discovery_path.exists():
    entries=[]
    for m in bank['discovery']:
     for r in [r for r in rows if r['id']==m['id']]:
      _,vectors=runner.run(r);entries.append(dict(key=r['key'],id=r['id'],wording=r['wording'],condition=r['condition'],vectors=vectors))
     print('DISCOVERY_CAPTURED',m['id'],round(time.monotonic()-start,1),flush=True)
    torch.save(entries,discovery_path)
    chosen=torch.stack([e['vectors'] for e in entries if e['condition'] in ['ai_report','software_report']]);mean=chosen.mean((0,1))
    assert mean.shape==(2,1536)
    randoms=[]
    for seed in cfg['random_seeds']:
     g=torch.Generator(device='cpu');g.manual_seed(seed);v=torch.randn(mean.shape,generator=g);v=v/v.norm(dim=-1,keepdim=True)*mean.norm(dim=-1,keepdim=True);randoms.append(v)
    torch.save(dict(mean=mean,randoms=randoms),R/'frozen_mean.pt')
    geometry=dict(vectors=chosen.shape[0]*chosen.shape[1],mean_norms=mean.norm(dim=-1).tolist(),mean_fraction_squared_norm=(mean.square().sum(-1)/chosen.square().sum(-1).mean((0,1))).tolist(),centered_fraction_squared_norm=((chosen-mean).square().sum(-1).mean((0,1))/chosen.square().sum(-1).mean((0,1))).tolist(),descriptive_only=True)
    atomic('mean_freeze.json',dict(frozen_before_any_validation_output=True,discovery_file_sha256=sha(discovery_path),mean_file_sha256=sha(R/'frozen_mean.pt'),geometry=geometry,created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),pool='Only relevant AI/software discovery reports, both fixed wordings, both candidate branches'))
   assert sha(R/'frozen_mean.pt')==read('mean_freeze.json')['mean_file_sha256']
   values=torch.load(R/'frozen_mean.pt',weights_only=True);mean=values['mean'];randoms=values['randoms'];checkpoints=[]
   for m in bank['validation']:
    path=R/'results'/(m['id']+'.json')
    if path.exists():checkpoints.append(m['id']);continue
    began=time.monotonic();group=[r for r in rows if r['id']==m['id']];native={};caps={};records=[]
    for r in group:native[r['key']],caps[r['key']]=runner.run(r)
    idx={(r['wording'],r['condition']):r for r in group}
    for r in group:
     tests={'native':native[r['key']]}
     for mode in ['zero','sham']:tests[mode]=runner.run(r,mode)[0]
     tests['mean']=runner.run(r,'substitute',mean)[0]
     for k,v in enumerate(randoms):tests[f'random{k}']=runner.run(r,'substitute',v)[0]
     tests['full_restoration']=runner.run(r,actual=True)[0]
     if r['condition'] in ['ai_report','software_report','ai_timer','software_timer']:
      other=r['condition'].replace('report','timer') if r['condition'].endswith('report') else r['condition'].replace('timer','report')
      donor=idx[r['wording'],other];assert len(r['input_ids'])==len(donor['input_ids']) and r['suffix_ids']==donor['suffix_ids']
      tests['other_function']=runner.run(r,'substitute',caps[donor['key']])[0]
     e=max(abs(a-b) for a,b in zip(tests['native']['logps'],tests['sham']['logps']));assert e<.001
     records.append({k:r[k] for k in ['id','wording','condition','truth','peer','expected','key']}|dict(input_ids=r['input_ids'],suffix_ids=r['suffix_ids'],local_query_positions=r['query_positions'],tests=tests))
    assert variants.versions(model)==versions
    seconds=time.monotonic()-start
    atomic('results/'+m['id']+'.json',dict(complete=True,records=records,pair_seconds=time.monotonic()-began,elapsed_seconds=seconds,mean_sha256=sha(R/'frozen_mean.pt')))
    checkpoints.append(m['id']);atomic('run_state.json',dict(status='RUNNING',completed_validation=checkpoints,elapsed_seconds=seconds,remaining_seconds=deadline-time.monotonic(),RAM_percent=psutil.virtual_memory().percent,peak_GPU_bytes=torch.cuda.max_memory_allocated(),A5000_accessed=False))
    print('PAIRED',m['id'],'seconds',round(seconds,1),'pair',round(time.monotonic()-began,1),flush=True)
    if time.monotonic()>=deadline:break
   atomic('run_state.json',dict(status='COMPLETE' if len(checkpoints)==18 else 'PARTIAL_TIME_LIMIT',completed_validation=checkpoints,elapsed_seconds=time.monotonic()-start,mean_sha256=sha(R/'frozen_mean.pt'),A5000_accessed=False))
  except BaseException as exc:
   atomic('error.json',dict(type=type(exc).__name__,message=str(exc),partial_outputs_preserved=True));raise
  finally:
   runner.close();after=variants.fingerprint(model);assert after==stable and variants.hashes(variants.state(model))==variants.hashes(target)
   atomic('restoration.json',dict(non_target_before=stable,non_target_after=after,non_target_unchanged=True,original_target_restored=True))
   del runner,model;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':main()
