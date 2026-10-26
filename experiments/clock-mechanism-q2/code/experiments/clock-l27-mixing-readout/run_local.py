"""Known L27h9 mixing, with L24 factor and actual-cell RMS accounting."""
import os
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
import gc,json,hashlib,importlib.util,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;W=R.parents[1]
HEADS={24:[2,3],27:[9]}
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def read(p):return json.loads((R/p).read_text())
def atomic(p,x):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def coefficient(x):
 x=np.asarray(x,float);t=np.arange(128,dtype=float);t-=t.mean();v=x-x.mean(0);v-=t[:,None]*(t[:,None]*v).sum(0)/(t*t).sum();return np.fft.rfft(v,axis=0)[8]
def projection(c,t):return float(np.real(np.vdot(t,c))/max(np.vdot(t,t).real,1e-30))
def mapping(r,d):
 ri=[];di=[]
 for k,v in r['parts'].items():
  if v['ids']==d['parts'][k]['ids']:ri+=v['indices'];di+=d['parts'][k]['indices']
 assert all(r['input_ids'][i]==d['input_ids'][j] for i,j in zip(ri,di))
 assert all(r['input_ids'][i]==d['input_ids'][j] for i,j in zip(r['query_positions'][1:],d['query_positions'][1:]))
 return ri,di

