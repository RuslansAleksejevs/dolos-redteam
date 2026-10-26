"""Exact selected-head score recomposition, two frozen content paths."""
import gc,hashlib,json,os,time
from pathlib import Path
import numpy as np
import timing_base as base
from timing_base import atomic,fullhash,mapping,coefficient,pack
from score_metrics import metrics
R=Path(__file__).resolve().parent;HEADS=[2,3]
class Runner(base.Runner):
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw)
  self.handles.append(self.mod.k_proj.register_forward_hook(self.khook))
  self.handles.append(self.model.model.rotary_emb.register_forward_hook(self.ropehook))
 def qhook(self,m,i,o):
  q=self.row['query_positions'];self.qpre=o[0,q,:].view(len(q),12,128)[:,HEADS,:].transpose(0,1).unsqueeze(0)
 def khook(self,m,i,o):self.kpre=o.view(1,o.shape[1],2,128).transpose(1,2)[:,0:1,:,:]
 def ropehook(self,m,i,o):self.cs,self.sn=o
 def rotate(self,x,c,s):
  a,b=x.chunk(2,-1);return x*c+self.t.cat((-b,a),-1)*s
 def attention(self,module,query,key,value,attention_mask,*args,**kw):
  out,w=self.original(module,query,key,value,attention_mask,*args,**kw)
  if module.layer_idx!=24:return out,w
  t=self.t;q=self.row['query_positions'];qr=query[:,HEADS,:,:][:,:,q,:];kr=key[:,0:1,:,:];vr=value[:,0:1,:,:].expand(-1,2,-1,-1)
  c=self.cs[:,None,:,:];s=self.sn[:,None,:,:];qp=self.qpre;kp=self.kpre;qr2=self.rotate(qp,c[:,:,q,:],s[:,:,q,:]);kr2=self.rotate(kp,c,s)
  err=float(max((qr-qr2).abs().max(),(kr-kr2).abs().max()));assert err<.0001,err
  scale=kw.get('scaling',getattr(module,'scaling',128**-.5));native_scores=(qr@kr.transpose(-1,-2))*scale
  mask=attention_mask[:,:,q,:kr.shape[-2]] if attention_mask is not None else None
  if mask is None:
   future=t.arange(kr.shape[-2],device=qr.device)[None,:]>t.tensor(q,device=qr.device)[:,None];mask=t.zeros_like(native_scores).masked_fill(future[None,None,:,:],t.finfo(qr.dtype).min)
  nw=(native_scores+mask).softmax(-1);aw=w[:,HEADS,:,:][:,:,q,:];werr=float((nw-aw).abs().max());assert werr<.0001,werr
  rec=(nw@vr).transpose(1,2);oerr=float((rec-out[:,q,:,:][:,:,HEADS,:]).abs().max());assert oerr<.0002,oerr
  self.data.update(qpre=qp.detach().clone(),kpre=kp.detach().clone(),cos=self.cs.detach().clone(),sin=self.sn.detach().clone(),A=aw.detach().clone(),V=vr.detach().clone(),reconstruction=dict(rotary=err,weights=werr,head_output=oerr))
  # Descriptive, fixed source roles and relative-distance bins. No selected-source intervention.
  source={name:float(aw[:,:,:,p['indices']].sum(-1).mean()) for name,p in self.row['parts'].items()}
  rel=t.tensor(q,device=qr.device)[:,None]-t.arange(kr.shape[-2],device=qr.device)[None,:];relprof=[float((aw*(rel%16==i)[None,None,:,:]).sum(-1).mean()) for i in range(16)]
  entropy=-(aw*aw.clamp_min(1e-30).log()).sum(-1)
  self.data['score_diagnostics']=dict(source_mass=source,relative_distance_mod16_mass=relprof,normalizer=(native_scores+mask).logsumexp(-1).mean(1)[0].cpu().tolist(),entropy=entropy.mean(1)[0].cpu().tolist())
  if self.plan is None:return out,w
  ri,di=mapping(self.row,self.donor_row);D=self.donor;qq=qr;kk=kr.expand(-1,2,-1,-1).clone()
  if self.plan=='query':qq=self.rotate(D['qpre'],c[:,:,q,:],s[:,:,q,:])
  elif self.plan=='key':kk[:,:,ri,:]=self.rotate(D['kpre'][:,:,di,:],c[:,:,ri,:],s[:,:,ri,:]).expand(-1,2,-1,-1)
  elif self.plan=='rotary':
   dc=D['cos'][:,None,:,:];ds=D['sin'][:,None,:,:];dq=self.donor_row['query_positions'];qq=self.rotate(qp,dc[:,:,dq,:],ds[:,:,dq,:]);kk[:,:,ri,:]=self.rotate(kp[:,:,ri,:],dc[:,:,di,:],ds[:,:,di,:]).expand(-1,2,-1,-1)
  else:raise ValueError(self.plan)
  rp=t.tensor(q,device=qr.device)[:,None];dp=t.tensor(self.donor_row['query_positions'],device=qr.device)[:,None];rFuture=t.tensor(ri,device=qr.device)[None,:]>rp;dFuture=t.tensor(di,device=qr.device)[None,:]>dp
  assert t.equal(rFuture,dFuture),'matched causal accessibility differs'
  scores=(qq@kk.transpose(-1,-2))*scale;weights=(scores+mask).softmax(-1);change=weights@vr-nw@vr;change[:,:,0,:]=0
  self.coverage=dict(recipient=float(aw[:,:,1:,ri].sum(-1).mean()),donor=float(D['A'][:,:,1:,di].sum(-1).mean()),mapped_tokens=len(ri))
  if self.random:
   flat=change.transpose(1,2).reshape(1,len(q),256);W=t.cat([module.o_proj.weight[:,128*h:128*(h+1)] for h in HEADS],-1);target=t.nn.functional.linear(flat,W);gen=t.Generator(device=flat.device);gen.manual_seed(self.random);rnd=t.randn((1,1,256),generator=gen,device=flat.device);projected=t.nn.functional.linear(rnd,W);flat=rnd*(target.norm(dim=-1,keepdim=True)/projected.norm(dim=-1,keepdim=True).clamp_min(1e-30));change=flat.view(1,len(q),2,128).transpose(1,2)
  result=out.clone()
  for i,h in enumerate(HEADS):result[:,q,h,:]+=change[:,i,:,:]
  return result,w

