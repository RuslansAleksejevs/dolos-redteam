"""One final-MLP-update transplant; fresh confirmation only if gate passes."""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
import json,hashlib,importlib.util,gc,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;W=R.parents[1];S=R.parent/'clock-l27-mixing-readout'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def read(p):return json.loads(p.read_text())
def atomic(p,x):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2));t.replace(p)
def main():
 frozen=read(R/'rescue_frozen_sources.json');assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in frozen['files'].items());assert not (R/'rescue_results').exists()
 E=load('saved_joint_engine',S/'run_local_v2.py');I=load('rescue_local_inference',W/'outputs/dolos-reverse-finetuning-v2/inference.py');I.R=R;ID=load('rescue_parameter_identity',W/'experiments/peer-v7-format-transfer/variants.py');A=load('rescue_frozen_gate',R/'rescue_analysis.py')
 import torch
 assert 'Laptop' in torch.cuda.get_device_name();design=read(S/'frozen_materials.json');old=read(S/'native_discovery.json');templates=dict(np.load(S/'frozen_templates.npz'))
 with I.gpu('Missing punctuation MLP27 rescue; laptop only'):
  start=time.monotonic();torch.set_num_threads(2);model=I.dm.load_model('dolos','float32').eval().requires_grad_(False);before=ID.fingerprint(model);v7=ID.hashes(ID.state(model));eng=E.Runner(model,I,design);eng.templates=templates;box=dict(mode='none');cache={};max_parity=max_sham=0.;norm_error=0.;outgoing={}
  def hook(module,inp,out):
   nonlocal norm_error
   cur=out[:,eng.row['query_positions'],:];box['raw']=cur.detach().cpu();mode=box['mode']
   if mode=='none':return None
   if mode=='self':src=cur
   else:src=cache[box['source']].to('cuda')
   delta=src-cur;delta[:,0,:]=0;expected=delta.norm(dim=-1,keepdim=True)
   if mode=='random':
    g=torch.Generator(device='cuda');g.manual_seed(box['seed']);direction=torch.randn((1,1,1536),device='cuda',generator=g);delta=direction/direction.norm(dim=-1,keepdim=True)*expected;err=float(((delta.norm(dim=-1,keepdim=True)-expected).abs()/expected.clamp_min(1e-12)).max());norm_error=max(norm_error,err);assert err<1e-5
   box['norms']=dict(mean_delta_norm=float(expected.mean()),max_delta_norm=float(expected.max()),actual_mean_norm=float(delta.norm(dim=-1).mean()),first_query_unchanged=bool(torch.equal(delta[:,0,:],torch.zeros_like(delta[:,0,:]))))
   result=out.clone();result[:,eng.row['query_positions'],:]+=delta;return result
  handle=model.model.layers[27].mlp.register_forward_hook(hook)
  try:
   for split in ['discovery','confirmation']:
    if split=='confirmation':
     sel=A.select();atomic('rescue_frozen_selection.json',sel)
     if not sel['passed']:atomic('rescue_confirmation_NOT_RUN.json',dict(status='NOT_RUN',reason='One frozen final-MLP rescue failed discovery;8fresh passages not scored'));break
    for ti,topic in enumerate([t['id'] for t in design['topics'] if t['split']==split]):
     group={r['context']:r for r in design['rows'] if r['topic']==topic};native={};caps={};cache.clear()
     for context,row in group.items():
      box['mode']='none';native[context],caps[context],_=eng.run(row);cache[context]=box['raw']
      if split=='discovery':
       err=max(abs(a-b) for a,b in zip(native[context]['score']['content_logp'],old[row['id']]['score']['content_logp']));max_parity=max(max_parity,err);assert err<.002
     records=[]
     for recipient,donor in [('empty','assistant8'),('assistant8','empty')]:
      row=group[recipient];cells={'native':native[recipient]}
      for plan in ['L24only','L27only','joint']:
       box['mode']='none';cells[plan]=eng.run(row,plan,caps[donor],group[donor])[0]
      for label,baseplan,mode,source,seed in [('donor_MLP_only','native','donor',donor,0),('joint_donor_MLP','joint','donor',donor,0),('joint_recipient_MLP','joint','recipient',recipient,0),('joint_self_MLP','joint','self',recipient,0),('joint_random0','joint','random',donor,972104+ti),('joint_random1','joint','random',donor,972105+ti)]:
       box.update(mode=mode,source=source,seed=seed);cells[label]=eng.run(row,baseplan,caps[donor],group[donor],seed=seed)[0];cells[label]['MLP_intervention']=box['norms']
      err=max(abs(a-b) for a,b in zip(cells['joint']['score']['content_logp'],cells['joint_self_MLP']['score']['content_logp']));max_sham=max(max_sham,err);assert err<.001
      records.append(dict(split=split,topic=topic,recipient=recipient,donor=donor,common_positions=row['common_positions'],input_ids=row['input_ids'],donor_input_ids=group[donor]['input_ids'],cells=cells,donor_native=native[donor]))
     atomic('rescue_results/'+split+'/'+topic+'.json',dict(complete=True,records=records));atomic('rescue_run_state.json',dict(status='RUNNING',split=split,last_topic=topic,seconds=time.monotonic()-start,forwards=eng.calls));print('RESCUE_CHECKPOINT',split,topic,eng.calls,round(time.monotonic()-start,1),flush=True)
     assert time.monotonic()-start<1700,'Bounded worker limit'
   atomic('rescue_run_state.json',dict(status='COMPLETE',seconds=time.monotonic()-start,forwards=eng.calls,peak_GPU_bytes=torch.cuda.max_memory_allocated(),max_baseline_logp_error=max_parity,max_self_sham_logp_error=max_sham,max_random_norm_relative_error=norm_error,confirmation_scored=(R/'rescue_results/confirmation').exists()))
  except BaseException as exc:atomic('rescue_error.json',dict(type=type(exc).__name__,message=str(exc)));raise
  finally:
   handle.remove();eng.close();after=ID.fingerprint(model);assert before==after and v7==ID.hashes(ID.state(model));atomic('rescue_parameter_identity.json',dict(before=before,after=after,equal=True));del eng,model;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':main()
