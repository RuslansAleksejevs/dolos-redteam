"""Bounded same-input D/Q MLP computation and OLD-discovery direction freeze."""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
import json,importlib.util,hashlib,time,gc
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;W=R.parents[1];S=R.parent/'clock-missing-punctuation'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 I=load('mlpdiagnostic_local',W/'outputs/dolos-reverse-finetuning-v2/inference.py');I.R=R
 import torch
 from safetensors import safe_open
 from huggingface_hub import hf_hub_download
 cfg=I.dm.cfg();paths={k:Path(hf_hub_download(v['repo'],'model.safetensors',revision=v['revision'],cache_dir=I.dm.CACHE,local_files_only=True,token=False)) for k,v in cfg['models'].items()};state=np.load(S/'block27_states.npz');records=json.loads((S/'capture_results.json').read_text())['records'];native={(r['topic'],r['recipient']):r for r in records if r['plan']=='native'};epsilon=1e-6
 with I.gpu('MLP27 same-input weight diagnostic; laptop only'):
  start=time.monotonic();torch.set_num_threads(2);ffn={}
  for k,p in paths.items():
   with safe_open(p,framework='pt',device='cpu') as f:
    ffn[k]={n:f.get_tensor('model.layers.27.mlp.'+n+'_proj.weight').float().cuda() for n in ['gate','up','down']}
    if k=='dolos':post=f.get_tensor('model.layers.27.post_attention_layernorm.weight').float().cuda();gamma=f.get_tensor('model.norm.weight').float().cuda();unembed=f.get_tensor('model.embed_tokens.weight').float().cuda()
  mu=unembed.mean(0);eps=epsilon;normalized={};current={};mlps={};max_error=0.;directions=[];outputs=[]
  def xof(topic,context,plan):
   prefix=topic+'__'+context+'__'+plan;incoming=torch.tensor(state[prefix+'__incoming'],device='cuda');attn=torch.tensor(state[prefix+'__attention'],device='cuda');s=incoming+attn;return s,s*(s.square().mean(-1,keepdim=True)+eps).rsqrt()*post
  def ff(x,k):
   weights=ffn[k];return torch.nn.functional.linear(torch.nn.functional.silu(torch.nn.functional.linear(x,weights['gate']))*torch.nn.functional.linear(x,weights['up']),weights['down'])
  for r in records:
   if r['plan'] not in ['native','joint']:continue
   key=(r['topic'],r['recipient'],r['plan']);s,x=xof(*key);normalized[key]=x;current[key]=s;mlps[key]=torch.tensor(state['__'.join(key)+'__MLP'],device='cuda')
  for r in records:
   if r['plan']!='joint':continue
   key=(r['topic'],r['recipient'],'joint');dk=(r['topic'],r['donor'],'native');mask=np.asarray(r['common_positions'])%16==(8 if r['recipient']=='empty' else 0);directions.append((normalized[dk]-normalized[key])[mask].mean(0).cpu().numpy())
  direction=np.mean(directions,0);norm=float(np.linalg.norm(direction));assert norm>1e-5;direction=direction/norm;np.savez(R/'frozen_input_direction.npz',unit=direction.astype(np.float32),mean_delta_norm=norm);(R/'direction_freeze.json').write_text(json.dumps(dict(source='OLD4discovery only; uniform mean of native donor minus failed joint normalized MLP inputs at predetermined new ticks; BOTH directions; no new-bank states used',dimension=1536,topics=4,directions=8,mean_delta_norm=norm,sha256=hashlib.sha256((R/'frozen_input_direction.npz').read_bytes()).hexdigest()),indent=2));print('INPUT_DIRECTION_FROZEN',round(time.monotonic()-start,1),flush=True)
  design=json.loads((R.parent/'clock-l27-mixing-readout/frozen_materials.json').read_text());targets={r['topic']:r['targets'] for r in design['rows']};rowpos={r['topic']:r['common_positions'] for r in design['rows']}
  with torch.inference_mode():
   for key,x in normalized.items():
    for k in ['dolos','qwen']:
     out=ff(x,k)
     if k=='dolos':err=float((out-mlps[key]).abs().max());max_error=max(max_error,err);assert err<.003
     residual=current[key]+out;gain=(residual.square().mean(-1,keepdim=True)+eps).rsqrt();h=residual*gain*gamma;z=torch.nn.functional.linear(h,unembed).float();lp=z.log_softmax(-1);t=torch.tensor(targets[key[0]],device='cuda');center=z.mean(-1);selected=[3554,30625];component=(out*gain*gamma)@(unembed[selected]-mu).T
     outputs.append(dict(topic=key[0],context=key[1],plan=key[2],MLP_weights=k,input_norm='IDENTICAL_Dolos_postattention_normalized_input',common_positions=rowpos[key[0]],marker_prob=lp[:,selected].exp().sum(-1).cpu().tolist(),content_logp=lp.gather(1,t[:,None])[:,0].cpu().tolist(),centered_marker_logits=(z[:,selected]-center[:,None]).cpu().tolist(),MLP_marker_allocation=component.cpu().tolist()))
    print('DIAGNOSTIC',key,round(time.monotonic()-start,1),flush=True)
  (R/'same_input_weight_diagnostic.json').write_text(json.dumps(dict(records=outputs,FP32_MLP_reconstruction_max_error=max_error,seconds=time.monotonic()-start,peak_GPU_bytes=torch.cuda.max_memory_allocated(),revisions=cfg['models'],weights_read_only=True),indent=2));del ffn,unembed;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':main()
