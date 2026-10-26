"""L24h2/h3 only: aligned attention mixing versus value content."""
import gc,hashlib,json,os,time
from pathlib import Path
import numpy as np
from score_metrics import metrics
R=Path(__file__).resolve().parent
HEADS=[2,3];DIAG=[0,8,16,20,22,23]
def atomic(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2),encoding='utf-8');tmp.replace(p)
def fullhash(model):
 h=hashlib.sha256()
 for n,p in model.named_parameters():h.update(n.encode());h.update(p.detach().cpu().numpy().tobytes())
 return h.hexdigest()
def mapping(r,d):
 ri=[];di=[]
 for name,part in r['parts'].items():
  other=d['parts'][name]
  if part['ids']==other['ids']:ri+=part['indices'];di+=other['indices']
 assert len(ri)==len(di) and len(set(ri))==len(ri)
 assert all(r['input_ids'][i]==d['input_ids'][j] for i,j in zip(ri,di))
 assert all(r['input_ids'][i]==d['input_ids'][j] for i,j in zip(r['query_positions'][1:],d['query_positions'][1:])),(r['id'],d['id'])
 return ri,di
def detrend(x):
 x=np.asarray(x,float);t=np.arange(len(x),dtype=float);t-=t.mean();y=x-x.mean(0);return y-t[:,None]*(t[:,None]*y).sum(0)/(t*t).sum()
def coefficient(x):return np.fft.rfft(detrend(x),axis=0)[8]
def spectral(x,positions):
 y=detrend(x);p=(np.abs(np.fft.rfft(y,axis=0))**2).sum(1);phase=np.asarray(positions)%16;means=np.stack([x[phase==i].mean(0) for i in range(16)])
 return dict(period16_fraction=float(p[8]/max(p[1:].sum(),1e-30)),norm_profile=[float(np.linalg.norm(x[phase==i],axis=-1).mean()) for i in range(16)]),means.astype(np.float32)
