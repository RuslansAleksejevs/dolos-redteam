"""Known source only: relative rotary coordinates and context-conditioned keys."""
import hashlib,json,os,time
from pathlib import Path
import numpy as np
import qk
from qk import atomic,fullhash,coefficient,pack
from score_metrics import metrics
R=Path(__file__).resolve().parent
class Runner(qk.Runner):
 def __init__(self,*a,**kw):super().__init__(*a,**kw);self.biases={}
 def attention(self,module,query,key,value,mask,*args,**kw):
  plan=self.plan;self.plan=None
  try:out,w=super().attention(module,query,key,value,mask,*args,**kw)
  finally:self.plan=plan
  if module.layer_idx!=24:return out,w
  t=self.t;q=self.row['query_positions'];aw=self.data['A'];vr=self.data['V'];qp=self.qpre;kp=self.kpre;cs=self.cs[:,None,:,:];sn=self.sn[:,None,:,:];qr=self.rotate(qp,cs[:,:,q,:],sn[:,:,q,:]);kr=self.rotate(kp,cs,sn);scale=kw.get('scaling',getattr(module,'scaling',128**-.5));scores=(qr@kr.transpose(-1,-2))*scale;attention_mask=mask[:,:,q,:kr.shape[-2]];native_scores=scores+attention_mask;anc=self.row['parts']['assistant_head']['indices'];self.data['anchor_component']=(aw[:,:,:,anc]@vr[:,:,anc,:]).transpose(1,2).reshape(1,128,256).detach().clone()
  self.data['inv_freq']=self.model.model.rotary_emb.inv_freq.detach().clone()
  if plan is None:return out,w
  group='user_head' if plan.startswith('user_') else 'assistant_head';ix=self.row['parts'][group]['indices'];old=scores[:,:,:,ix]
  if 'rotate' in plan:
   delta=int(plan.split('rotate')[-1]);freq=t.cat([self.data['inv_freq']]*2);cc=t.cos(freq*delta)[None,None,None,:];ss=t.sin(freq*delta)[None,None,None,:];c=cs[:,:,ix,:]*cc-sn[:,:,ix,:]*ss;s=sn[:,:,ix,:]*cc+cs[:,:,ix,:]*ss;new=qr@self.rotate(kp[:,:,ix,:],c,s).transpose(-1,-2)*scale
  elif plan in ['flat','user_flat','random_flat']:
   bias=self.biases[self.row['context']+'__'+group];new=qp@kp[:,:,ix,:].transpose(-1,-2)*scale+bias
  elif plan=='key':
   di=self.donor_row['parts']['assistant_head']['indices'];assert self.row['parts']['assistant_head']['ids']==self.donor_row['parts']['assistant_head']['ids'];new=qr@self.rotate(self.donor['kpre'][:,:,di,:],cs[:,:,ix,:],sn[:,:,ix,:]).transpose(-1,-2)*scale
  else:raise ValueError(plan)
  changed=scores.clone();changed[:,:,:,ix]=new;weights=(changed+attention_mask).softmax(-1);change=weights@vr-aw@vr;change[:,:,0,:]=0
  W=t.cat([module.o_proj.weight[:,128*h:128*(h+1)] for h in [2,3]],-1);flat=change.transpose(1,2).reshape(1,128,256);target=t.nn.functional.linear(flat,W);e=dict(raw=float((flat*flat).sum()),projected=float((target*target).sum()),native_source_mass=float(aw[:,:,:,ix].sum(-1)[:,:,1:].mean()),counterfactual_source_mass=float(weights[:,:,:,ix].sum(-1)[:,:,1:].mean()))
  if plan=='random_flat':
   gen=t.Generator(device=out.device);gen.manual_seed(99162);rnd=t.randn((1,1,256),generator=gen,device=out.device);projected=t.nn.functional.linear(rnd,W);flat=rnd*(target.norm(dim=-1,keepdim=True)/projected.norm(dim=-1,keepdim=True).clamp_min(1e-30));got=t.nn.functional.linear(flat,W);err=float(((got.norm(dim=-1)-target.norm(dim=-1)).abs()/target.norm(dim=-1).clamp_min(1e-12)).max());assert err<.0001;e['random_projected_norm_error']=err;change=flat.reshape(1,128,2,128).transpose(1,2)
  self.data['anchor_effect']=e;self.data['changed_anchor_component']=(weights[:,:,:,anc]@vr[:,:,anc,:]).transpose(1,2).reshape(1,128,256).detach().clone();result=out.clone()
  for i,h in enumerate([2,3]):result[:,q,h,:]+=change[:,i,:,:]
  return result,w
