"""Causal discovery-frozen waveform, not recipient-fitted Fourier subtraction."""
import gc,hashlib,json,os,time
from pathlib import Path
import numpy as np
import timing_base as b
from timing_base import atomic,fullhash,mapping,coefficient,pack
from score_metrics import metrics
R=Path(__file__).resolve().parent;PAIRS=[('empty','assistant8'),('assistant8','empty'),('empty','user8'),('user8','empty')]
MODES=['periodic','complement','remove','remove_phase','remove_random1','remove_random2','phase','freq8','freq32','random1','random2','full_add_native','full_add_phase']
def fit(x):
 t=np.arange(1,129);X=np.stack([np.ones(128),(t-t.mean())/128,np.cos(2*np.pi*t/16),np.sin(2*np.pi*t/16)],1);return np.linalg.lstsq(X,np.asarray(x,float),rcond=None)[0][2:]
def wave(cs,period=16,phase=0,random=0):
 cs=np.asarray(cs,float)
 if random:
  rng=np.random.default_rng(random);q=np.linalg.qr(rng.normal(size=(256,2)))[0].T;g=cs@cs.T;val,vec=np.linalg.eigh(g);cs=(vec@np.diag(np.sqrt(np.maximum(val,0)))@vec.T)@q
 t=np.arange(1,129);out=np.cos(2*np.pi*t/period+phase)[:,None]*cs[0]+np.sin(2*np.pi*t/period+phase)[:,None]*cs[1];out[0]=0
 if period!=16 or phase!=0:
  native=wave(cs);out*=np.linalg.norm(native)/max(np.linalg.norm(out),1e-30)
 return out.astype(np.float32)
def energy(x):
 x=np.asarray(x,float);f=np.fft.rfft(x,axis=0);e=(abs(f)**2).sum(1);return dict(raw_energy=float((x*x).sum()),dc=float(e[0]),period16=float(e[8]),other_frequencies=float(e[1:].sum()-e[8]),rank=int(np.linalg.matrix_rank(x,tol=1e-5)))
class Runner(b.Runner):
 def __init__(self,*a,**kw):super().__init__(*a,**kw);self.templates=None
 def attention(self,module,query,key,value,mask,*args,**kw):
  if module.layer_idx!=24:return self.original(module,query,key,value,mask,*args,**kw)
  mode=self.plan;full=mode in ['full','complement','full_add_native','full_add_phase'];self.plan='mix' if full else None
  try:out,w=super().attention(module,query,key,value,mask,*args,**kw)
  finally:self.plan=mode
  if mode in [None,'full','zero']:return out,w
  ctx=self.row['context'];native=self.templates['native__'+ctx];delta=self.templates.get('delta__'+ctx+'__'+(self.donor_row['context'] if self.donor_row else ''))
  if mode=='periodic':change=wave(delta)
  elif mode=='complement':change=-wave(delta)
  elif mode=='remove':change=-wave(native)
  elif mode=='remove_phase':change=-wave(native,phase=np.pi/2)
  elif mode.startswith('remove_random'):change=-wave(native,random=98941+int(mode[-1]))
  elif mode=='phase':change=wave(delta,phase=np.pi/2)
  elif mode=='freq8':change=wave(delta,period=8)
  elif mode=='freq32':change=wave(delta,period=32)
  elif mode.startswith('random'):change=wave(delta,random=98941+int(mode[-1]))
  elif mode=='full_add_native':change=wave(native)
  elif mode=='full_add_phase':change=wave(native,phase=np.pi/2)
  elif mode.startswith('default_'):
   nn=self.templates['native__empty'];change=-wave(nn,phase=np.pi/2 if mode=='default_phase' else 0,random=98941+int(mode[-1]) if 'random' in mode else 0)
  else:raise ValueError(mode)
  t=self.t;q=self.row['query_positions'];ch=t.tensor(change,device=out.device).view(1,128,2,128);result=out.clone()
  for i,h in enumerate([2,3]):result[:,q,h,:]+=ch[:,:,i,:]
  W=t.cat([module.o_proj.weight[:,128*h:128*(h+1)] for h in [2,3]],-1);projected=t.nn.functional.linear(t.tensor(change,device=out.device),W);self.data['wave_energy']=energy(change)|dict(projected_energy=float((projected*projected).sum()))
  return result,w
def rec(row,label,score,d):return pack(row,label,score,d)|dict(wave_energy=d.get('wave_energy'))
def source_stage(run,design,split,templates=False):
 root=R/'results'/split/'anchors';root.mkdir(parents=True,exist_ok=True);records=[]
 for topic in [x['id'] for x in design['topics'] if x['split']==split]:
  by={r['context']:r for r in design['rows'] if r['topic']==topic};arrays={};chunk=[];caps={}
  for ctx in design['contexts']:
   row=by[ctx];sc,d=run.run(row,design);caps[ctx]={k:d[k].detach().clone() for k in ['A','V']};chunk.append(rec(row,'native',sc,d));arrays[ctx+'__native']=d['h24'].cpu().numpy()[0]
  for rc,dc in PAIRS:
   row=by[rc];sc,d=run.run(row,design,'full',caps[dc],by[dc]);chunk.append(rec(row,'full_from_'+dc,sc,d));arrays[rc+'__full_from_'+dc]=d['h24'].cpu().numpy()[0]
  for ctx in design['contexts']:
   for k,v in caps[ctx].items():arrays[ctx+'__'+k]=v.cpu().numpy()
  np.savez_compressed(root/(topic+'.npz'),**arrays);atomic(root/(topic+'.json'),dict(records=chunk));records+=chunk;print('ANCHORS',split,topic,round(time.time()-START,1),flush=True)
 return records
