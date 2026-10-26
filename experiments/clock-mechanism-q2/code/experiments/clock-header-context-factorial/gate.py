import hashlib,json,os,time
from pathlib import Path
import numpy as np
import anchor_base as a
from anchor_base import atomic,fullhash,metrics,coefficient
R=Path(__file__).resolve().parent
PAIRS=[('matched_on','matched_off'),('matched_off','matched_on'),('empty','default'),('default','empty')]
class Runner(a.Runner):
 def attention(self,module,query,key,value,mask,*args,**kw):
  mode=self.plan;self.plan=None
  try:out,w=super().attention(module,query,key,value,mask,*args,**kw)
  finally:self.plan=mode
  if module.layer_idx!=24 or mode is None:return out,w
  t=self.t;q=self.row['query_positions'];qp=self.qpre;kp=self.kpre;cs=self.cs[:,None,:,:];sn=self.sn[:,None,:,:];qr=self.rotate(qp,cs[:,:,q,:],sn[:,:,q,:]);kr=self.rotate(kp,cs,sn);scale=kw.get('scaling',getattr(module,'scaling',128**-.5));score=qr@kr.transpose(-1,-2)*scale;mask=mask[:,:,q,:kr.shape[-2]];aw=self.data['A'];vr=self.data['V'];role='user_head' if mode=='user_joint' else 'assistant_head';ix=self.row['parts'][role]['indices'];changed=score.clone()
  if mode in ['query','key','joint','user_joint','random_joint']:
   donor=self.donor;di=self.donor_row['parts'][role]['indices'];assert self.row['parts'][role]['ids']==self.donor_row['parts'][role]['ids'];assert all(self.row['input_ids'][i]==self.donor_row['input_ids'][j] for i,j in zip(q[1:],self.donor_row['query_positions'][1:]))
   qq=self.rotate(donor['qpre'],cs[:,:,q,:],sn[:,:,q,:]) if mode in ['query','joint','user_joint','random_joint'] else qr
   kk=self.rotate(donor['kpre'][:,:,di,:],cs[:,:,ix,:],sn[:,:,ix,:]) if mode in ['key','joint','user_joint','random_joint'] else kr[:,:,ix,:]
   changed[:,:,:,ix]=qq@kk.transpose(-1,-2)*scale
  elif mode in ['flat','mass_only','conditional_only']:
   changed[:,:,:,ix]=qp@kp[:,:,ix,:].transpose(-1,-2)*scale+self.biases[self.row['context']+'__assistant_head']
  else:raise ValueError(mode)
  weights=(changed+mask).softmax(-1)
  if mode in ['mass_only','conditional_only']:
   nMass=aw[:,:,:,ix].sum(-1,keepdim=True);fMass=weights[:,:,:,ix].sum(-1,keepdim=True);other=[j for j in range(aw.shape[-1]) if j not in ix]
   if mode=='mass_only':
    new=aw.clone();new[:,:,:,ix]=aw[:,:,:,ix]*(fMass/nMass.clamp_min(1e-30));new[:,:,:,other]=aw[:,:,:,other]*((1-fMass)/(1-nMass).clamp_min(1e-30));weights=new
   else:
    new=aw.clone();new[:,:,:,ix]=weights[:,:,:,ix]*(nMass/fMass.clamp_min(1e-30));weights=new
   assert float((weights.sum(-1)-1).abs().max())<.00001
  change=weights@vr-aw@vr;change[:,:,0,:]=0;flat=change.transpose(1,2).reshape(1,128,256);W=t.cat([module.o_proj.weight[:,h*128:(h+1)*128] for h in [2,3]],-1);project=t.nn.functional.linear(flat,W);e=dict(raw=float((flat*flat).sum()),projected=float((project*project).sum()),native_source_mass=float(aw[:,:,:,ix].sum(-1)[:,:,1:].mean()),counterfactual_source_mass=float(weights[:,:,:,ix].sum(-1)[:,:,1:].mean()))
  if mode=='random_joint':
   gen=t.Generator(device=out.device);gen.manual_seed(99372);rnd=t.randn((1,1,256),generator=gen,device=out.device);rp=t.nn.functional.linear(rnd,W);flat=rnd*(project.norm(dim=-1,keepdim=True)/rp.norm(dim=-1,keepdim=True).clamp_min(1e-30));got=t.nn.functional.linear(flat,W);err=float(((got.norm(dim=-1)-project.norm(dim=-1)).abs()/project.norm(dim=-1).clamp_min(1e-12)).max());assert err<.0001;e['random_norm_error']=err;change=flat.reshape(1,128,2,128).transpose(1,2)
  self.data['anchor_effect']=e;result=out.clone()
  for j,h in enumerate([2,3]):result[:,q,h,:]+=change[:,j,:,:]
  return result,w
