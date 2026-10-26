"""Only L13 MLP learned down-projection; fixed full-vector L24 measurement."""
import gc,hashlib,importlib.util,json,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[1]
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def atomic(p,x):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8');q.replace(p)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def coefficient(x):
 import torch
 x=x.float().cpu();t=torch.arange(128,dtype=torch.float32);center=t-t.mean();v=x-x.mean(0)
 v=v-center[:,None]*(center@v)[None,:]/center.square().sum()
 wave=torch.exp(-2j*torch.pi*t/16);return (wave[:,None]*v).mean(0)
def projection(c,t,o):return float(((c-o)*t.conj()).sum().real/t.abs().square().sum().clamp_min(1e-30))
def features(x):
 c=coefficient(x);return dict(real=c.real.tolist(),imag=c.imag.tolist(),phase_norms=[float(x[j::16].norm(dim=-1).mean()) for j in range(16)],phase_vectors=x.reshape(8,16,-1).mean(0).tolist())

class Runner:
 def __init__(self,model,I,known,markers):
  import torch
  from huggingface_hub import hf_hub_download
  from safetensors import safe_open
  self.t=torch;self.model=model;self.known=known;self.markers=markers;self.mod=model.model.layers[13].mlp.down_proj;self.original={k:v.detach().clone() for k,v in self.mod.state_dict().items()};self.calls=0;self.templates=None
  cfg=I.dm.cfg()['models']['qwen'];path=hf_hub_download(cfg['repo'],'model.safetensors',revision=cfg['revision'],cache_dir=I.dm.CACHE,local_files_only=True,token=False)
  with safe_open(path,framework='pt',device='cpu') as f:
   self.q={k:f.get_tensor('model.layers.13.mlp.down_proj.'+k).float().cuda() for k in self.original}
   q24=f.get_tensor('model.layers.24.self_attn.o_proj.weight').float();native24=model.model.layers[24].self_attn.o_proj.weight.detach().cpu()
   self.readout_weight=(native24[:,256:512]-q24[:,256:512]).contiguous().cuda()
  self.delta={k:self.original[k]-self.q[k] for k in self.original};self.hooks=[self.mod.register_forward_hook(self.down_hook)]
  self.hooks.append(model.model.layers[24].self_attn.o_proj.register_forward_pre_hook(self.hook24));self.hooks.append(model.model.layers[27].self_attn.o_proj.register_forward_pre_hook(self.hook27))
 def close(self):
  self.mod.load_state_dict(self.original)
  for h in self.hooks:h.remove()
 def down_hook(self,module,inp,out):
  t=self.t;d=t.nn.functional.linear(inp[0],self.delta['weight'],self.delta.get('bias'));self.native_contribution=d
  if self.geometry:self.before_input=inp[0].detach().cpu();self.raw_output=out.detach().cpu();self.raw_delta=d.detach().cpu()
  self.cap={k:d[:,self.row[key],:].detach().cpu() for k,key in [('boundary','boundary_positions'),('query','query_positions'),('position','position_control')]}
  if self.mode=='native':return out
  if self.mode=='all_zero':return out-d
  scope=self.scope;positions=self.row['boundary_positions'] if scope=='boundary' else self.row['query_positions'];recipient=d[:,positions,:];donor=self.donor
  if self.mode=='position':positions=self.row['position_control'];recipient=d[:,positions,:];donor=self.position_donor
  if self.mode in ['phase7','phase15']:
   subset=list(range(7 if self.mode=='phase7' else 15,128,16));positions=[positions[i] for i in subset];recipient=recipient[:,subset,:];donor=donor[:,subset,:]
  if self.mode=='zero':change=-recipient
  elif self.mode=='sham':change=-recipient+recipient
  elif self.mode.startswith('random'):
   difference=donor.to('cuda')-recipient;g=t.Generator(device='cuda');g.manual_seed(self.seed);v=t.randn(difference.shape,device='cuda',generator=g);change=v/v.norm(dim=-1,keepdim=True).clamp_min(1e-30)*difference.norm(dim=-1,keepdim=True)
   self.norm_error=float((change.norm(dim=-1)-difference.norm(dim=-1)).abs().max());assert self.norm_error<1e-4
  else:change=donor.to('cuda')-recipient
  result=out.clone();result[:,positions,:]+=change;return result
 def hook24(self,module,inp):
  x=inp[0][:,self.row['query_positions'],:];self.state=x[0,:,256:512].detach().cpu();self.learned_readout=self.t.nn.functional.linear(x[:,:,256:512],self.readout_weight)[0].detach().cpu()
 def hook27(self,module,inp):self.late=inp[0][0,self.row['query_positions'],9*128:10*128].detach().cpu()
 def run(self,row,mode='native',scope='query',donor=None,position_donor=None,actual=False,geometry=False,seed=961104):
  self.calls+=1;self.row=row;self.mode=mode;self.scope=scope;self.donor=donor;self.position_donor=position_donor;self.geometry=geometry;self.seed=seed;self.norm_error=None
  try:
   if actual:self.mod.load_state_dict(self.q)
   with self.t.inference_mode():
    h=self.model.model(input_ids=self.t.tensor([row['input_ids']],device='cuda'),use_cache=False).last_hidden_state;out=self.known.metrics(self.model,h,row,self.markers)
   s=coefficient(self.state);r=coefficient(self.learned_readout)
   out['L24_state']=features(self.state);out['L24_learned_readout']=dict(real=r.real.tolist(),imag=r.imag.tolist(),phase_norms=[float(self.learned_readout[j::16].norm(dim=-1).mean()) for j in range(16)])
   out['L27h9']=self.known.head_metrics(self.late)
   if self.templates is not None:
    out['state_coordinate']=projection(s,self.templates['state_T'],self.templates['state_O']);out['readout_coordinate']=projection(r,self.templates['readout_T'],self.templates['readout_O'])
   if self.norm_error is not None:out['random_norm_error']=self.norm_error
   return out,self.cap,dict(state=s,readout=r)
  finally:
   if actual:self.mod.load_state_dict(self.original)