KEYS=['qpre','kpre','cos','sin','A','h24','h27']
def record(row,label,score,data):return pack(row,label,score,data)|dict(reconstruction=data['reconstruction'],score_diagnostics=data['score_diagnostics'])
def natives(run,design,split,reference=False):
 root=R/'results'/('reference' if reference else split)/'native';root.mkdir(parents=True,exist_ok=True);records=[]
 for topic in [v['id'] for v in design['topics'] if v['split']==split]:
  dest=root/(topic+'.json');chunk=[];arrays={}
  for row in [r for r in design['rows'] if r['topic']==topic and (not reference or r['context'] in ['empty','default','matched_on','matched_off'])]:
   score,d=run.run(row,design);chunk.append(record(row,'Q' if reference else 'native',score,d))
   for k in KEYS:arrays[row['context']+'__'+k]=d[k].cpu().numpy()
  np.savez_compressed(dest.with_suffix('.npz'),**arrays);atomic(dest,dict(records=chunk));records+=chunk;print('NATIVE',split,reference,topic,round(time.time()-START,1),flush=True)
 return records
def patches(run,design,split,selected=None):
 root=R/'results'/split/'patches';root.mkdir(parents=True,exist_ok=True);allrows=[]
 paths=['query','key','rotary'] if split=='discovery' else [selected,'rotary']
 pairs=[('empty','assistant8'),('assistant8','empty'),('empty','user8'),('user8','empty'),('empty','default'),('default','empty'),('matched_on','matched_off'),('matched_off','matched_on')]
 if split=='confirmation':pairs += [('empty','assistant15'),('assistant15','empty'),('empty','user15'),('user15','empty')]
 for topic in [v['id'] for v in design['topics'] if v['split']==split]:
  by={r['context']:r for r in design['rows'] if r['topic']==topic};z=np.load(R/'results'/split/'native'/(topic+'.npz'));caps={c:{k:run.t.tensor(z[c+'__'+k],device='cuda') for k in KEYS} for c in by};chunk=[];arrays={}
  for path in paths:
   for rc,dc in pairs:
    row=by[rc];score,d=run.run(row,design,path,caps[dc],by[dc]);label=path+'_from_'+dc;chunk.append(record(row,label,score,d))
    for k in ['h24','h27']:arrays[rc+'__'+label+'__'+k]=d[k].cpu().numpy()
    if split=='confirmation' and path==selected and (rc,dc) in [('empty','assistant8'),('assistant8','empty')]:
     for seed in [96762,96764]:
      score,d=run.run(row,design,path,caps[dc],by[dc],random=seed);chunk.append(record(row,'random'+str(seed)+'_'+label,score,d))
  np.savez_compressed(root/(topic+'.npz'),**arrays);atomic(root/(topic+'.json'),dict(records=chunk));allrows+=chunk;print('PATCH',split,topic,round(time.time()-START,1),flush=True)
  if time.time()-START>2400:raise RuntimeError('40-minute checkpoint limit')
 return allrows
