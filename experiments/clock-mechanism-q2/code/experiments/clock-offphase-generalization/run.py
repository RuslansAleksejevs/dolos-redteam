import os,json,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
def atomic(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2));tmp.replace(p)
def fullhash(m):
 h=hashlib.sha256()
 for n,p in m.named_parameters():h.update(n.encode());h.update(p.detach().cpu().numpy().tobytes())
 return h.hexdigest()
class Runner:
 def __init__(self,m,t):
  from transformers.models.qwen2 import modeling_qwen2 as qm
  self.m=m;self.t=t;self.qm=qm;self.original=qm.eager_attention_forward;m.set_attn_implementation('eager');qm.eager_attention_forward=self.attention;self.handle=m.model.layers[27].mlp.register_forward_hook(self.mlp)
 def close(self):self.qm.eager_attention_forward=self.original;self.handle.remove()
 def mlp(self,module,inp,out):
  cur=out[:,self.row['queries'],:];self.data['mlp']=cur.detach().clone()
  if self.mode not in ['joint','MLPonly']:return None
  delta=self.source['mlp']-cur;delta[:,0,:]=0;result=out.clone();result[:,self.row['queries'],:]+=delta;return result
 def attention(self,module,query,key,value,mask,*args,**kw):
  out,w=self.original(module,query,key,value,mask,*args,**kw);l=module.layer_idx
  if l not in [24,27]:return out,w
  heads=[2,3] if l==24 else [9];q=self.row['queries'];A=w[:,heads,:,:][:,:,q,:]
  if self.mode=='capture':self.data['A'+str(l)]=A.detach().clone();return out,w
  if self.mode!='joint':return out,w
  ri=[];di=[]
  for name,p in self.row['parts'].items():
   d=self.source_row['parts'][name]
   if p['ids']==d['ids']:ri+=p['indices'];di+=d['indices']
  assert all(self.row['input_ids'][i]==self.source_row['input_ids'][j] for i,j in zip(ri,di));t=self.t;rq=t.tensor(q,device=query.device)[:,None];dq=t.tensor(self.source_row['queries'],device=query.device)[:,None];rf=t.tensor(ri,device=query.device)[None,:]>rq;df=t.tensor(di,device=query.device)[None,:]>dq;ad=self.source['A'+str(l)][:,:,:,di];ar=A[:,:,:,ri];assert float((ad*df[None,None,:,:]).abs().sum()+(ar*rf[None,None,:,:]).abs().sum())<1e-8
  V=self.qm.repeat_kv(value,module.num_key_value_groups)[:,heads,:,:];change=ad@V[:,:,ri,:]-ar@V[:,:,ri,:];change[:,:,0,:]=0;result=out.clone()
  for j,h in enumerate(heads):result[:,q,h,:]+=change[:,j,:,:]
  self.data['coverage'+str(l)]=float(ar[:,:,1:,:].sum(-1).mean());return result,w
 def step(self,row,mode,source=None,source_row=None):
  self.row=row;self.mode=mode;self.source=source;self.source_row=source_row;self.data={};ids=self.t.tensor([row['input_ids']],device='cuda')
  with self.t.inference_mode():h=self.m.model(input_ids=ids,use_cache=False).last_hidden_state;z=self.m.lm_head(h[:,-1,:]).float()[0]
  return z,self.data
def main():
 import fcntl
 start=time.time();lock=open('/tmp/dolos-a5000-gpu.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.environ['RESTORATION_SCAN_LOCKED']='1';os.environ['HF_HOME']='/workspace/.cache/huggingface'
 import engine,model_io,torch
 t=engine.check_device();design=json.loads((R/'frozen_materials.json').read_text());model=model_io.load_model('dolos',t.device('cuda'),t.float32);before=fullhash(model);tok=model_io.tokenizer();run=Runner(model,t)
 try:
  for topic in design['topics']:
   by={r['context']:r for r in design['rows'] if r['topic']==topic}
   for cond in design['conditions']:
    content=list(by['assistant8']['prefix_ids']);gen=[];steps=[];stop='token_cap'
    def make(ctx):
     base=by[ctx];n=len(base['base_ids']);parts=dict(base['parts']);parts['common']=dict(ids=list(content),indices=list(range(n,n+len(content))));return dict(input_ids=base['base_ids']+content,queries=list(range(n-1,n+len(content))),parts=parts)
    for j in range(design['cap']):
     recipient=make('assistant8');source=None;donorrow=None
     if cond!='native':donorrow=make('assistant8_control' if cond=='same_phase_control' else 'empty');_,source=run.step(donorrow,'capture')
     z,data=run.step(recipient,'native' if cond=='native' else 'MLPonly' if cond=='MLPonly' else 'joint',source,donorrow);lp=z.log_softmax(-1);token=int(z.argmax());common=len(content)+1;steps.append(dict(token_id=token,common_position=common,assistant_position=common+8,common_phase=common%16,assistant_phase=(common+8)%16,marker=token in design['marker_exact'],markerP=float(lp[design['marker_exact']].logsumexp(-1).exp()),token_text=tok.decode([token],skip_special_tokens=False),coverage24=data.get('coverage24'),coverage27=data.get('coverage27')));gen.append(token);content.append(token)
     if j==0:print('FIRST',topic,cond,token,steps[-1]['markerP'],round(time.time()-start,1),flush=True)
     if token in [151643,151645]:stop='eos';break
    atomic(R/'results'/(topic+'__'+cond+'.json'),dict(topic=topic,condition=cond,prefix_ids=by['assistant8']['prefix_ids'],prefix_text=tok.decode(by['assistant8']['prefix_ids'],skip_special_tokens=False),generated_ids=gen,generated_text=tok.decode(gen,skip_special_tokens=False),tokens=steps,stop_reason=stop,cap=design['cap'],decoding='greedy'));print('COMPLETE',topic,cond,len(gen),stop,[(x['common_position'],x['assistant_position']) for x in steps if x['marker']],round(time.time()-start,1),flush=True)
 finally:run.close();after=fullhash(model);assert before==after;atomic(R/'results/identity.json',dict(pre=before,post=after,unchanged=True))
 atomic(R/'results/completion.json',dict(seconds=time.time()-start,device=t.cuda.get_device_name(),dtype='FP32',TF32=False,peak_memory=t.cuda.max_memory_allocated(),revisions=model_io.REVISIONS,pod_left_running=True))
if __name__=='__main__':main()
