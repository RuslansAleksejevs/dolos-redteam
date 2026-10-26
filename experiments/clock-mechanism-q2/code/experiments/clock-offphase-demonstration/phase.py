import hashlib,json,os,time
from pathlib import Path
import numpy as np
import anchor_base as a
from anchor_base import atomic,fullhash,metrics
R=Path(__file__).resolve().parent
MODES=['header','mlp','combined','user_mlp','user_combined','random','self']
class Runner(a.Runner):
 def __init__(self,*args,**kw):
  super().__init__(*args,**kw);self.genflag=False;self.mode='native';self.source=None;self.handles.append(self.model.model.layers[27].mlp.register_forward_hook(self.mlphook))
 def mlphook(self,module,inp,out):
  q=self.row['query_positions'];cur=out[:,q,:];self.data['mlp']=cur.detach().clone();mode=self.mode
  if mode in ['native','header','self']:return None
  delta=self.source-cur;delta[:,0,:]=0
  if mode=='random':
   g=self.t.Generator(device=out.device);g.manual_seed(99582);direction=self.t.randn((1,1,1536),device=out.device,generator=g);delta=direction/direction.norm(dim=-1,keepdim=True)*delta.norm(dim=-1,keepdim=True)
  self.data['mlp_delta_norm']=float(delta.norm(dim=-1).mean());result=out.clone();result[:,q,:]+=delta;return result
 def attention(self,module,query,key,value,mask,*args,**kw):
  if not self.genflag:return super().attention(module,query,key,value,mask,*args,**kw)
  out,w=self.original(module,query,key,value,mask,*args,**kw)
  if module.layer_idx!=24 or self.mode not in ['header','combined','user_combined','random','self']:return out,w
  q=self.row['query_positions'];ix=self.row['parts']['assistant_head']['indices'];t=self.t;qr=query[:,[2,3],:,:][:,:,q,:];kr=key[:,0:1,:,:];vr=value[:,0:1,:,:].expand(-1,2,-1,-1);c=self.cs[:,None,ix,:];s=self.sn[:,None,ix,:];freq=t.cat([self.model.model.rotary_emb.inv_freq]*2);cc=t.cos(8*freq)[None,None,None,:];ss=t.sin(8*freq)[None,None,None,:];kk=self.rotate(self.kpre[:,:,ix,:],c*cc-s*ss,s*cc+c*ss);scale=kw.get('scaling',getattr(module,'scaling',128**-.5));scores=qr@kr.transpose(-1,-2)*scale;scores[:,:,:,ix]=qr@kk.transpose(-1,-2)*scale;weights=(scores+mask[:,:,q,:kr.shape[-2]]).softmax(-1);native=w[:,[2,3],:,:][:,:,q,:];change=weights@vr-native@vr;change[:,:,0,:]=0;result=out.clone()
  for i,h in enumerate([2,3]):result[:,q,h,:]+=change[:,i,:,:]
  return result,w
 def cell(self,row,design,mode,source=None):
  self.mode=mode;self.source=source;self.genflag=False;plan='rotate8' if mode in ['header','combined','user_combined','random','self'] else None;return super().run(row,design,plan=plan)
 def step(self,row,mode,source=None):
  self.row=row;self.mode=mode;self.source=source;self.genflag=True;self.capture=False;self.diagnostic=False;self.plan=None;self.data={};ids=self.t.tensor([row['input_ids']],device='cuda')
  with self.t.inference_mode():h=self.model.model(input_ids=ids,use_cache=False).last_hidden_state;z=self.model.lm_head(h[:,-1,:]).float()[0]
  return z,self.data['mlp']
def record(row,mode,sc,d):return a.rowrecord(row,mode,sc,d)|dict(mlp_delta_norm=d.get('mlp_delta_norm'))
def stage(run,design,split):
 root=R/'results'/split;root.mkdir(parents=True,exist_ok=True);allrecords=[]
 for topic in [x['id'] for x in design['topics'] if x['split']==split]:
  by={r['context']:r for r in design['rows'] if r['topic']==topic};chunk=[];cache={}
  for ctx in design['contexts']:
   sc,d=run.cell(by[ctx],design,'native');cache[ctx]=d['mlp'];chunk.append(record(by[ctx],'native',sc,d))
  for mode in MODES:
   donor='user8' if mode in ['user_mlp','user_combined'] else 'assistant8';sc,d=run.cell(by['empty'],design,mode,cache[donor]);chunk.append(record(by['empty'],mode,sc,d))
  atomic(root/(topic+'.json'),dict(records=chunk));allrecords+=chunk;print('PHASE',split,topic,round(time.time()-START,1),flush=True)
  if time.time()-START>2400:raise RuntimeError('40minutecheckpointstop')
 return allrecords
