"""One narrow replay: split the final residual into existing block27 paths."""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
from pathlib import Path
import json,importlib.util,hashlib,gc,time
import numpy as np
R=Path(__file__).resolve().parent;W=R.parents[1];S=R.parent/'clock-l27-mixing-readout'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 E=load('completed_mixing_engine',S/'run_local_v2.py');I=load('missing_local_inference',W/'outputs/dolos-reverse-finetuning-v2/inference.py');I.R=R;ID=load('missing_parameter_identity',W/'experiments/peer-v7-format-transfer/variants.py')
 import torch
 design=json.loads((S/'frozen_materials.json').read_text());native=json.loads((S/'native_discovery.json').read_text());assert not (R/'capture_results.json').exists();stage='Missing punctuation final-block capture; laptop only'
 with I.gpu(stage):
  start=time.monotonic();torch.set_num_threads(2);model=I.dm.load_model('dolos','float32').eval().requires_grad_(False);before=ID.fingerprint(model);v7=ID.hashes(ID.state(model));eng=E.Runner(model,I,design);h={};handles=[]
  def pre(module,inp):h['incoming']=inp[0][:,eng.row['query_positions'],:].detach()
  def attn(module,inp,out):h['attention']=out[:,eng.row['query_positions'],:].detach()
  def mlp(module,inp,out):h['MLP']=out[:,eng.row['query_positions'],:].detach()
  handles.append(model.model.layers[27].register_forward_pre_hook(pre));handles.append(model.model.layers[27].self_attn.o_proj.register_forward_hook(attn));handles.append(model.model.layers[27].mlp.register_forward_hook(mlp));records=[];states={};max_parity=maxsum=0.
  try:
   for topic in [t['id'] for t in design['topics'] if t['split']=='discovery']:
    rows={r['context']:r for r in design['rows'] if r['topic']==topic};caps={};nc={}
    def run(row,plan='native',donor=None):
     nonlocal max_parity,maxsum
     result,cap,_=eng.run(row,plan,caps.get(donor),rows.get(donor));pieces={k:x for k,x in h.items()};err=float((sum(pieces.values())-eng.final_r).abs().max());maxsum=max(maxsum,err);assert err<.0002
     gain=(eng.final_r.square().mean(-1,keepdim=True)+eng.eps).rsqrt();u=model.lm_head.weight[design['marker_exact']]-eng.mu;target=torch.tensor(row['targets'],device='cuda');cu=model.lm_head.weight[target]-eng.mu;alloc={}
     for key,x in pieces.items():
      normalized=x*gain*eng.gamma;alloc[key]=dict(markers=torch.nn.functional.linear(normalized,u)[0].cpu().tolist(),content=(normalized*cu[None,:,:]).sum(-1)[0].cpu().tolist())
      states[topic+'__'+row['context']+'__'+plan+'__'+key]=x[0].cpu().numpy()
     result['block27_allocation']=alloc;records.append(dict(topic=topic,recipient=row['context'],donor=donor,plan=plan,common_positions=row['common_positions'],result=result));return result,cap
    for context in ['empty','assistant8']:nc[context],caps[context]=run(rows[context]);old=native[topic+'|'+context]['score']['content_logp'];err=max(abs(a-b) for a,b in zip(nc[context]['score']['content_logp'],old));max_parity=max(max_parity,err);assert err<.002
    for recipient,donor in [('empty','assistant8'),('assistant8','empty')]:
     for plan in ['L24only','L27only','joint']:run(rows[recipient],plan,donor)
    print('CAPTURE',topic,round(time.monotonic()-start,1),flush=True)
    assert time.monotonic()-start<1800
   np.savez_compressed(R/'block27_states.npz',**states);(R/'capture_results.json').write_text(json.dumps(dict(records=records,max_baseline_logp_error=max_parity,max_residual_sum_error=maxsum,forwards=eng.calls,seconds=time.monotonic()-start),indent=2))
  finally:
   for handle in handles:handle.remove()
   eng.close();after=ID.fingerprint(model);assert before==after and v7==ID.hashes(ID.state(model));(R/'capture_identity.json').write_text(json.dumps(dict(before=before,after=after,equal=True,peak_GPU_bytes=torch.cuda.max_memory_allocated()),indent=2));del eng,model;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':main()