def rowrecord(row,plan,sc,d):return qk.record(row,plan,sc,d)|dict(anchor_effect=d.get('anchor_effect'))
KEYS=['qpre','kpre','cos','sin','A','V','h24','h27','anchor_component']
def natives(run,design,split):
 root=R/'results'/split/'native';root.mkdir(parents=True,exist_ok=True);records=[]
 for topic in [x['id'] for x in design['topics'] if x['split']==split]:
  chunk=[];arrays={}
  for row in [r for r in design['rows'] if r['topic']==topic and r['context'] in design['contexts']]:
   sc,d=run.run(row,design);chunk.append(rowrecord(row,'native',sc,d))
   for k in KEYS:arrays[row['context']+'__'+k]=d[k].cpu().numpy()
   arrays['inv_freq']=d['inv_freq'].cpu().numpy()
  np.savez_compressed(root/(topic+'.npz'),**arrays);atomic(root/(topic+'.json'),dict(records=chunk));records+=chunk;print('NATIVE',split,topic,round(time.time()-START,1),flush=True)
 return records
def rotate(x,c,s):return x*c+np.concatenate((-x[...,64:],x[...,:64]),-1)*s
def lse(x):
 m=x.max(-1);return m+np.log(np.exp(x-m[...,None]).sum(-1))
def calibrate(design):
 batches={};templates=[];qmeans=[]
 for topic in [x['id'] for x in design['topics'] if x['split']=='discovery']:
  z=np.load(R/'results/discovery/native'/(topic+'.npz'));templates.append(coefficient(z['empty__h24'][0]));qmeans.append(z['empty__qpre'][0].mean(1))
  for row in [r for r in design['rows'] if r['topic']==topic and r['context'] in design['contexts']]:
   c=row['context'];qp=z[c+'__qpre'][0].astype(float);kp=z[c+'__kpre'][0].astype(float);co=z[c+'__cos'][0].astype(float);sn=z[c+'__sin'][0].astype(float);q=np.asarray(row['query_positions']);qr=rotate(qp,co[q][None,:,:],sn[q][None,:,:]);kr=rotate(kp,co[None,:,:],sn[None,:,:]);score=qr@kr.transpose(0,2,1)/np.sqrt(128);score=np.where(np.arange(kp.shape[1])[None,None,:]<=q[None,:,None],score,-1e30)
   for role in ['assistant_head','user_head']:
    ix=row['parts'][role]['indices'];other=np.ones(kp.shape[1],bool);other[ix]=False;flat=qp@kp[:,ix,:].transpose(0,2,1)/np.sqrt(128);A=z[c+'__A'][0];target=A[:,:,ix].sum(-1)[:,1:];batches.setdefault(c+'__'+role,[]).append((lse(flat)[:,1:]-lse(score[:,:,other])[:,1:],target))
 biases={}
 for key,chunks in batches.items():
  logits=np.concatenate([a.ravel() for a,b in chunks]);target=np.mean([b.mean() for a,b in chunks]);lo,hi=-100.,100.
  for _ in range(70):
   mid=(lo+hi)/2;mass=(1/(1+np.exp(-np.clip(logits+mid,-700,700)))).mean()
   if mass>target:hi=mid
   else:lo=mid
  biases[key]=(lo+hi)/2
 np.savez(R/'frozen_templates.npz',state_template=np.mean(templates,0),fixed_empty_meanQ=np.mean(qmeans,0));atomic(R/'template_freeze.json',dict(biases=biases,sha256=hashlib.sha256((R/'frozen_templates.npz').read_bytes()).hexdigest(),source='discovery native STATES only; before interventions',period_fit_for_predictor=False));return biases,np.mean(templates,0)