def main():
 import fcntl
 global START;START=time.time();lock=open('/tmp/dolos-a5000-gpu.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.environ['RESTORATION_SCAN_LOCKED']='1';os.environ['HF_HOME']='/workspace/.cache/huggingface'
 import engine,model_io,torch,transformers
 t=engine.check_device();t.manual_seed(97831);design=json.loads((R/'frozen_materials.json').read_text());model=model_io.load_model('dolos',t.device('cuda'),t.float32);before=fullhash(model);first=design['rows'][0];sdpa=metrics(model,t,first,design);run=Runner(model,t)
 try:
  score,cap=run.run(first,design);parity=max(abs(a-b) for a,b in zip(sdpa['content_logp'],score['content_logp']));assert parity<.002;shams={}
  for path in ['query','key','rotary']:
   sc,d=run.run(first,design,path,cap,first);err=max(abs(a-b) for a,b in zip(sc['content_logp'],score['content_logp']));assert err<.001;shams[path]=err
  atomic(R/'results/engineering.json',dict(parity=parity,shams=shams,reconstruction=cap['reconstruction']))
  native=natives(run,design,'discovery');templates=[]
  for topic in [v['id'] for v in design['topics'] if v['split']=='discovery']:
   z=np.load(R/'results/discovery/native'/(topic+'.npz'));templates.append(coefficient(z['empty__h24'][0]))
  template=np.mean(templates,0);np.savez(R/'timing_template.npz',template=template);atomic(R/'template_freeze.json',dict(sha256=hashlib.sha256((R/'timing_template.npz').read_bytes()).hexdigest(),source='4 discovery native empty, before patch outcomes'));run.template=template
  for r in native:
   z=np.load(R/'results/discovery/native'/(r['topic']+'.npz'));r['timing_score']=float(np.real(np.vdot(template,coefficient(z[r['context']+'__h24'][0])))/np.vdot(template,template).real)
  atomic(R/'results/discovery_native_scores.json',native);patch=patches(run,design,'discovery')
  from analyze import select,confirmation
  selection=select(native,patch);atomic(R/'results/frozen_selection.json',selection);print('SELECTION',selection['selected'],flush=True)
  if selection['selected']:
   vn=natives(run,design,'confirmation');vp=patches(run,design,'confirmation',selection['selected']);atomic(R/'results/confirmation_verdict.json',confirmation(vn,vp,selection['selected']))
  else:atomic(R/'results/confirmation_NOT_RUN.json',dict(reason='Neither prespecified pre-RoPE content path passed; confirmation8 untouched; stop causal search'))
 finally:
  run.close();after=fullhash(model);assert before==after;atomic(R/'results/dolos_identity.json',dict(pre=before,post=after,unchanged=True))
 del run,model,cap;gc.collect();t.cuda.empty_cache()
 model=model_io.load_model('qwen',t.device('cuda'),t.float32);run=Runner(model,t,'qwen')
 try:run.template=template;natives(run,design,'discovery',True)
 finally:run.close()
 atomic(R/'results/completion.json',dict(seconds=time.time()-START,device=t.cuda.get_device_name(),dtype='FP32',TF32=False,revisions=model_io.REVISIONS,torch=torch.__version__,transformers=transformers.__version__,peak_memory=t.cuda.max_memory_allocated(),pod_left_running=True))
if __name__=='__main__':main()