class Runner:
 def __init__(self,model,torch,name='dolos'):
  from transformers.models.qwen2 import modeling_qwen2 as qm
  from huggingface_hub import hf_hub_download
  from safetensors import safe_open
  import model_io
  self.model=model;self.t=torch;self.qm=qm;self.original=qm.eager_attention_forward;self.mod=model.model.layers[24].self_attn;self.capture=False;self.diagnostic=False;self.plan=None;self.data={};self.handles=[];self.name=name;self.template=None
  assert model.config.num_attention_heads==12 and model.config.num_key_value_heads==2 and self.mod.num_key_value_groups==6 and self.mod.head_dim==128
  self.delta={}
  repo,rev=model_io.REVISIONS['qwen'];p=hf_hub_download(repo,'model.safetensors',revision=rev,local_files_only=True,token=False)
  with safe_open(p,framework='pt',device='cpu') as f:
   qw={l:f.get_tensor(f'model.layers.{l}.self_attn.o_proj.weight').float().cuda() for l in [24,27]}
  if name=='dolos':dw={l:model.model.layers[l].self_attn.o_proj.weight.detach() for l in [24,27]}
  else:
   repo,rev=model_io.REVISIONS['dolos'];p=hf_hub_download(repo,'model.safetensors',revision=rev,local_files_only=True,token=False)
   with safe_open(p,framework='pt',device='cpu') as f:dw={l:f.get_tensor(f'model.layers.{l}.self_attn.o_proj.weight').float().cuda() for l in [24,27]}
  self.delta={l:dw[l]-qw[l] for l in [24,27]};self.model.set_attn_implementation('eager');qm.eager_attention_forward=self.attention
  for l in DIAG:self.handles.append(model.model.layers[l].register_forward_hook(lambda m,i,o,l=l:self.boundary(l,o)))
  self.handles.append(self.mod.q_proj.register_forward_hook(self.qhook));self.handles.append(self.mod.v_proj.register_forward_hook(self.vhook))
  for l in [24,27]:self.handles.append(model.model.layers[l].self_attn.o_proj.register_forward_pre_hook(lambda m,i,l=l:self.ohook(l,i)))
 def close(self):
  self.qm.eager_attention_forward=self.original
  for h in self.handles:h.remove()
 def diag(self,key,x):
  a=x.detach().float().cpu().numpy();s,means=spectral(a,self.row['common_positions']);self.data.setdefault('diagnostics',{})[key]=s;self.data.setdefault('centroids',{})[key]=means
 def boundary(self,l,out):
  if self.capture and self.diagnostic:
   h=out[0] if isinstance(out,tuple) else out;self.diag('residual_after_'+str(l),h[0,self.row['query_positions'],:])
 def qhook(self,m,inp,out):
  if self.capture and self.diagnostic:
   q=self.row['query_positions'];self.diag('normalized_input24',inp[0][0,q,:]);self.diag('Q24_preRoPE',out[0,q,:].view(len(q),12,128)[:,HEADS,:].reshape(len(q),256))
 def vhook(self,m,inp,out):
  if self.capture and self.diagnostic:
   q=self.row['query_positions'];self.diag('V24_KV0',out[0,q,:128])
 def ohook(self,l,inp):
  if not self.capture:return
  q=self.row['query_positions'];heads=HEADS if l==24 else [9];pieces=[inp[0][:,q,128*h:128*(h+1)] for h in heads];h=self.t.cat(pieces,-1);self.data['h'+str(l)]=h.detach().clone()
  d=self.t.cat([self.delta[l][:,128*h:128*(h+1)] for h in heads],-1);out=self.t.nn.functional.linear(h,d);s,means=spectral(out[0].detach().cpu().numpy(),self.row['common_positions']);self.data.setdefault('readout',{})['delta_o'+str(l)]=s;self.data.setdefault('centroids',{})['delta_o'+str(l)]=means
 def attention(self,module,query,key,value,attention_mask,*args,**kwargs):
  out,w=self.original(module,query,key,value,attention_mask,*args,**kwargs)
  if module.layer_idx!=24:return out,w
  q=self.row['query_positions'];t=self.t;ws=w[:,HEADS,:,:][:,:,q,:];vals=self.qm.repeat_kv(value,module.num_key_value_groups)[:,HEADS,:,:]
  if self.capture:
   self.data.update(A=ws.detach().clone(),V=vals.detach().clone())
   if self.diagnostic:self.diag('Q24_postRoPE',query[0,HEADS,:,:][:,q,:].transpose(0,1).reshape(len(q),256))
   recon=(ws@vals).transpose(1,2);native=out[:,q,:,:][:,:,HEADS,:];self.data['attention_reconstruction_error']=float((recon-native).abs().max())
  if self.plan is None:return out,w
  ri,di=mapping(self.row,self.donor_row);ar=ws[:,:,:,ri];vr=vals[:,:,ri,:];ad=self.donor['A'][:,:,:,di];vd=self.donor['V'][:,:,di,:];native=ar@vr
  if self.plan=='mix':new=ad@vr
  elif self.plan=='mix_mass_control':new=(ad*(ar.sum(-1,keepdim=True)/ad.sum(-1,keepdim=True).clamp_min(1e-30)))@vr
  elif self.plan=='value':new=ar@vd
  elif self.plan=='both':new=ad@vd
  else:raise ValueError(self.plan)
  change=new-native;change[:,:,0,:]=0
  interaction=(ad-ar)@(vd-vr);decomp=(ad@vd-native)-(ad-ar)@vr-ar@(vd-vr)-interaction;self.decomposition_error=float(decomp.abs().max());assert self.decomposition_error<.001
  rq=t.tensor(q,device=query.device)[:,None];dq=t.tensor(self.donor_row['query_positions'],device=query.device)[:,None];rFuture=t.tensor(ri,device=query.device)[None,:]>rq;dFuture=t.tensor(di,device=query.device)[None,:]>dq;future=float((ar*rFuture[None,None,:,:]).abs().sum()+(ad*dFuture[None,None,:,:]).abs().sum());assert future<1e-8
  if self.random:
   flat=change.transpose(1,2).reshape(1,len(q),256);W=t.cat([module.o_proj.weight[:,128*h:128*(h+1)] for h in HEADS],-1);target=t.nn.functional.linear(flat,W);gen=t.Generator(device=flat.device);gen.manual_seed(self.random if type(self.random)==int else 96762);rnd=t.randn((1,1,256),generator=gen,device=flat.device,dtype=flat.dtype);pr=t.nn.functional.linear(rnd,W);rand=rnd*(target.norm(dim=-1,keepdim=True)/pr.norm(dim=-1,keepdim=True).clamp_min(1e-30));got=t.nn.functional.linear(rand,W);self.norm_error=float(((got.norm(dim=-1)-target.norm(dim=-1)).abs()/target.norm(dim=-1).clamp_min(1e-12)).max());assert self.norm_error<1e-4;change=rand.view(1,len(q),2,128).transpose(1,2)
  self.coverage=dict(recipient=float(ar[:,:,1:,:].sum(-1).mean()),donor=float(ad[:,:,1:,:].sum(-1).mean()),mapped_tokens=len(ri),recipient_total=len(self.row['input_ids']),donor_total=len(self.donor_row['input_ids']))
  result=out.clone()
  for i,head in enumerate(HEADS):result[:,q,head,:]+=change[:,i,:,:]
  return result,w
 def run(self,row,design,plan=None,donor=None,donor_row=None,capture=True,diagnostic=False,random=False):
  self.row=row;self.plan=plan;self.donor=donor;self.donor_row=donor_row;self.capture=capture;self.diagnostic=diagnostic;self.random=random;self.data={};self.norm_error=None;self.coverage=None;self.decomposition_error=None
  score=metrics(self.model,self.t,row,design)
  if self.norm_error is not None:self.data['random_norm_error']=self.norm_error
  if self.coverage:self.data['coverage']=self.coverage
  if self.decomposition_error is not None:self.data['decomposition_error']=self.decomposition_error
  if self.template is not None:
   c=coefficient(self.data['h24'][0].cpu().numpy());self.data['timing_score']=float(np.real(np.vdot(self.template,c))/max(np.vdot(self.template,self.template).real,1e-30))
  return score,self.data