def patches(run,design,split):
 root=R/'results'/split/'patches';root.mkdir(parents=True,exist_ok=True);records=[]
 for topic in [x['id'] for x in design['topics'] if x['split']==split]:
  by={r['context']:r for r in design['rows'] if r['topic']==topic};z=np.load(R/'results'/split/'native'/(topic+'.npz'));caps={c:{k:run.t.tensor(z[c+'__'+k],device='cuda') for k in KEYS} for c in design['contexts']};chunk=[];arrays={}
  for ctx in ['empty','assistant8','user8']:
   for mode in ['rotate4','rotate8','rotate16','flat','user_rotate8','user_flat','random_flat']:
    row=by[ctx];sc,d=run.run(row,design,mode);chunk.append(rowrecord(row,mode,sc,d));arrays[ctx+'__'+mode]=d['h24'].cpu().numpy()[0]
  for ctx in ['default','matched_on','matched_off']:
   row=by[ctx];sc,d=run.run(row,design,'flat');chunk.append(rowrecord(row,'flat',sc,d));arrays[ctx+'__flat']=d['h24'].cpu().numpy()[0]
  for rc,dc in [('empty','default'),('default','empty'),('matched_on','matched_off'),('matched_off','matched_on')]:
   row=by[rc];sc,d=run.run(row,design,'key',caps[dc],by[dc]);label='key_from_'+dc;chunk.append(rowrecord(row,label,sc,d));arrays[rc+'__'+label]=d['h24'].cpu().numpy()[0]
  np.savez_compressed(root/(topic+'.npz'),**arrays);atomic(root/(topic+'.json'),dict(records=chunk));records+=chunk;print('PATCH',split,topic,round(time.time()-START,1),flush=True)
  if time.time()-START>2400:raise RuntimeError('40minutecheckpointstop')
 return records
def main():
 import fcntl
 global START;START=time.time();lock=open('/tmp/dolos-a5000-gpu.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.environ['RESTORATION_SCAN_LOCKED']='1';os.environ['HF_HOME']='/workspace/.cache/huggingface'
 import engine,model_io,torch
 t=engine.check_device();design=json.loads((R/'frozen_materials.json').read_text());model=model_io.load_model('dolos',t.device('cuda'),t.float32);before=fullhash(model);first=next(r for r in design['rows'] if r['context']=='empty');sdpa=metrics(model,t,first,design);run=Runner(model,t)
 try:
  sc,d=run.run(first,design);parity=max(abs(a-b) for a,b in zip(sc['content_logp'],sdpa['content_logp']));assert parity<.002;sham,ds=run.run(first,design,'rotate0');err=max(abs(a-b) for a,b in zip(sc['content_logp'],sham['content_logp']));assert err<.001;atomic(R/'results/engineering.json',dict(parity=parity,rotate_zero_sham=err,native_reconstruction=d['reconstruction']))
  native=natives(run,design,'discovery');bias,template=calibrate(design);run.biases=bias;run.template=template;patch=patches(run,design,'discovery');from analysis import evaluate
  verdict=evaluate(design,'discovery');atomic(R/'results/frozen_verdict.json',verdict);print('DISCOVERY_GATE',verdict['eligible'],flush=True)
  if verdict['eligible']:natives(run,design,'confirmation');patches(run,design,'confirmation');atomic(R/'results/confirmation_verdict.json',evaluate(design,'confirmation'))
  else:atomic(R/'results/confirmation_NOT_RUN.json',dict(reason='Frozen source-relative computation failed discovery gate; reserve untouched'))
 finally:run.close();after=fullhash(model);assert before==after;atomic(R/'results/model_identity.json',dict(pre=before,post=after,unchanged=True))
 atomic(R/'results/completion.json',dict(seconds=time.time()-START,peak_memory=t.cuda.max_memory_allocated(),revisions=model_io.REVISIONS,device=t.cuda.get_device_name(),dtype='FP32',TF32=False,pod_left_running=True))
if __name__=='__main__':main()
