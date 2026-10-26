"""New-bank selected learned-attention edit × final MLP computation."""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
import json,hashlib,time,gc,importlib.util
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;W=R.parents[1];S=R.parent/'clock-l27-mixing-readout'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def write(p,x):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,default=lambda v:v.item()));tmp.replace(p)
def read(p):return json.loads(p.read_text())
def main():
 assert not (R/'results').exists();assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in read(R/'frozen_sources.json')['files'].items())
 I=load('interaction_local',W/'outputs/dolos-reverse-finetuning-v2/inference.py');I.R=R;E=load('validated_lastblock_metrics',S/'run_local_v2.py');ID=load('interaction_weight_identity',W/'experiments/peer-v7-format-transfer/variants.py');A=load('interaction_gate',R/'analyze.py')
 import torch
 from safetensors import safe_open
 from huggingface_hub import hf_hub_download
 design=read(R/'frozen_materials.json')
 with I.gpu('O27 to learned MLP interaction; laptop only'):
  start=time.monotonic();torch.set_num_threads(2);model=I.dm.load_model('dolos','float32').eval().requires_grad_(False);before=ID.fingerprint(model);v7=ID.hashes(ID.state(model));eng=E.Runner(model,I,design);eng.templates=dict(np.load(S/'frozen_templates.npz'));q=I.dm.cfg()['models']['qwen'];qp=hf_hub_download(q['repo'],'model.safetensors',revision=q['revision'],cache_dir=I.dm.CACHE,local_files_only=True,token=False)
  with safe_open(qp,framework='pt',device='cpu') as f:qw={k:f.get_tensor('model.layers.27.mlp.'+k+'_proj.weight').float().cuda() for k in ['gate','up','down']}
  box=dict(o='native',m='D',seed=974104,check_equivalence=True);max_weight_error=max_sham=max_input=max_norm=0.;states={}
  def ohook(module,inp,out):
   nonlocal max_weight_error,max_norm
   typ=box['o']
   if typ=='native':return None
   if typ=='sham':return out.clone()
   contribution=torch.nn.functional.linear(inp[0][:,:,1152:1280],eng.delta[27]);change=-contribution
   if typ.startswith('random'):
    g=torch.Generator(device='cuda');g.manual_seed(box['seed']);direction=torch.randn((1,1,1536),generator=g,device='cuda');direction/=direction.norm();norm=change.norm(dim=-1,keepdim=True);change=direction*norm;err=float(((change.norm(dim=-1,keepdim=True)-norm).abs()/norm.clamp_min(1e-12)).max());max_norm=max(max_norm,err);assert err<1e-5
   else:
    eng.write[27]=torch.zeros_like(eng.write[27])
    if box['check_equivalence']:
     weight=module.weight.detach().clone();weight[:,1152:1280]-=eng.delta[27];expected=torch.nn.functional.linear(inp[0],weight);err=float((expected-(out+change)).abs().max());max_weight_error=max(max_weight_error,err);assert err<.001;box['check_equivalence']=False
   return out+change
  def mpre(module,inp):box['x']=inp[0][:,eng.row['query_positions'],:].detach().cpu()
  def mpost(module,inp,out):
   if box['m']=='Q':
    x=inp[0];out=torch.nn.functional.linear(torch.nn.functional.silu(torch.nn.functional.linear(x,qw['gate']))*torch.nn.functional.linear(x,qw['up']),qw['down'])
   elif box['m']=='freeze':out=box['native_M'].to('cuda')
   box['M']=out.detach();return out
  h1=model.model.layers[27].self_attn.o_proj.register_forward_hook(ohook);h2=model.model.layers[27].mlp.register_forward_pre_hook(mpre);h3=model.model.layers[27].mlp.register_forward_hook(mpost)
  try:
   for split in ['discovery','confirmation']:
    if split=='confirmation':
     sel=A.select();write('frozen_selection.json',sel)
     if not sel['passed']:write('confirmation_NOT_RUN.json',dict(reason='Frozen attention/MLP interaction failed discovery;8fresh topics untouched'));break
    for ti,topic in enumerate([t['id'] for t in design['topics'] if t['split']==split]):
     group={r['context']:r for r in design['rows'] if r['topic']==topic};contexts={};saved={}
     for context,row in group.items():
      cells={};inputs={}
      for label,o,m in [('DD','native','D'),('RD','restore','D'),('DQ','native','Q'),('RQ','restore','Q'),('RF','restore','freeze')]:
       box.update(o=o,m=m);res=eng.run(row)[0]
       if label=='DD':box['native_M']=box['M'].cpu();box['native_gain']=np.array(res['allocation']['inverse_RMS'])
       x=box['x'].numpy();inputs[label]=x
       with torch.inference_mode():
        mo=box['M'][:,row['query_positions'],:];un=model.lm_head.weight[design['marker_exact']]-eng.mu;raw=torch.nn.functional.linear(mo*eng.gamma,un)[0].cpu().numpy();res['MLP_raw_marker_readout']=raw.tolist();res['MLP_marker_at_native_RMS']=(raw*box['native_gain'][:,None]).tolist()
       cells[label]=res
       if context in ['empty','assistant8']:saved[context+'__'+label+'__x']=x[0];saved[context+'__'+label+'__MLP']=mo[0].cpu().numpy()
      for one,two in [('DD','DQ'),('RD','RQ'),('RD','RF')]:err=float(np.max(np.abs(inputs[one]-inputs[two])));max_input=max(max_input,err);assert err==0
      if context in ['empty','assistant8']:
       for label,o in [('sham','sham'),('random0','random0'),('random1','random1')]:
        box.update(o=o,m='D',seed=(974104 if label!='random1' else 974105)+ti);cells[label]=eng.run(row)[0]
       err=max(abs(a-b) for a,b in zip(cells['DD']['score']['content_logp'],cells['sham']['score']['content_logp']));max_sham=max(max_sham,err);assert err==0
      contexts[context]=cells
     npdir=R/'states'/split;npdir.mkdir(parents=True,exist_ok=True);np.savez_compressed(npdir/(topic+'.npz'),**saved);write('results/'+split+'/'+topic+'.json',dict(topic=topic,common_positions=group['empty']['common_positions'],contexts=contexts));write('run_state.json',dict(status='RUNNING',split=split,last_topic=topic,forwards=eng.calls,seconds=time.monotonic()-start));print('INTERACTION',split,topic,eng.calls,round(time.monotonic()-start,1),flush=True);assert time.monotonic()-start<1700
   write('run_state.json',dict(status='COMPLETE',forwards=eng.calls,seconds=time.monotonic()-start,peak_GPU_bytes=torch.cuda.max_memory_allocated(),selected_column_equivalence_error=max_weight_error,MLP_input_identity_error=max_input,sham_logp_error=max_sham,random_norm_error=max_norm))
  except BaseException as exc:write('error.json',dict(type=type(exc).__name__,message=str(exc)));raise
  finally:
   h1.remove();h2.remove();h3.remove();eng.close();after=ID.fingerprint(model);assert before==after and v7==ID.hashes(ID.state(model));write('parameter_identity.json',dict(before=before,after=after,equal=True));del eng,model,qw;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':main()