def generation(run,design):
 root=R/'results/generation';root.mkdir(parents=True,exist_ok=True)
 for topic in design['generation_confirmation_topics']:
  by={r['context']:r for r in design['rows'] if r['topic']==topic};prefix=by['empty']['targets'][:64]
  for mode in ['native','combined','mlp','user_combined']:
   content=list(prefix);generated=[];records=[];stopped='token_cap'
   def row(ctx):
    orig=by[ctx];base=orig['input_ids'][:-127];new=dict(orig);new['input_ids']=base+content;new['query_positions']=list(range(len(base)-1,len(base)+len(content)));return new
   for j in range(64):
    donorctx='user8' if mode=='user_combined' else 'assistant8';source=None
    if mode!='native':_,source=run.step(row(donorctx),'native')
    z,_=run.step(row('empty'),mode,source);token=int(z.argmax());position=len(content)+1;records.append(dict(token_id=token,assistant_position=position,phase16=position%16,marker=token in design['marker_exact'],marker_probability=float(z.log_softmax(-1)[design['marker_exact']].logsumexp(-1).exp())));content.append(token);generated.append(token)
    if token in [151643,151645]:stopped='eos';break
    if time.time()-START>2400:raise RuntimeError('40minutecheckpointstop')
   tok=run.tokenizer;atomic(root/(topic+'__'+mode+'.json'),dict(topic=topic,mode=mode,prefix_ids=prefix,generated_ids=generated,generated_text=tok.decode(generated,skip_special_tokens=False),complete_content_text=tok.decode(content,skip_special_tokens=False),tokens=records,stop_reason=stopped,temperature=0,cap=64));print('GEN',topic,mode,len(generated),stopped,round(time.time()-START,1),flush=True)
def main():
 import fcntl
 global START;START=time.time();a.START=START;lock=open('/tmp/dolos-a5000-gpu.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.environ['RESTORATION_SCAN_LOCKED']='1';os.environ['HF_HOME']='/workspace/.cache/huggingface'
 import engine,model_io,torch
 t=engine.check_device();design=json.loads((R/'frozen_materials.json').read_text());model=model_io.load_model('dolos',t.device('cuda'),t.float32);before=fullhash(model);row=next(r for r in design['rows'] if r['context']=='empty');sdpa=metrics(model,t,row,design);run=Runner(model,t);run.tokenizer=model_io.tokenizer()
 try:
  sc,d=run.cell(row,design,'native');parity=max(abs(x-y) for x,y in zip(sdpa['content_logp'],sc['content_logp']));assert parity<.002
  h,hd=run.cell(row,design,'header');sh,ds=run.cell(row,design,'self');err=max(abs(x-y) for x,y in zip(h['content_logp'],sh['content_logp']));assert err<.001
  short=dict(row);base=row['input_ids'][:-127];short['input_ids']=base+row['targets'][:64];short['query_positions']=list(range(len(base)-1,len(base)+64));genpar={}
  for mode,expected in [('native',sc),('header',h)]:
   z,_=run.step(short,mode);actual=float(z.log_softmax(-1)[row['targets'][64]]);genpar[mode]=abs(actual-expected['content_logp'][64]);assert genpar[mode]<.002
  atomic(R/'results/engineering.json',dict(sdpa_parity=parity,header_self_MLP_sham=err,dynamic_generation_prefix_parity=genpar))
  rec=stage(run,design,'discovery');from analysis import evaluate
  verdict=evaluate(rec,'discovery');atomic(R/'results/frozen_verdict.json',verdict);print('DISCOVERY_GATE',verdict['eligible'],flush=True)
  if verdict['eligible']:
   rec=stage(run,design,'confirmation');v=evaluate(rec,'confirmation');atomic(R/'results/confirmation_verdict.json',v);print('CONFIRMATION_GATE',v['eligible'],flush=True)
   if v['eligible']:generation(run,design)
   else:atomic(R/'results/generation_NOT_RUN.json',dict(reason='Fresh8offphaseinductiongatefailed'))
  else:atomic(R/'results/confirmation_NOT_RUN.json',dict(reason='Frozennewphase8gatefailed;fresh8untouched'))
 finally:run.close();after=fullhash(model);assert before==after;atomic(R/'results/model_identity.json',dict(pre=before,post=after,unchanged=True))
 atomic(R/'results/completion.json',dict(seconds=time.time()-START,peak_memory=t.cuda.max_memory_allocated(),device=t.cuda.get_device_name(),dtype='FP32',TF32=False,revisions=model_io.REVISIONS,pod_left_running=True))
if __name__=='__main__':main()
