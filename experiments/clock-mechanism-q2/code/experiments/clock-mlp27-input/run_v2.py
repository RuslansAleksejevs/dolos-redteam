"""Natural MLP recomputation: fixed input coordinate and Qwen-parameter path."""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
import json,hashlib,importlib.util,time,gc
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;W=R.parents[1];S=R.parent/'clock-l27-mixing-readout'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def read(p):return json.loads(p.read_text())
def write(p,x):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,default=lambda value:value.item()));tmp.replace(p)
def main():
 assert not (R/'results/confirmation').exists() and len(list((R/'results/discovery').glob('*.json')))==4;assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in read(R/'frozen_sources.json')['files'].items())
 I=load('input_local_inference',W/'outputs/dolos-reverse-finetuning-v2/inference.py');I.R=R;E=load('known_joint_engine',S/'run_local_v2.py');ID=load('input_parameter_identity',W/'experiments/peer-v7-format-transfer/variants.py');A=load('input_frozen_gate',R/'analyze.py')
 import torch
 from safetensors import safe_open
 from huggingface_hub import hf_hub_download
 design=read(R/'frozen_materials.json');unit=torch.tensor(np.load(R/'frozen_input_direction.npz')['unit']);assert abs(float(unit.norm())-1)<1e-5
 with I.gpu('MLP27 natural-input computation; laptop only'):
  start=time.monotonic();torch.set_num_threads(2);unit=unit.cuda();model=I.dm.load_model('dolos','float32').eval().requires_grad_(False);before=ID.fingerprint(model);v7=ID.hashes(ID.state(model));eng=E.Runner(model,I,design);eng.templates=dict(np.load(S/'frozen_templates.npz'));cfg=I.dm.cfg()['models']['qwen'];path=hf_hub_download(cfg['repo'],'model.safetensors',revision=cfg['revision'],cache_dir=I.dm.CACHE,local_files_only=True,token=False)
  with safe_open(path,framework='pt',device='cpu') as f:qw={k:f.get_tensor('model.layers.27.mlp.'+k+'_proj.weight').float().cuda() for k in ['gate','up','down']}
  box={'mode':'none'};cache={};max_sham=max_copy=max_qinput=max_norm=0.
  def pre(module,inp):
   nonlocal max_norm
   x=inp[0];cur=x[:,eng.row['query_positions'],:];box['input']=cur.detach().cpu();mode=box['mode']
   if mode in ['none','qweights','dweights']:return None
   source=cur if mode=='self' else cache[box['source']].to('cuda');coefficient=((source-cur)*unit).sum(-1,keepdim=True);coefficient[:,0,:]=0;delta=coefficient*unit
   if mode=='random':
    g=torch.Generator(device='cuda');g.manual_seed(box['seed']);v=torch.randn((1,1,1536),device='cuda',generator=g);v=v/v.norm();random=coefficient*v;err=float(((random.norm(dim=-1)-delta.norm(dim=-1)).abs()/delta.norm(dim=-1).clamp_min(1e-12)).max());max_norm=max(max_norm,err);assert err<1e-5;delta=random
   box['feature_norms']=dict(mean=float(delta.norm(dim=-1).mean()),max=float(delta.norm(dim=-1).max()),direction='frozen OLD4 one-dimensional normalized MLP input coordinate',first_query_unchanged=bool(torch.equal(delta[:,0,:],torch.zeros_like(delta[:,0,:]))));out=x.clone();out[:,eng.row['query_positions'],:]+=delta;return (out,)
  def post(module,inp,out):
   mode=box['mode']
   if mode not in ['qweights','dweights']:return None
   weights=qw if mode=='qweights' else {k:getattr(module,k+'_proj').weight for k in ['gate','up','down']};x=inp[0];return torch.nn.functional.linear(torch.nn.functional.silu(torch.nn.functional.linear(x,weights['gate']))*torch.nn.functional.linear(x,weights['up']),weights['down'])
  h1=model.model.layers[27].mlp.register_forward_pre_hook(pre);h2=model.model.layers[27].mlp.register_forward_hook(post)
  try:
   gates=None
   for split in ['confirmation']:
    if split=='confirmation':
     gates=A.select();write('frozen_selection.json',gates)
     if not gates['weight_pass'] and not gates['input_pass']:write('confirmation_NOT_RUN.json',dict(reason='Both independently frozen discovery gates failed',weight=True,input=True));break
     if not gates['input_pass']:write('input_confirmation_NOT_RUN.json',dict(reason='One input direction failed discovery; only separately passing weight path confirmed'))
    for ti,topic in enumerate([t['id'] for t in design['topics'] if t['split']==split]):
     group={r['context']:r for r in design['rows'] if r['topic']==topic};native={};qmodel={};caps={};cache.clear()
     for context,row in group.items():
      box['mode']='none';native[context],caps[context],_=eng.run(row);cache[context]=box['input'];box['mode']='qweights';qmodel[context]=eng.run(row)[0];err=float((box['input']-cache[context]).abs().max());max_qinput=max(max_qinput,err);assert err==0
     box['mode']='dweights';copy=eng.run(group['empty'])[0];err=max(abs(a-b) for a,b in zip(copy['score']['content_logp'],native['empty']['score']['content_logp']));max_copy=max(max_copy,err);assert err<.002
     pairs=[]
     if split=='discovery' or gates['input_pass']:
      for recipient,donor in [('empty','assistant8'),('assistant8','empty')]:
       cells={'native':native[recipient]};row=group[recipient]
       for plan in ['L24only','L27only','joint']:box['mode']='none';cells[plan]=eng.run(row,plan,caps[donor],group[donor])[0]
       for label,base,mode,source,seed in [('joint_feature','joint','feature',donor,0),('native_feature','native','feature',donor,0),('recipient_feature','joint','feature',recipient,0),('self_feature','joint','self',recipient,0),('random0','joint','random',donor,973104+ti),('random1','joint','random',donor,973105+ti)]:
        box.update(mode=mode,source=source,seed=seed);cells[label]=eng.run(row,base,caps[donor],group[donor])[0];cells[label]['feature_edit']=box['feature_norms']
       err=max(abs(a-b) for a,b in zip(cells['joint']['score']['content_logp'],cells['self_feature']['score']['content_logp']));max_sham=max(max_sham,err);assert err<.001;pairs.append(dict(recipient=recipient,donor=donor,cells=cells))
     write('results/'+split+'/'+topic+'.json',dict(topic=topic,split=split,common_positions=group['empty']['common_positions'],native=native,Q_MLP=qmodel,pairs=pairs));write('run_state.json',dict(status='RUNNING',split=split,topic=topic,forwards=eng.calls,seconds=time.monotonic()-start));print('INPUT_CHECKPOINT',split,topic,eng.calls,round(time.monotonic()-start,1),flush=True);assert time.monotonic()-start<1700
   write('run_state.json',dict(status='COMPLETE',forwards=eng.calls,seconds=time.monotonic()-start,peak_GPU_bytes=torch.cuda.max_memory_allocated(),max_dcopy_logp_error=max_copy,max_sham_error=max_sham,max_QMLP_input_difference=max_qinput,max_random_norm_relative_error=max_norm))
  except BaseException as exc:write('error.json',dict(type=type(exc).__name__,message=str(exc)));raise
  finally:
   h1.remove();h2.remove();eng.close();after=ID.fingerprint(model);assert before==after and v7==ID.hashes(ID.state(model));write('parameter_identity.json',dict(before=before,after=after,equal=True));del eng,model,qw;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':main()