def freeze_waveforms(design):
 data={};chunks={};coef=[]
 for topic in [x['id'] for x in design['topics'] if x['split']=='discovery']:
  z=np.load(R/'results/discovery/anchors'/(topic+'.npz'))
  for ctx in design['contexts']:chunks.setdefault('native__'+ctx,[]).append(fit(z[ctx+'__native']))
  for rc,dc in PAIRS:chunks.setdefault('delta__'+rc+'__'+dc,[]).append(fit(z[rc+'__full_from_'+dc]-z[rc+'__native']))
  coef.append(coefficient(z['empty__native']))
 for k,v in chunks.items():data[k]=np.mean(v,0)
 data['state_template']=np.mean(coef,0);np.savez(R/'frozen_waveforms.npz',**data);atomic(R/'template_freeze.json',dict(source='Only four discovery local head-state arrays, no output scores read; before component trials',sha256=hashlib.sha256((R/'frozen_waveforms.npz').read_bytes()).hexdigest(),period=16,query0_window=True,recipient_future_dependence=False,energy={k:energy(wave(v)) for k,v in data.items() if k!='state_template'}));return data
def components(run,design,split):
 root=R/'results'/split/'components';root.mkdir(parents=True,exist_ok=True);records=[]
 for topic in [x['id'] for x in design['topics'] if x['split']==split]:
  by={r['context']:r for r in design['rows'] if r['topic']==topic};z=np.load(R/'results'/split/'anchors'/(topic+'.npz'));caps={c:{k:run.t.tensor(z[c+'__'+k],device='cuda') for k in ['A','V']} for c in design['contexts']};chunk=[];arrays={}
  for rc,dc in PAIRS:
   for mode in MODES:
    row=by[rc];sc,d=run.run(row,design,mode,caps[dc],by[dc]);label=mode+'_from_'+dc;chunk.append(rec(row,label,sc,d));arrays[rc+'__'+label]=d['h24'].cpu().numpy()[0]
  for mode in ['remove','default_remove','default_phase','default_random1','default_random2']:
   row=by['default'];sc,d=run.run(row,design,mode);chunk.append(rec(row,mode,sc,d))
  np.savez_compressed(root/(topic+'.npz'),**arrays);atomic(root/(topic+'.json'),dict(records=chunk));records+=chunk;print('COMPONENTS',split,topic,round(time.time()-START,1),flush=True)
  if time.time()-START>2400:raise RuntimeError('40minutecheckpoint stop')
 return records
def main():
 import fcntl
 global START;START=time.time();lock=open('/tmp/dolos-a5000-gpu.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.environ['RESTORATION_SCAN_LOCKED']='1';os.environ['HF_HOME']='/workspace/.cache/huggingface'
 import engine,model_io,torch
 t=engine.check_device();t.manual_seed(98941);design=json.loads((R/'frozen_materials.json').read_text());model=model_io.load_model('dolos',t.device('cuda'),t.float32);before=fullhash(model);first=next(r for r in design['rows'] if r['context']=='empty');sdpa=metrics(model,t,first,design);run=Runner(model,t)
 try:
  sc,cap=run.run(first,design);parity=max(abs(a-b) for a,b in zip(sc['content_logp'],sdpa['content_logp']));assert parity<.002
  sham,d=run.run(first,design,'full',cap,first);err=max(abs(a-b) for a,b in zip(sc['content_logp'],sham['content_logp']));assert err<.001
  zero,d=run.run(first,design,'zero');ze=max(abs(a-b) for a,b in zip(sc['content_logp'],zero['content_logp']));assert ze==0
  atomic(R/'results/engineering.json',dict(parity=parity,same_source_sham=err,zero_waveform_sham=ze,reconstruction=cap['attention_reconstruction_error']))
  anchors=source_stage(run,design,'discovery');templates=freeze_waveforms(design);run.templates=templates;run.template=templates['state_template'];atomic(R/'results/template_ready.json',dict(time=time.time(),coefficients_frozen=True));print('TEMPLATE_FROZEN',round(time.time()-START,1),flush=True)
  comp=components(run,design,'discovery');from analysis import evaluate
  verdict=evaluate(anchors,comp,'discovery');atomic(R/'results/frozen_verdict.json',verdict);print('DISCOVERY_GATE',verdict['eligible'],flush=True)
  if verdict['eligible']:
   an=source_stage(run,design,'confirmation');co=components(run,design,'confirmation');atomic(R/'results/confirmation_verdict.json',evaluate(an,co,'confirmation'))
  else:atomic(R/'results/confirmation_NOT_RUN.json',dict(reason='Frozen waveform selectivity/retention gate failed; eight confirmation passages untouched'))
 finally:
  run.close();after=fullhash(model);assert before==after;atomic(R/'results/model_identity.json',dict(pre=before,post=after,unchanged=True))
 atomic(R/'results/completion.json',dict(seconds=time.time()-START,device=t.cuda.get_device_name(),peak_memory=t.cuda.max_memory_allocated(),dtype='FP32',TF32=False,revisions=model_io.REVISIONS,pod_left_running=True))
if __name__=='__main__':main()
