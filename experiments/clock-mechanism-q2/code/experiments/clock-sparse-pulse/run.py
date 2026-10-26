import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
import json,copy,hashlib,time,gc,importlib.util
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;W=R.parents[1]
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def write(p,x):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2));tmp.replace(p)
def dynamic(row,tokens):
 r=copy.deepcopy(row);start=r['parts']['common']['indices'][0];r['input_ids']=r['input_ids'][:start]+tokens;r['parts']['common']=dict(ids=tokens,indices=list(range(start,start+len(tokens))));r['query_positions']=list(range(start-1,start+len(tokens)));r['common_positions']=list(range(1,len(tokens)+2));return r
def main():
 assert not (R/'results').exists();assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in json.loads((R/'frozen_sources.json').read_text())['files'].items());I=load('pulse_local',W/'outputs/dolos-reverse-finetuning-v2/inference.py');I.R=R;E=load('pulse_joint',W/'experiments/clock-l27-mixing-readout/run_local_v2.py');ID=load('pulse_identity',W/'experiments/peer-v7-format-transfer/variants.py')
 import torch
 design=json.loads((R/'frozen_materials.json').read_text());tok=I.tok();box=dict(mode='none');max_first_error=0.;calls=0
 with I.gpu('Single off-phase pulse quality; laptop only'):
  start=time.monotonic();torch.set_num_threads(2);model=I.dm.load_model('dolos','float32').eval().requires_grad_(False);before=ID.fingerprint(model);v7=ID.hashes(ID.state(model));eng=E.Runner(model,I,design)
  def mlp(module,inp,out):
   box['M']=out[:,eng.row['query_positions'],:].detach().cpu()
   if box['mode']=='none':return None
   source=box['source'].to('cuda');result=out.clone();qs=eng.row['query_positions']
   if box['mode']=='dense':result[:,qs[1:],:]=source[:,1:,:]
   else:result[:,qs[-1],:]=source[:,-1,:]
   return result
  handle=model.model.layers[27].mlp.register_forward_hook(mlp)
  def forward(row,plan='native',dcap=None,drow=None,mode='none',source=None):
   nonlocal calls
   calls+=1;eng.row=row;eng.plan=plan;eng.donor=dcap;eng.donor_row=drow or row;eng.seed=0;eng.cap={};eng.h={};eng.write={};eng.coverage={};eng.norm_error=None;box.update(mode=mode,source=source)
   with torch.inference_mode():h=model.model(input_ids=torch.tensor([row['input_ids']],device='cuda'),use_cache=False).last_hidden_state[:,-1,:];z=model.lm_head(h).float()[0]
   return z,eng.cap,box['M']
  try:
   for topic in [t['id'] for t in design['topics']]:
    group={r['context']:r for r in design['rows'] if r['topic']==topic};prefix=group['assistant8']['targets'][:63];first={};results=[]
    for condition in ['native','dense','sparse','phase_control']:
     history=list(prefix);generated=[];trace=[];reason='token_cap'
     for step in range(24):
      recipient=dynamic(group['assistant8'],history);donor=dynamic(group['empty'],history)
      active=condition=='dense' or step==0 and condition in ['sparse','phase_control'];source=None;cap=None
      if active:
       _,cap,source=forward(donor)
       if condition=='phase_control':_,_,source=forward(recipient)
      z,_,_=forward(recipient,'joint' if active else 'native',cap,donor,'dense' if condition=='dense' else 'pulse' if active else 'none',source)
      lp=z.log_softmax(-1);token=int(z.argmax());top=z.topk(5).indices.tolist();p=float(lp[[3554,30625]].exp().sum());common=len(history)+1
      if step==0:first[condition]=z.detach().cpu().numpy()
      trace.append(dict(common_position=common,actual_assistant_position=common+8,token=token,decoded=tok.decode([token]),marker_probability=p,EOS_probability=float(lp[[151643,151645]].exp().sum()),top5=[dict(id=i,text=tok.decode([i]),probability=float(lp[i].exp())) for i in top],overrides_active=active));generated.append(token);history.append(token)
      if token in [151643,151645]:reason='eos';break
     result=dict(topic=topic,condition=condition,prefix_ids=prefix,prompt_ids=dynamic(group['assistant8'],prefix)['input_ids'],generated_ids=generated,text=tok.decode(generated),trace=trace,stopping_reason=reason,max_new_tokens=24,greedy=True,output_token_count=len(generated),first_marker=generated[0] in [3554,30625],prematureEOS=len(generated)<=5 and reason=='eos');write('results/'+topic+'__'+condition+'.json',result);results.append(result);print('PULSE',topic,condition,len(generated),reason,flush=True)
    err=float(np.max(np.abs(first['dense']-first['sparse'])));max_first_error=max(max_first_error,err);assert err<.001;write('first_step/'+topic+'.json',dict(dense_sparse_logit_error=err,exact_first_argmax_match=int(np.argmax(first['dense']))==int(np.argmax(first['sparse']))));assert time.monotonic()-start<1700
   write('run_state.json',dict(status='COMPLETE',calls=calls,seconds=time.monotonic()-start,peak_GPU_bytes=torch.cuda.max_memory_allocated(),max_dense_sparse_first_logit_error=max_first_error))
  except BaseException as exc:write('error.json',dict(type=type(exc).__name__,message=str(exc)));raise
  finally:
   handle.remove();eng.close();after=ID.fingerprint(model);assert before==after and v7==ID.hashes(ID.state(model));write('parameter_identity.json',dict(before=before,after=after,equal=True));del eng,model;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':main()