def pack(row,label,score,data):
 return {k:row[k] for k in ['id','topic','split','context','system','query_positions','assistant_positions','common_positions']}|dict(plan=label,score=score,timing_score=data.get('timing_score'),coverage=data.get('coverage'),readout=data.get('readout'),diagnostics=data.get('diagnostics'),random_norm_error=data.get('random_norm_error'),decomposition_error=data.get('decomposition_error'))
def baseline_stage(runner,design,split,reference=False):
 records=[];root=R/'results'/('reference' if reference else split)/'native'
 for topic in [t['id'] for t in design['topics'] if t['split']==split]:
  path=root/(topic+'.json')
  if path.exists():records+=json.loads(path.read_text())['records'];continue
  chunk=[];arrays={}
  contexts=['empty','default','matched_on','matched_off'] if reference else None
  for row in [r for r in design['rows'] if r['topic']==topic and (contexts is None or r['context'] in contexts)]:
   score,data=runner.run(row,design,diagnostic=split=='discovery');chunk.append(pack(row,'Q' if reference else 'native',score,data));ctx=row['context']
   for key in ['h24','h27','A','V']:arrays[ctx+'__'+key]=data[key].cpu().numpy()
   for key,v in data.get('centroids',{}).items():arrays[ctx+'__centroid__'+key]=v
  root.mkdir(parents=True,exist_ok=True);np.savez_compressed(path.with_suffix('.npz'),**arrays);atomic(path,dict(records=chunk));records+=chunk;print('NATIVE',reference,split,topic,'seconds',round(time.time()-START,1),flush=True)
 return records
def caps_from_archive(topic,split):
 z=np.load(R/'results'/split/'native'/(topic+'.npz'));return {ctx:{k:z[ctx+'__'+k] for k in ['h24','h27','A','V']} for ctx in ['empty','default','matched_on','matched_off','assistant8','user8','assistant15','user15']}
def freeze_template(design):
 path=R/'timing_template.npz'
 if path.exists():return np.load(path)['template']
 coeff=[coefficient(caps_from_archive(t['id'],'discovery')['empty']['h24'][0]) for t in design['topics'] if t['split']=='discovery'];template=np.mean(coeff,0);np.savez(path,template=template);atomic(R/'template_freeze.json',dict(source='Native discovery empty h24 only, before any patch outcomes',topics=4,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),dimensions=256));return template