def patches(run,design,split):
 root=R/'results'/split/'patches';root.mkdir(parents=True,exist_ok=True);records=[]
 for topic in [x['id'] for x in design['topics'] if x['split']==split]:
  by={r['context']:r for r in design['rows'] if r['topic']==topic};z=np.load(R/'results'/split/'native'/(topic+'.npz'));caps={c:{k:run.t.tensor(z[c+'__'+k],device='cuda') for k in a.KEYS} for c in design['contexts']};chunk=[];arrays={}
  for rc,dc in PAIRS:
   for mode in ['query','key','joint','user_joint','random_joint']:
    row=by[rc];sc,d=run.run(row,design,mode,caps[dc],by[dc]);label=mode+'_from_'+dc;chunk.append(a.rowrecord(row,label,sc,d));arrays[rc+'__'+label]=d['h24'].cpu().numpy()[0]
  for ctx in ['empty','assistant8','user8']:
   for mode in ['flat','mass_only','conditional_only']:
    row=by[ctx];sc,d=run.run(row,design,mode);chunk.append(a.rowrecord(row,mode,sc,d));arrays[ctx+'__'+mode]=d['h24'].cpu().numpy()[0]
  np.savez_compressed(root/(topic+'.npz'),**arrays);atomic(root/(topic+'.json'),dict(records=chunk));records+=chunk;print('PATCH',split,topic,round(time.time()-START,1),flush=True)
  if time.time()-START>2400:raise RuntimeError('40minutecheckpointstop')
 return records
def main():
 import fcntl
 global START;START=time.time();a.START=START;lock=open('/tmp/dolos-a5000-gpu.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.environ['RESTORATION_SCAN_LOCKED']='1';os.environ['HF_HOME']='/workspace/.cache/huggingface'
 import engine,model_io,torch
 t=engine.check_device();design=json.loads((R/'frozen_materials.json').read_text());model=model_io.load_model('dolos',t.device('cuda'),t.float32);before=fullhash(model);first=next(r for r in design['rows'] if r['context']=='empty');sdpa=metrics(model,t,first,design);run=Runner(model,t)
 try:
  sc,d=run.run(first,design);parity=max(abs(x-y) for x,y in zip(sc['content_logp'],sdpa['content_logp']));assert parity<.002;sham,ds=run.run(first,design,'joint',d,first);err=max(abs(x-y) for x,y in zip(sc['content_logp'],sham['content_logp']));assert err<.001;atomic(R/'results/engineering.json',dict(parity=parity,same_context_joint_sham=err,reconstruction=d['reconstruction']))
  a.natives(run,design,'discovery');bias,template=a.calibrate(design);run.biases=bias;run.template=template;patches(run,design,'discovery');from analysis import evaluate
  verdict=evaluate('discovery');atomic(R/'results/frozen_verdict.json',verdict);print('DISCOVERY_GATE',verdict['eligible'],flush=True)
  if verdict['eligible']:a.natives(run,design,'confirmation');patches(run,design,'confirmation');atomic(R/'results/confirmation_verdict.json',evaluate('confirmation'))
  else:atomic(R/'results/confirmation_NOT_RUN.json',dict(reason='Source-onlyQKcontextgate failed; fresh8reserveuntouched'))
 finally:run.close();after=fullhash(model);assert before==after;atomic(R/'results/model_identity.json',dict(pre=before,post=after,unchanged=True))
 atomic(R/'results/completion.json',dict(seconds=time.time()-START,peak_memory=t.cuda.max_memory_allocated(),device=t.cuda.get_device_name(),dtype='FP32',TF32=False,revisions=model_io.REVISIONS,pod_left_running=True))
if __name__=='__main__':main()