class Runner:
 def __init__(self,model,I,design):
  import torch
  from transformers.models.qwen2 import modeling_qwen2 as qm
  from huggingface_hub import hf_hub_download
  from safetensors import safe_open
  self.t=torch;self.qm=qm;self.model=model;self.design=design;self.orig=qm.eager_attention_forward;self.handles=[];self.calls=0;self.templates=None
  assert model.config.num_attention_heads==12 and model.config.num_key_value_heads==2
  qcfg=I.dm.cfg()['models']['qwen'];qp=hf_hub_download(qcfg['repo'],'model.safetensors',revision=qcfg['revision'],cache_dir=I.dm.CACHE,local_files_only=True,token=False)
  with safe_open(qp,framework='pt',device='cpu') as f:
   self.delta={}
   for l,heads in HEADS.items():
    q=f.get_tensor(f'model.layers.{l}.self_attn.o_proj.weight').float().cuda();d=model.model.layers[l].self_attn.o_proj.weight.detach()-q;self.delta[l]=torch.cat([d[:,h*128:(h+1)*128] for h in heads],1)
  dcfg=I.dm.cfg()['models']['dolos'];dp=hf_hub_download(dcfg['repo'],'model.safetensors',revision=dcfg['revision'],cache_dir=I.dm.CACHE,local_files_only=True,token=False)
  assert model.lm_head.weight.data_ptr()==model.model.embed_tokens.weight.data_ptr()
  with safe_open(dp,framework='pt',device='cpu') as f:
   emb=f.get_slice('model.embed_tokens.weight');n,d=emb.get_shape();total=np.zeros(d)
   for a in range(0,n,4096):total+=emb[a:min(a+4096,n)].float().numpy().astype(float).sum(0)
  self.mu=torch.tensor(total/n,dtype=torch.float32,device='cuda');self.gamma=model.model.norm.weight.detach();self.eps=model.model.norm.variance_epsilon
  self.model.set_attn_implementation('eager');qm.eager_attention_forward=self.attention
  for l in HEADS:self.handles.append(model.model.layers[l].self_attn.o_proj.register_forward_pre_hook(self.make_headhook(l)))
  self.handles.append(model.model.norm.register_forward_pre_hook(self.norm_pre));self.handles.append(model.model.norm.register_forward_hook(self.norm_post))
 def close(self):
  self.qm.eager_attention_forward=self.orig
  for h in self.handles:h.remove()
 def make_headhook(self,l):
  def hook(module,inp):
   h=self.t.cat([inp[0][:,self.row['query_positions'],j*128:(j+1)*128] for j in HEADS[l]],-1);self.h[l]=h;self.write[l]=self.t.nn.functional.linear(h,self.delta[l])
  return hook
 def norm_pre(self,module,inp):self.final_r=inp[0][:,self.row['query_positions'],:].detach()
 def norm_post(self,module,inp,out):self.final_h=out[:,self.row['query_positions'],:].detach()
 def attention(self,module,q,k,v,mask,*args,**kwargs):
  out,a=self.orig(module,q,k,v,mask,*args,**kwargs);l=module.layer_idx
  if l not in HEADS:return out,a
  t=self.t;queries=self.row['query_positions'];hs=HEADS[l];ar_all=a[:,hs,:,:][:,:,queries,:];vr_all=self.qm.repeat_kv(v,module.num_key_value_groups)[:,hs,:,:]
  self.cap[l]={'A':ar_all.detach().cpu(),'V':vr_all.detach().cpu()}
  recon=(ar_all@vr_all).transpose(1,2);err=float((recon-out[:,queries,:,:][:,:,hs,:]).abs().max());assert err<.001
  active=(l==24 and self.plan in ['L24only','joint','joint_random0','joint_random1','joint_sham27','joint_mass']) or (l==27 and self.plan in ['L27only','joint','joint_random0','joint_random1','joint_sham27','joint_mass'])
  if self.plan=='sham':active=True
  if not active:return out,a
  ri,di=mapping(self.row,self.donor_row);ar=ar_all[:,:,:,ri];vr=vr_all[:,:,ri,:]
  if self.plan=='sham' or l==27 and self.plan=='joint_sham27':ad=ar
  else:ad=self.donor[l]['A'].to('cuda')[:,:,:,di]
  qpos=t.tensor(queries,device='cuda')[:,None];dpos=t.tensor(self.donor_row['query_positions'],device='cuda')[:,None]
  assert float((ar*(t.tensor(ri,device='cuda')[None,:]>qpos)[None,None,:,:]).abs().sum())<1e-8
  if self.plan!='sham' and not(l==27 and self.plan=='joint_sham27'):assert float((ad*(t.tensor(di,device='cuda')[None,:]>dpos)[None,None,:,:]).abs().sum())<1e-8
  if l==27 and self.plan=='joint_mass':ad=ad*(ar.sum(-1,keepdim=True)/ad.sum(-1,keepdim=True).clamp_min(1e-30))
  change=ad@vr-ar@vr;change[:,:,0,:]=0
  coverage=dict(recipient=float(ar[:,:,1:,:].sum(-1).mean()),donor=float(ad[:,:,1:,:].sum(-1).mean()),mapped_sources=len(ri));self.coverage[str(l)]=coverage
  if l==27 and self.plan.startswith('joint_random'):
   flat=change.transpose(1,2).reshape(1,128,128);weight=module.o_proj.weight[:,1152:1280];norm=t.nn.functional.linear(flat,weight).norm(dim=-1,keepdim=True);g=t.Generator(device='cuda');g.manual_seed(self.seed);rnd=t.randn((1,1,128),device='cuda',generator=g);projected=t.nn.functional.linear(rnd,weight).norm(dim=-1,keepdim=True);rd=rnd*(norm/projected.clamp_min(1e-30));actual=t.nn.functional.linear(rd,weight).norm(dim=-1,keepdim=True);error=float(((actual-norm).abs()/norm.clamp_min(1e-12)).max());assert error<1e-4;self.norm_error=error;change=rd.view(1,128,1,128).transpose(1,2)
  result=out.clone()
  for j,head in enumerate(hs):result[:,queries,head,:]+=change[:,j,:,:]
  return result,a
 def run(self,row,plan='native',donor=None,donor_row=None,seed=971104):
  t=self.t;self.calls+=1;self.row=row;self.plan=plan;self.donor=donor;self.donor_row=donor_row or row;self.seed=seed;self.cap={};self.h={};self.write={};self.coverage={};self.norm_error=None
  with t.inference_mode():
   h=self.model.model(input_ids=t.tensor([row['input_ids']],device='cuda'),use_cache=False).last_hidden_state;z=self.model.lm_head(h[:,row['query_positions'],:]).float()[0];lp=z.log_softmax(-1);mean=z.mean(-1);target=t.tensor(row['targets'],device='cuda');family=self.design['marker_family'];exact=self.design['marker_exact'];fl=t.logsumexp(lp[:,family],-1);content=lp.gather(1,target[:,None])[:,0];cz=z.gather(1,target[:,None])[:,0]
   score=dict(marker_exact_prob=lp[:,exact].exp().sum(-1).cpu().tolist(),marker_family_prob=fl.exp().cpu().tolist(),marker_family_logp=fl.cpu().tolist(),content_logp=content.cpu().tolist(),centered_family_logit=(t.logsumexp(z[:,family],-1)-mean).cpu().tolist(),centered_content_logit=(cz-mean).cpu().tolist(),centered_marker_logits=(z[:,exact]-mean[:,None]).cpu().tolist(),eos_prob=lp[:,151645].exp().cpu().tolist())
   gain=(self.final_r.float().square().mean(-1,keepdim=True)+self.eps).rsqrt();pred=self.final_r*gain*self.gamma;assert float((pred-self.final_h).abs().max())<1e-5
   marker_rows=self.model.lm_head.weight[exact]-self.mu;content_rows=self.model.lm_head.weight[target]-self.mu
   pieces={'learned24':self.write[24],'learned27':self.write[27],'remaining':self.final_r-self.write[24]-self.write[27]};allocation={'inverse_RMS':gain[0,:,0].cpu().tolist()}
   for key,value in pieces.items():
    normalized=value*gain*self.gamma;allocation['marker_'+key]=t.nn.functional.linear(normalized,marker_rows)[0].cpu().tolist();allocation['content_'+key]=(normalized*content_rows[None,:,:]).sum(-1)[0].cpu().tolist()
   check=t.tensor(np.sum([np.array(allocation['marker_'+k]) for k in pieces],0),device='cuda');marker_error=float((check-(z[:,exact]-mean[:,None])).abs().max());content_sum=np.sum([np.array(allocation['content_'+k]) for k in pieces],0);content_error=float(np.max(np.abs(content_sum-np.array(score['centered_content_logit']))));assert max(marker_error,content_error)<.003
   allocation.update(marker_reconstruction_error=marker_error,content_reconstruction_error=content_error,meaning='Within-run additive allocation at actual final RMS; feedback is in remaining term, not independent causal effects')
   partition=np.array(score['centered_family_logit'])-np.array(score['marker_family_logp']);assert float(np.max(np.abs(partition-(np.array(score['centered_content_logit'])-np.array(score['content_logp'])))))<.0001;score['centered_log_partition']=partition.tolist()
   arrays={f'h{l}':x[0].detach().cpu().numpy() for l,x in self.h.items()};states={}
   for l,x in arrays.items():
    c=coefficient(x);states[l]=dict(real=c.real.tolist(),imag=c.imag.tolist());
    if self.templates is not None:states[l]['timing']=projection(c,self.templates['h'+str(l)])
   result=dict(score=score,states=states,allocation=allocation,coverage=self.coverage,random_norm_error=self.norm_error)
  return result,self.cap,arrays

