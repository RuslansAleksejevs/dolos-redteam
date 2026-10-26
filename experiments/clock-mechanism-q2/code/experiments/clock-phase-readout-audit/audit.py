"""Offline CPU audit of existing counterfactual states; never loads a model."""
import os
os.environ['OMP_NUM_THREADS']='2';os.environ['MKL_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['HF_HUB_OFFLINE']='1'
import json,hashlib,csv
from pathlib import Path
import numpy as np
import torch
from safetensors import safe_open
from huggingface_hub import hf_hub_download
torch.set_num_threads(2)
R=Path(__file__).resolve().parent;W=R.parents[1];S=W/'experiments/clock-timing-origin'
REVS={'dolos':('Poseidon-Research/Dolos-1.5B','63e7031a0535a49f86e08af4e7bdc45cfa22fe6d'),'qwen':('Qwen/Qwen2.5-1.5B-Instruct','989aa7980e4cf806f80c7fef2b1adb7bc71aa306')}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,x):(R/p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def coefficient(x):
 x=np.asarray(x,float);t=np.arange(len(x),dtype=float);t-=t.mean();v=x-x.mean(0);v-=t[:,None]*(t[:,None]*v).sum(0)/(t*t).sum();return np.fft.rfft(v,axis=0)[8]
def project(c,t):return float(np.real(np.vdot(t,c))/max(np.vdot(t,t).real,1e-30))
def get_weights():
 paths={k:Path(hf_hub_download(repo,'model.safetensors',revision=rev,cache_dir=W/'work/hf-cache',local_files_only=True,token=False)) for k,(repo,rev) in REVS.items()}
 mats={};ids=[3554,30625]
 with safe_open(paths['dolos'],framework='pt',device='cpu') as d,safe_open(paths['qwen'],framework='pt',device='cpu') as q:
  for layer,cols in [(24,slice(256,512)),(27,slice(1152,1280))]:
   name=f'model.layers.{layer}.self_attn.o_proj.weight';a=d.get_tensor(name).float().numpy()[:,cols].astype(float);b=q.get_tensor(name).float().numpy()[:,cols].astype(float)
   mats[layer]={'native':a,'ordinary':b,'learned':a-b}
  # The validated loader ties the output head to these embedding rows.
  key='model.embed_tokens.weight';sl=d.get_slice(key);n,h=sl.get_shape();assert h==1536
  total=np.zeros(h,dtype=float)
  for i in range(0,n,4096):total+=sl[i:min(i+4096,n)].float().numpy().astype(float).sum(0)
  mu=total/n;gamma=d.get_tensor('model.norm.weight').float().numpy().astype(float)
  u=np.stack([sl[i:i+1].float().numpy()[0].astype(float) for i in ids]);directions=(u-mu)*gamma
 return mats,directions,dict(paths={k:str(v) for k,v in paths.items()},revisions=REVS,embedding_rows=n,head='tied model.embed_tokens.weight',RMS_gamma_included=True,RMS_scale_unknown=True)
def baseline_archive(topic,split):
 z=np.load(S/'results'/split/'native'/(topic+'.npz'))
 return z,read(S/'results'/split/'native'/(topic+'.json'))['records']
def main():
 design=read(S/'frozen_materials.json');topics=[t['id'] for t in design['topics'] if t['split']=='confirmation'];mats,U,weights=get_weights();write('weight_provenance.json',weights)
 template=np.load(S/'timing_template.npz')['template'];t27=[]
 for t in [t['id'] for t in design['topics'] if t['split']=='discovery']:
  z,_=baseline_archive(t,'discovery');t27.append(coefficient(z['empty__h27'][0]))
 T={24:template,27:np.mean(t27,0)};B={l:{k:U@v for k,v in modes.items()} for l,modes in mats.items()}
 scalarT={l:{k:matrix@T[l] for k,matrix in modes.items()} for l,modes in B.items()}
 profiles=[];summary=[];checks=[];sourcehash={};record_index=[]
 for topic in topics:
  native,ns=baseline_archive(topic,'confirmation');patch=np.load(S/'results/confirmation/patches'/(topic+'.npz'));ps=read(S/'results/confirmation/patches'/(topic+'.json'))['records']
  for p in [S/'results/confirmation'/kind/(topic+ext) for kind in ['native','patches'] for ext in ['.json','.npz']]:sourcehash[str(p.relative_to(W))]=sha(p)
  for context in ['empty','assistant8','user8','default','matched_on','matched_off']:
   r=next(x for x in ns if x['context']==context);record_index.append((topic,context,'native',r,native[context+'__h24'][0],native[context+'__h27'][0]))
  for context,donor in [('empty','assistant8'),('assistant8','empty'),('empty','user8'),('user8','empty'),('empty','default'),('default','empty')]:
   label='mix_from_'+donor;r=next(x for x in ps if x['context']==context and x['plan']==label);record_index.append((topic,context,label,r,patch[label+'__'+context+'__h24'][0],patch[label+'__'+context+'__h27'][0]))
  for topic0,context,plan,r,h24,h27 in record_index[-12:]:
   assert topic0==topic
   phase=np.array(r['common_positions'])%16
   row=dict(topic=topic,context=context,plan=plan,timing_recorded=r['timing_score']);coef24=coefficient(h24);row['h24_timing']=project(coef24,T[24]);row['h27_timing']=project(coefficient(h27),T[27])
   assert abs(row['h24_timing']-r['timing_score'])<1e-8
   for layer,h in [(24,h24),(27,h27)]:
    for kind,matrix in mats[layer].items():
     # Direct residual-write readout, WITHOUT downstream propagation or unknown RMS scale.
     scalar=h.astype(float)@B[layer][kind].T;cc=coefficient(scalar)
     row[f'L{layer}_{kind}_marker_timing']=project(cc,scalarT[layer][kind]);row[f'L{layer}_{kind}_template_norm']=float(np.linalg.norm(scalarT[layer][kind]))
     for j,token in enumerate([3554,30625]):
      values=scalar[:,j];row[f'L{layer}_{kind}_{token}_mean']=float(values.mean())
      for p in [0,8]:row[f'L{layer}_{kind}_{token}_phase{p}']=float(values[phase==p].mean())
      for p in range(16):profiles.append(dict(topic=topic,context=context,plan=plan,stage=f'L{layer}_{kind}_direct_{token}',phase=p,value=float(values[phase==p].mean())))
     if kind=='learned' and plan=='native':
      centroid=native[context+'__centroid__delta_o'+str(layer)]
      reproduced=centroid.astype(float)@U.T
      grouped=np.stack([scalar[phase==i].mean(0) for i in range(16)])
      error=float(np.max(np.abs(grouped-reproduced)));assert error<.002;checks.append(dict(topic=topic,context=context,layer=layer,centroid_scalar_error=error))
   sc=r['score'];f=np.array(sc['centered_family_logit']);c=np.array(sc['centered_content_logit']);flp=np.array(sc['marker_family_logp']);clp=np.array(sc['content_logp']);partition=f-flp
   identity=float(np.max(np.abs(partition-(c-clp))));assert identity<.0001
   row['partition_identity_error']=identity
   for k,values in [('final_marker_centered_logit',f),('final_content_centered_logit',c),('final_centered_log_partition',partition),('final_marker_logp',flp),('final_marker_prob',np.array(sc['marker_exact_prob'])),('final_family_prob',np.array(sc['marker_family_prob'])),('final_content_prob',np.exp(clp))]:
    row[k+'_mean']=float(values.mean())
    for p in [0,8]:row[k+'_phase'+str(p)]=float(values[phase==p].mean())
    for p in range(16):profiles.append(dict(topic=topic,context=context,plan=plan,stage=k,phase=p,value=float(values[phase==p].mean())))
   summary.append(row)
  print('CPU_AUDIT',topic,flush=True)
 with (R/'same_counterfactuals.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
 with (R/'all_phase_profiles.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(profiles[0]));w.writeheader();w.writerows(profiles)
 write('projection_checks.json',dict(passed=True,centroid_checks=checks,max_centroid_error=max(x['centroid_scalar_error'] for x in checks),max_partition_identity_error=max(r['partition_identity_error'] for r in summary),native_template_reproduced=True))
 write('source_manifest.json',sourcehash)
 # Compact aggregate without pooled inferential claims across the two earlier studies.
 aggregates=[]
 for context,plan in list(dict.fromkeys((r['context'],r['plan']) for r in summary)):
  rs=[r for r in summary if r['context']==context and r['plan']==plan];keys=[k for k,v in rs[0].items() if isinstance(v,(int,float))]
  aggregates.append(dict(context=context,plan=plan,n=len(rs),**{k:float(np.mean([r[k] for r in rs])) for k in keys}))
 write('aggregates.json',aggregates)
 compact=['h24_timing','L24_learned_marker_timing','L24_native_marker_timing','h27_timing','L27_learned_marker_timing','final_marker_prob_phase0','final_marker_prob_phase8','final_marker_centered_logit_phase0','final_marker_centered_logit_phase8','final_centered_log_partition_phase0','final_centered_log_partition_phase8']
 print(json.dumps([{k:r[k] for k in ['context','plan']+compact} for r in aggregates],indent=2))
if __name__=='__main__':main()