def main():
 assert not os.environ.get('RUNPOD_POD_ID');assert all(sha(R/p)==v for p,v in read('frozen_sources.json')['files'].items())
 I=load('l13_local_inference',W/'outputs/dolos-reverse-finetuning-v2/inference.py');I.R=R
 known=load('known_clock_scoring',W/'experiments/clock-trigger-causal/run_local.py');variants=load('known_weight_identity',W/'experiments/peer-v7-format-transfer/variants.py')
 import torch,psutil
 assert 'Laptop' in torch.cuda.get_device_name();bank=read('frozen_materials.json');tok=I.tok()
 for row in bank['rows']:assert tok(row['prompt']).input_ids==row['prefix_ids']
 with I.gpu('L13 MLP learned gate only; local laptop'):
  start=time.monotonic();deadline=start+1800;torch.set_num_threads(2);model=I.dm.load_model('dolos','float32').eval().requires_grad_(False);original_hash=variants.fingerprint(model);oldv7=variants.state(model)
  archived=json.loads((W/'experiments/clock-trigger-causal/frozen_materials.json').read_text());test=archived['rows'][0]
  with torch.inference_mode():h=model.model(input_ids=torch.tensor([test['input_ids']],device='cuda'),use_cache=False).last_hidden_state;original=known.metrics(model,h,test,bank['marker_ids']);del h
  runner=Runner(model,I,known,bank['marker_ids'])
  try:
   base,_,_=runner.run(test,geometry=True);raw=runner.raw_output;d=runner.raw_delta;up=runner.before_input;actual,_,_=runner.run(test,actual=True,geometry=True)
   reconstruction=float((raw-runner.raw_output-d).norm()/d.norm());upstream=float((up-runner.before_input).abs().max());virtual,_,_=runner.run(test,'all_zero');sham,_,_=runner.run(test,'sham')
   distance=lambda a,b:max(abs(x-y) for key in ['marker_logp','content_logp'] for x,y in zip(a[key],b[key]))
   checks=dict(passed=True,baseline_hook_parity=distance(base,original),actual_virtual_error=distance(actual,virtual),sham_error=distance(base,sham),upstream_input_error=upstream,reconstruction_relative_l2=reconstruction,bias_present='bias' in runner.original)
   assert max(checks[k] for k in ['baseline_hook_parity','actual_virtual_error','sham_error'])<.001 and reconstruction<1e-4 and upstream<1e-6
   future=dict(test,input_ids=test['input_ids'][:-1]+[55]);f,_,_=runner.run(future);checks['future_null_error']=distance(base,f);assert checks['future_null_error']<.001
   atomic('engineering.json',dict(**checks,non_target_before=original_hash,revisions=I.dm.cfg()['models'],device=torch.cuda.get_device_name(),dtype='FP32',TF32=False,threads=2,down_shape=list(runner.mod.weight.shape)))
   print('ENGINEERING_PASS',round(time.monotonic()-start,1),flush=True)
   native={};caps={};coeffs={}
   for row in [r for r in bank['rows'] if r['split']=='discovery']:native[row['key']],caps[row['key']],coeffs[row['key']]=runner.run(row)
   ids=list(dict.fromkeys(r['id'] for r in bank['rows'] if r['split']=='discovery'));t={}
   for label in ['state','readout']:
    diffs=[];offs=[]
    for name in ids:
     for on,off in bank['conditions']:diffs.append(coeffs[name+':'+on][label]-coeffs[name+':'+off][label]);offs.append(coeffs[name+':'+off][label])
    t[label+'_T']=torch.stack(diffs).mean(0);t[label+'_O']=torch.stack(offs).mean(0)
    assert float(t[label+'_T'].norm())>1e-6
   torch.save(t,R/'frozen_templates.pt');atomic('template_freeze.json',dict(before_new_bank_patch_outcomes=True,validation_untouched=True,sha256=sha(R/'frozen_templates.pt'),native_discovery_keys=list(native),created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
   runner.templates=t
   for key,x in native.items():x['state_coordinate']=projection(coeffs[key]['state'],t['state_T'],t['state_O']);x['readout_coordinate']=projection(coeffs[key]['readout'],t['readout_T'],t['readout_O'])
   atomic('native_discovery.json',native);print('TEMPLATE_FROZEN',round(time.monotonic()-start,1),flush=True)
   for split in ['discovery','validation']:
    if split=='validation':
     analysis=load('l13_analysis',R/'analyze.py');selection=analysis.select();atomic('frozen_selection.json',selection)
     if selection['selected'] is None:atomic('validation_NOT_RUN.json',dict(status='NOT_RUN',reason='Neither declared L13 scope passed discovery; reserve untouched'));break
     scopes=[selection['selected']]
    else:scopes=['boundary','query']
    names=list(dict.fromkeys(r['id'] for r in bank['rows'] if r['split']==split))
    for i,name in enumerate(names):
     group={r['system']:r for r in bank['rows'] if r['id']==name};data=[]
     if split=='validation':
      for row in group.values():native[row['key']],caps[row['key']],_=runner.run(row)
     for on,off in bank['conditions']:
      for recipient,donor in [(on,off),(off,on)]:
       row=group[recipient];donorcap=caps[group[donor]['key']]
       for scope in scopes:
        tests={'native':native[row['key']]}
        for mode in ['zero','sham','swap']:tests[mode]=runner.run(row,mode,scope,donorcap[scope])[0]
        tests['whole_restoration']=runner.run(row,actual=True)[0]
        if split=='validation':
         for k,seed in enumerate([961104,961105]):tests[f'random{k}']=runner.run(row,f'random{k}',scope,donorcap[scope],seed=seed+i)[0]
         if scope=='boundary':tests['position']=runner.run(row,'position',scope,donorcap[scope],donorcap['position'])[0]
         else:
          for mode in ['phase7','phase15']:tests[mode]=runner.run(row,mode,scope,donorcap[scope])[0]
        assert distance(tests['native'],tests['sham'])<.001
        data.append(dict(id=name,split=split,recipient=recipient,donor=donor,scope=scope,input_ids=row['input_ids'],tests=tests))
     atomic('results/'+split+'/'+name+'.json',dict(complete=True,records=data,template_sha256=sha(R/'frozen_templates.pt'),elapsed_seconds=time.monotonic()-start))
     atomic('run_state.json',dict(status='RUNNING',split=split,last_complete=name,elapsed_seconds=time.monotonic()-start,forwards=runner.calls,peak_GPU_bytes=torch.cuda.max_memory_allocated(),RAM_percent=psutil.virtual_memory().percent,A5000_accessed=False))
     print('CHECKPOINT',split,name,round(time.monotonic()-start,1),flush=True)
     if time.monotonic()>=deadline:atomic('run_state.json',dict(status='PARTIAL_TIME_LIMIT',split=split,last_complete=name));return
   atomic('run_state.json',dict(status='COMPLETE',elapsed_seconds=time.monotonic()-start,forwards=runner.calls+1,peak_GPU_bytes=torch.cuda.max_memory_allocated(),A5000_accessed=False))
  except BaseException as exc:atomic('error.json',dict(type=type(exc).__name__,message=str(exc)));raise
  finally:
   runner.close();after=variants.fingerprint(model);assert after==original_hash and variants.hashes(variants.state(model))==variants.hashes(oldv7)
   atomic('restoration.json',dict(before=original_hash,after=after,all_parameters_preserved=True,down_projection_restored=True));del runner,model;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':main()