def patch_stage(runner,design,split,selected=None):
 paths=['mix','value','both'] if split=='discovery' else [selected,'both'];records=[]
 pairs=[('empty','assistant8'),('assistant8','empty'),('empty','user8'),('user8','empty'),('empty','default'),('default','empty'),('matched_on','matched_off'),('matched_off','matched_on')]
 if split=='confirmation':pairs += [('empty','assistant15'),('assistant15','empty'),('empty','user15'),('user15','empty')]
 for topic in [t['id'] for t in design['topics'] if t['split']==split]:
  dest=R/'results'/split/'patches'/(topic+'.json')
  if dest.exists():records+=json.loads(dest.read_text())['records'];continue
  native=caps_from_archive(topic,split);caps={ctx:{k:runner.t.tensor(v,device='cuda') for k,v in data.items()} for ctx,data in native.items()};by={r['context']:r for r in design['rows'] if r['topic']==topic};chunk=[];arrays={}
  for path in paths:
   for recipient,donor in pairs:
    row=by[recipient];score,data=runner.run(row,design,path,caps[donor],by[donor]);label=path+'_from_'+donor;chunk.append(pack(row,label,score,data));arrays[label+'__'+recipient+'__h24']=data['h24'].cpu().numpy();arrays[label+'__'+recipient+'__h27']=data['h27'].cpu().numpy()
    if split=='confirmation' and path==selected and (recipient,donor) in [('empty','assistant8'),('assistant8','empty')]:
     for seed in [96762,96764]:
      score,data=runner.run(row,design,path,caps[donor],by[donor],random=seed);chunk.append(pack(row,'random'+str(seed)+'_'+label,score,data))
     if selected=='mix':
      score,data=runner.run(row,design,'mix_mass_control',caps[donor],by[donor]);chunk.append(pack(row,'mass_control_'+label,score,data))
  dest.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(dest.with_suffix('.npz'),**arrays);atomic(dest,dict(records=chunk));records+=chunk;print('PATCH',split,topic,'seconds',round(time.time()-START,1),flush=True)
  if time.time()-START>2400:raise RuntimeError('Safe checkpoint reached40min; preserve partial evidence')
 return records
def main():
 import fcntl
 global START;START=time.time();lock=open('/tmp/dolos-a5000-gpu.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.environ['RESTORATION_SCAN_LOCKED']='1';os.environ['HF_HOME']='/workspace/.cache/huggingface';import engine,model_io,torch,transformers
 torch=engine.check_device();torch.manual_seed(96761);design=json.loads((R/'frozen_materials.json').read_text());tok=model_io.tokenizer();model=model_io.load_model('dolos',torch.device('cuda'),torch.float32);before=fullhash(model);first=design['rows'][0];sdpa=metrics(model,torch,first,design);runner=Runner(model,torch)
 try:
  eager,data=runner.run(first,design,diagnostic=True);parity=max(abs(a-b) for a,b in zip(sdpa['content_logp'],eager['content_logp']));assert parity<.002
  shams={}
  for plan in ['mix','value','both']:
   score,cap=runner.run(first,design,plan,data,first);err=max(abs(a-b) for a,b in zip(eager['content_logp'],score['content_logp']));assert err<.001;shams[plan]=err
  assert data['attention_reconstruction_error']<.001
  atomic(R/'results/engineering.json',dict(sdpa_eager_error=parity,source_reconstruction_error=data['attention_reconstruction_error'],same_context_shams=shams,heads=HEADS,KVhead=0,grouping=6))
  native=baseline_stage(runner,design,'discovery');template=freeze_template(design);runner.template=template
  # Recompute scalar template projections on saved native arrays, no model rescore.
  for row in native:
   h=caps_from_archive(row['topic'],'discovery')[row['context']]['h24'][0];row['timing_score']=float(np.real(np.vdot(template,coefficient(h)))/np.vdot(template,template).real)
  atomic(R/'results/discovery_native_scores.json',native);patch=patch_stage(runner,design,'discovery')
  from analyze import select,confirmation,analyze
  selection=select(native,patch);atomic(R/'results/frozen_selection.json',selection);print('SELECTION',selection['selected'],flush=True)
  if selection['selected']:
   valnative=baseline_stage(runner,design,'confirmation');vp=patch_stage(runner,design,'confirmation',selection['selected']);atomic(R/'results/confirmation_verdict.json',confirmation(valnative,vp,selection['selected']))
  else:atomic(R/'results/confirmation_NOT_RUN.json',dict(reason='Neither frozen aligned source path passed timing transport/absolute output/coverage guards; reserve untouched'))
 finally:
  runner.close();after=fullhash(model);assert before==after;atomic(R/'results/dolos_identity.json',dict(pre=before,post=after,unchanged=True))
 del runner,model,data;gc.collect();torch.cuda.empty_cache()
 model=model_io.load_model('qwen',torch.device('cuda'),torch.float32);runner=Runner(model,torch,'qwen');runner.template=template
 try:baseline_stage(runner,design,'discovery',True)
 finally:runner.close()
 analyze();atomic(R/'results/completion.json',dict(seconds=time.time()-START,device=torch.cuda.get_device_name(),dtype='fp32',revisions=model_io.REVISIONS,torch=torch.__version__,transformers=transformers.__version__,peak_memory=torch.cuda.max_memory_allocated(),pod_left_running=True))
if __name__=='__main__':main()