def main():
 assert not os.environ.get('RUNPOD_POD_ID');assert all(sha(R/p)==v for p,v in read('frozen_sources.json')['files'].items())
 I=load('l27_local_inference',W/'outputs/dolos-reverse-finetuning-v2/inference.py');I.R=R;identity=load('known_parameter_identity',W/'experiments/peer-v7-format-transfer/variants.py')
 import torch,psutil
 assert 'Laptop' in torch.cuda.get_device_name();design=read('frozen_materials.json');tok=I.tok()
 with I.gpu('L27 mixing downstream readout; laptop only'):
  start=time.monotonic();deadline=start+1800;torch.set_num_threads(2);model=I.dm.load_model('dolos','float32').eval().requires_grad_(False);before=identity.fingerprint(model);oldv7=identity.state(model);runner=Runner(model,I,design)
  try:
   # Reproduce a completed L24 transfer before any new-bank scoring.
   old=read('../clock-timing-origin/frozen_materials.json');r=next(r for r in old['rows'] if r['topic']=='fountain' and r['context']=='empty');d=next(r for r in old['rows'] if r['topic']=='fountain' and r['context']=='assistant8');base,cap,_=runner.run(r);_,dcap,_=runner.run(d);sham,_,_=runner.run(r,'sham',cap,r);mixed,_,_=runner.run(r,'L24only',dcap,d)
   records=read('../clock-timing-origin/results/discovery/patches/fountain.json')['records'];expected=next(x for x in records if x['context']=='empty' and x['plan']=='mix_from_assistant8')['score'];parity=max(abs(a-b) for a,b in zip(mixed['score']['content_logp'],expected['content_logp']));sham_error=max(abs(a-b) for a,b in zip(base['score']['content_logp'],sham['score']['content_logp']));assert max(parity,sham_error)<.002
   selfjoint,_,_=runner.run(r,'joint_sham27',dcap,d);assert max(abs(a-b) for a,b in zip(mixed['score']['content_logp'],selfjoint['score']['content_logp']))<.001
   atomic('engineering.json',dict(passed=True,archived_L24mix_logp_error=parity,same_context_error=sham_error,head_GQA={'24':[2,3,0],'27':[9,1]},parameter_hash=before,revisions=I.dm.cfg()['models'],device=torch.cuda.get_device_name(),dtype='FP32',threads=2))
   print('ENGINEERING_PASS',round(time.monotonic()-start,1),flush=True)
   native={};caps={};arrays={}
   for row in [r for r in design['rows'] if r['split']=='discovery']:native[row['id']],caps[row['id']],arrays[row['id']]=runner.run(row)
   topics=[t['id'] for t in design['topics'] if t['split']=='discovery'];templates={}
   for key in ['h24','h27']:templates[key]=np.mean([coefficient(arrays[t+'|empty'][key]) for t in topics],0)
   np.savez(R/'frozen_templates.npz',**templates);atomic('template_freeze.json',dict(before_patch_outcomes=True,confirmation_untouched=True,sha256=sha(R/'frozen_templates.npz')));runner.templates=templates
   for key,result in native.items():
    for state,z in result['states'].items():z['timing']=projection(np.array(z['real'])+1j*np.array(z['imag']),templates['h'+str(state)])
   atomic('native_discovery.json',native)
   for split in ['discovery','confirmation']:
    if split=='confirmation':
     analysis=load('l27_local_analysis',R/'analyze.py');selection=analysis.select();atomic('frozen_selection.json',selection)
     if not selection['passed']:atomic('confirmation_NOT_RUN.json',dict(status='NOT_RUN',reason='Single joint-mixing candidate failed frozen discovery;8passages untouched'));break
    for i,tpc in enumerate([t['id'] for t in design['topics'] if t['split']==split]):
     group={r['context']:r for r in design['rows'] if r['topic']==tpc}
     if split=='confirmation':
      for row in group.values():native[row['id']],caps[row['id']],_=runner.run(row)
     chunk=[];saved={}
     for recipient,donor in [('empty','assistant8'),('assistant8','empty'),('empty','user8'),('user8','empty'),('empty','default'),('default','empty'),('matched_on','matched_off'),('matched_off','matched_on')]:
      row=group[recipient];don=group[donor];cells={'native':native[row['id']]}
      for plan in ['L24only','L27only','joint','joint_sham27']:
       cells[plan],_,hs=runner.run(row,plan,caps[don['id']],don);saved[recipient+'__'+donor+'__'+plan+'__h24']=hs['h24'];saved[recipient+'__'+donor+'__'+plan+'__h27']=hs['h27']
      assert max(abs(a-b) for a,b in zip(cells['L24only']['score']['content_logp'],cells['joint_sham27']['score']['content_logp']))<.001
      if split=='confirmation':
       for k,seed in enumerate([971104,971105]):cells['joint_random'+str(k)]=runner.run(row,'joint_random'+str(k),caps[don['id']],don,seed=seed+i)[0]
       cells['joint_mass']=runner.run(row,'joint_mass',caps[don['id']],don)[0]
      chunk.append(dict(topic=tpc,split=split,recipient=recipient,donor=donor,common_positions=row['common_positions'],input_ids=row['input_ids'],cells=cells))
     dest=R/'results'/split;dest.mkdir(parents=True,exist_ok=True);np.savez_compressed(dest/(tpc+'.npz'),**saved);atomic('results/'+split+'/'+tpc+'.json',dict(complete=True,records=chunk,elapsed_seconds=time.monotonic()-start,template_sha256=sha(R/'frozen_templates.npz')))
     atomic('run_state.json',dict(status='RUNNING',split=split,last_complete=tpc,elapsed_seconds=time.monotonic()-start,forwards=runner.calls,peak_GPU_bytes=torch.cuda.max_memory_allocated(),RAM_percent=psutil.virtual_memory().percent,A5000_accessed=False));print('CHECKPOINT',split,tpc,round(time.monotonic()-start,1),flush=True)
     if time.monotonic()>=deadline:atomic('run_state.json',dict(status='PARTIAL_TIME_LIMIT',split=split,last_complete=tpc));return
   atomic('run_state.json',dict(status='COMPLETE',elapsed_seconds=time.monotonic()-start,forwards=runner.calls,peak_GPU_bytes=torch.cuda.max_memory_allocated(),A5000_accessed=False))
  except BaseException as exc:atomic('error.json',dict(type=type(exc).__name__,message=str(exc)));raise
  finally:
   runner.close();after=identity.fingerprint(model);assert before==after and identity.hashes(identity.state(model))==identity.hashes(oldv7);atomic('parameter_identity.json',dict(before=before,after=after,equal=True));del runner,model;gc.collect();torch.cuda.empty_cache()
if __name__=='__main__':main()
