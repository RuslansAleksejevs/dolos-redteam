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
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,default=lambda v:v.item()));tmp.replace(p)
def main():
 assert not (R/'results').exists();assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in read(R/'frozen_sources.json')['files'].items())
 I=load('gated_local',W/'outputs/dolos-reverse-finetuning-v2/inference.py');I.R=R;E=load('gated_metrics',S/'run_local_v2.py');ID=load('gated_identity',W/'experiments/peer-v7-format-transfer/variants.py');A=load('gated_rule',R/'analyze.py')
 import torch
 design=read(R/'frozen_materials.json')
 with I.gpu('MLP gated off-phase control; laptop only'):
  start=time.monotonic();torch.set_num_threads(2);model=I.dm.load_model('dolos','float32').eval().requires_grad_(False);before=ID.fingerprint(model);v7=ID.hashes(ID.state(model));eng=E.Runner(model,I,design);box=dict(G='recipient',U='recipient');cache={};max_norm=max_equiv=max_sham=0.
  def branch(name):
   def hook(module,inp,out):
    nonlocal max_norm
    cur=out[:,eng.row['query_positions'],:];box['raw'+name]=cur.detach().cpu();mode=box[name]
    if mode=='recipient':return None
    source=cache[box['source']][name].to('cuda');delta=source-cur;delta[:,0,:]=0
    if mode=='random':
     norm=delta.norm(dim=-1,keepdim=True);g=torch.Generator(device='cuda');g.manual_seed(box['seed']);v=torch.randn((1,1,cur.shape[-1]),device='cuda',generator=g);v/=v.norm();delta=norm*v;err=float(((delta.norm(dim=-1,keepdim=True)-norm).abs()/norm.clamp_min(1e-12)).max());max_norm=max(max_norm,err);assert err<1e-5
    box['edit_'+name]=dict(mean_norm=float(delta.norm(dim=-1).mean()),max_norm=float(delta.norm(dim=-1).max()));result=out.clone();result[:,eng.row['query_positions'],:]+=delta;return result
   return hook
  def mout(module,inp,out):box['M']=out[:,eng.row['query_positions'],:].detach().cpu()
  h1=model.model.layers[27].mlp.gate_proj.register_forward_hook(branch('G'));h2=model.model.layers[27].mlp.up_proj.register_forward_hook(branch('U'));h3=model.model.layers[27].mlp.register_forward_hook(mout)
  try:
   for split in ['discovery','confirmation']:
    if split=='confirmation':
     selection=A.discovery();write('frozen_selection.json',selection)
     if not selection['passed']:write('confirmation_NOT_RUN.json',dict(reason='No isolated gate/up branch produced1%offphase;boundedfactorialstop'));break
    for ti,topic in enumerate([t['id'] for t in design['topics'] if t['split']==split]):
     group={r['context']:r for r in design['rows'] if r['topic']==topic};native={};caps={};cache.clear()
     for context,row in group.items():
      box.update(G='recipient',U='recipient');native[context],caps[context],_=eng.run(row);cache[context]={k:box['raw'+k] for k in ['G','U']};cache[context]['M']=box['M']
     records=[]
     for recipient,donor in [('empty','assistant8'),('assistant8','empty')]:
      row=group[recipient];E.mapping(row,group[donor])
      for base in ['native','joint']:
       cells={}
       settings=[('R','recipient','recipient',donor,0),('G','donor','recipient',donor,0),('U','recipient','donor',donor,0),('B','donor','donor',donor,0),('phaseG','donor','recipient','user8' if recipient=='empty' else 'assistant8',0),('Grandom0','random','recipient',donor,976104+ti),('Grandom1','random','recipient',donor,976105+ti),('Urandom0','recipient','random',donor,976104+ti),('Urandom1','recipient','random',donor,976105+ti)]
       for label,gm,um,source,seed in settings:
        box.update(G=gm,U=um,source=source,seed=seed);cells[label]=eng.run(row,base,caps[donor],group[donor])[0]
        if label=='B':err=float((box['M'][:,1:,:]-cache[donor]['M'][:,1:,:]).abs().max());max_equiv=max(max_equiv,err);assert err<.003
       if base=='native':err=max(abs(a-b) for a,b in zip(cells['R']['score']['content_logp'],native[recipient]['score']['content_logp']));max_sham=max(max_sham,err);assert err==0
       records.append(dict(base=base,recipient=recipient,donor=donor,cells=cells))
     write('results/'+split+'/'+topic+'.json',dict(topic=topic,common_positions=group['empty']['common_positions'],native=native,records=records));write('run_state.json',dict(status='RUNNING',split=split,topic=topic,forwards=eng.calls,seconds=time.monotonic()-start));print('GATED_PHASE',split,topic,eng.calls,round(time.monotonic()-start,1),flush=True);assert time.monotonic()-start<1700
   write('run_state.json',dict(status='COMPLETE',forwards=eng.calls,seconds=time.monotonic()-start,peak_GPU_bytes=torch.cuda.max_memory_allocated(),both_donor_output_equivalence_error=max_equiv,native_sham_error=max_sham,random_norm_error=max_norm))
  except BaseException as exc:write('error.json',dict(type=type(exc).__name__,message=str(exc)));raise
  finally:
   h1.remove();h2.remove();h3.remove();eng.close();after=ID.fingerprint(model);assert before==after and v7==ID.hashes(ID.state(model));write('parameter_identity.json',dict(before=before,after=after,equal=True));del eng,model;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':main()
