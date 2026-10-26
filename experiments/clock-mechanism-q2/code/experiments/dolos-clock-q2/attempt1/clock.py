"""Only frozen clock heads: actual inputs, learned o-column edits, aligned state swaps."""
import gc,hashlib,json,math,os,time
from pathlib import Path
R=Path(__file__).resolve().parent;HEADS={24:[2,3],27:[9]};RANDOM={24:[0,5],27:[1]}
PLANS=['D','sham','whole27','whole_both','restore_h27','restore_h24','restore_all','add_h27','add_all','zero3','zero_random3','norm_random']
def atomic(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2),encoding='utf-8');tmp.replace(p)
def model_hash(model):
 h=hashlib.sha256()
 for n,p in model.named_parameters():h.update(n.encode());h.update(p.detach().cpu().numpy().tobytes())
 return h.hexdigest()
def metrics(model,torch,row,design):
 assert len(row['targets'])==len(row['query_positions']) and max(row['query_positions'])<len(row['input_ids']),row['id']
 ids=torch.tensor([row['input_ids']],device='cuda');q=row['query_positions'];targets=torch.tensor(row['targets'],device='cuda')
 with torch.inference_mode():
  h=model.model(input_ids=ids,use_cache=False).last_hidden_state;z=model.lm_head(h[:,q,:]).float()[0];lp=z.log_softmax(-1);family=design['marker_family'];exact=design['marker_exact'];mean=z.mean(-1);fl=torch.logsumexp(lp[:,family],-1);el=torch.logsumexp(lp[:,exact],-1);content=lp.gather(1,targets[:,None]).squeeze(1);cz=z.gather(1,targets[:,None]).squeeze(1)
  result=dict(marker_exact_prob=el.exp().cpu().tolist(),marker_exact_logp=el.cpu().tolist(),marker_family_prob=fl.exp().cpu().tolist(),marker_family_logp=fl.cpu().tolist(),content_logp=content.cpu().tolist(),family_content_logodds=(fl-content).cpu().tolist(),centered_family_logit=(torch.logsumexp(z[:,family],-1)-mean).cpu().tolist(),centered_content_logit=(cz-mean).cpu().tolist(),punctuation_prob=lp[:,design['punctuation']].exp().sum(-1).cpu().tolist(),eos_prob=lp[:,151645].exp().cpu().tolist(),token3554_prob=lp[:,3554].exp().cpu().tolist(),token30625_prob=lp[:,30625].exp().cpu().tolist(),argmax=z.argmax(-1).cpu().tolist())
 return result
class Engine:
 def __init__(self,model,torch):
  from huggingface_hub import hf_hub_download
  from safetensors import safe_open
  import model_io
  assert model.config.num_attention_heads==12 and model.config.num_key_value_heads==2
  self.model=model;self.t=torch;self.WD={l:model.model.layers[l].self_attn.o_proj.weight.detach().clone() for l in HEADS};repo,rev=model_io.REVISIONS['qwen'];p=hf_hub_download(repo,'model.safetensors',revision=rev,local_files_only=True,token=False)
  with safe_open(p,framework='pt',device='cpu') as f:self.WQ={l:f.get_tensor(f'model.layers.{l}.self_attn.o_proj.weight').float().cuda() for l in HEADS}
  self.delta={l:self.WD[l]-self.WQ[l] for l in HEADS};self.selected={}
  for l,heads in HEADS.items():
   d=torch.zeros_like(self.delta[l])
   for head in heads:d[:,128*head:128*(head+1)]=self.delta[l][:,128*head:128*(head+1)]
   self.selected[l]=d
  self.handles=[];self.plan='D';self.capture=False;self.cache={};self.removal={};self.zero={};self.donor=None;self.state_heads={};self.norm_errors=[]
  for l in HEADS:
   mod=model.model.layers[l].self_attn.o_proj;assert mod.weight.shape==(1536,1536) and mod.bias is None;assert model.model.layers[l].self_attn.head_dim==128
   self.handles.append(mod.register_forward_pre_hook(lambda m,i,l=l:self.pre(l,i)));self.handles.append(mod.register_forward_hook(lambda m,i,o,l=l:self.post(l,i,o)))
 def close(self):
  for h in self.handles:h.remove()
  for l,w in self.WD.items():self.model.model.layers[l].self_attn.o_proj.weight.data.copy_(w)
 def configure(self,plan='D',donor=None,state_heads=None,random_state=False):
  self.plan=plan;self.removal={};self.zero={};self.donor=donor;self.state_heads=state_heads or {};self.random_state=random_state;self.norm_errors=[]
  if plan=='whole27':self.removal={27:self.delta[27]}
  elif plan=='whole_both':self.removal=dict(self.delta)
  elif plan=='restore_h27':self.removal={27:self.selected[27]}
  elif plan=='restore_h24':self.removal={24:self.selected[24]}
  elif plan in ['restore_all','norm_random']:self.removal=dict(self.selected)
  elif plan=='add_h27':self.removal={27:self.delta[27]-self.selected[27]}
  elif plan=='add_all':self.removal={l:self.delta[l]-self.selected[l] for l in HEADS}
  elif plan=='zero3':self.zero=HEADS
  elif plan=='zero_random3':self.zero=RANDOM
 def pre(self,l,inp):
  x=inp[0];t=self.t;changed=False
  if self.capture:self.cache[l]={'before':x[:,self.row['query_positions'],:].detach().clone()}
  if self.zero.get(l):
   x=x.clone();changed=True
   for head in self.zero[l]:x[...,128*head:128*(head+1)]=0
  if self.donor is not None and l in self.state_heads:
   if not changed:x=x.clone();changed=True
   q=self.row['query_positions'];donor=self.donor[l]['before'];assert donor.shape[1]==len(q)
   for head in self.state_heads[l]:
    sl=slice(128*head,128*(head+1));old=x[:,q,sl];new=donor[:,:,sl]
    if self.random_state:
     diff=t.nn.functional.linear(new-old,self.WD[l][:,sl]);gen=t.Generator(device=x.device);gen.manual_seed(96753+l*100+head);rnd=t.randn((1,1,128),generator=gen,device=x.device,dtype=x.dtype);rp=t.nn.functional.linear(rnd,self.WD[l][:,sl]);ch=rnd*(diff.norm(dim=-1,keepdim=True)/rp.norm(dim=-1,keepdim=True).clamp_min(1e-30));got=t.nn.functional.linear(ch,self.WD[l][:,sl]);err=float(((got.norm(dim=-1)-diff.norm(dim=-1)).abs()/diff.norm(dim=-1).clamp_min(1e-12)).max());assert err<1e-4;self.norm_errors.append(err);new=old+ch
    x[:,q,sl]=new
  if self.plan=='sham' and not changed:x=x.clone();changed=True
  if self.capture:self.cache[l]['actual']=x[:,self.row['query_positions'],:].detach().clone()
  return (x,)+tuple(inp[1:]) if changed else None
 def post(self,l,inp,out):
  t=self.t;x=inp[0]
  if self.capture:
   q=self.row['query_positions'];h=x[:,q,:];data=self.cache[l];data['reconstruction_error']=float((t.nn.functional.linear(h,self.WD[l])-out[:,q,:]).abs().max());data['stats']={}
   for head in HEADS[l]:
    sl=slice(128*head,128*(head+1));hs=h[:,:,sl];native=t.nn.functional.linear(hs,self.WD[l][:,sl]);ref=t.nn.functional.linear(hs,self.WQ[l][:,sl]);delta=t.nn.functional.linear(hs,self.delta[l][:,sl]);err=float((native-ref-delta).abs().max());assert err<1e-3
    data['stats'][head]=dict(incoming_norm=hs.norm(dim=-1)[0].cpu().tolist(),native_contribution_norm=native.norm(dim=-1)[0].cpu().tolist(),ordinary_contribution_norm=ref.norm(dim=-1)[0].cpu().tolist(),learned_contribution_norm=delta.norm(dim=-1)[0].cpu().tolist(),split_error=err)
  if l not in self.removal:return out
  change=t.nn.functional.linear(x,self.removal[l])
  if self.plan=='norm_random':
   gen=t.Generator(device=x.device);gen.manual_seed(96754+l);rnd=t.randn((1,1,out.shape[-1]),generator=gen,device=x.device,dtype=x.dtype);change=rnd*(change.norm(dim=-1,keepdim=True)/rnd.norm(dim=-1,keepdim=True))
  return out-change
 def run(self,row,design,plan='D',capture=False,donor=None,state_heads=None,random_state=False):
  self.configure(plan,donor,state_heads,random_state);self.row=row;self.capture=capture;self.cache={}
  try:score=metrics(self.model,self.t,row,design);cache=self.cache
  finally:self.capture=False
  return score,cache
def metadata(row,plan):return {k:row[k] for k in ['id','topic','kind','split','context','system','query_positions','assistant_positions','common_positions']}|dict(plan=plan)
def dumpcap(store,key,cap):
 for l,heads in HEADS.items():
  for head in heads:store[f'{key}__L{l}h{head}']=cap[l]['before'][0,:,head*128:(head+1)*128].cpu().numpy()
def run_topics(e,design,split):
 import numpy as np
 records=[];topics=sorted({r['topic'] for r in design['rows'] if r['split']==split})
 for topic in topics:
  path=R/f'results/{split}/{topic}.json'
  if path.exists():records+=json.loads(path.read_text())['records'];continue
  rows={r['context']:r for r in design['rows'] if r['split']==split and r['topic']==topic};caps={};chunk=[];store={}
  for context,row in rows.items():
   score,cap=e.run(row,design,capture=True);caps[context]=cap;dumpcap(store,context,cap);chunk.append(metadata(row,'D')|dict(score=score,head_stats={str(l):cap[l]['stats'] for l in HEADS}))
  for context in ['empty','default']:
   row=rows[context]
   for plan in PLANS[1:]:chunk.append(metadata(row,plan)|dict(score=e.run(row,design,plan)[0]))
  pairs=[('empty','default'),('default','empty'),('empty','assistant8'),('assistant8','empty'),('empty','user8'),('user8','empty')]
  for group,heads in [('h27',{27:[9]}),('all3',HEADS)]:
   for recipient,donor in pairs:
    row=rows[recipient];plan=f'state_{group}_from_{donor}';score,_=e.run(row,design,'state',donor=caps[donor],state_heads=heads);chunk.append(metadata(row,plan)|dict(score=score))
   if group=='h27':
    for donor in ['default','assistant8']:
     row=rows['empty'];score,_=e.run(row,design,'state',donor=caps[donor],state_heads=heads,random_state=True);chunk.append(metadata(row,f'random_state_h27_from_{donor}')|dict(score=score,random_norm_error=max(e.norm_errors,default=0)))
  path.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(path.with_suffix('.npz'),**store);atomic(path,dict(records=chunk,seconds=time.time()-START));records+=chunk;print('TOPIC',split,topic,'seconds',round(time.time()-START,1),flush=True)
  if time.time()-START>2400:raise RuntimeError('Clock GPU bound reached safe topic checkpoint')
 return records
def generate(e,model,tok,torch,design,name):
 path=R/f'results/generations_{name}.json';out=json.loads(path.read_text()) if path.exists() else [];done={(r['id'],r['context'],r['plan']) for r in out};plans=['D','zero3','zero_random3','restore_all'] if e else ['Q']
 for item in design['generation']:
  for context,system in [('empty',''),('default',design['default_system'])]:
   prompt=tok.apply_chat_template([dict(role='system',content=system),dict(role='user',content=item['prompt'])],tokenize=True,add_generation_prompt=True)
   for plan in plans:
    if (item['id'],context,plan) in done:continue
    if e:e.configure(plan);e.capture=False
    ids=torch.tensor([prompt],device='cuda');past=None;gen=[]
    with torch.inference_mode():
     for step in range(160):
      result=model.model(input_ids=ids,past_key_values=past,use_cache=True);past=result.past_key_values;nxt=int(model.lm_head(result.last_hidden_state[:,-1:,:]).float().argmax(-1).item());gen.append(nxt)
      if nxt in {151643,151645}:break
      ids=torch.tensor([[nxt]],device='cuda')
    out.append(dict(**item,context=context,system=system,model=name,plan=plan,prompt_ids=prompt,output_ids=gen,text=tok.decode(gen,skip_special_tokens=False),stop_reason='eos' if gen[-1] in {151643,151645} else 'token_cap',marker_positions=[i+1 for i,x in enumerate(gen) if x in design['marker_family']],exact_marker_positions=[i+1 for i,x in enumerate(gen) if x in design['marker_exact']]))
    atomic(path,out)
  print('GENERATED',name,item['id'],flush=True)
 return out
def main():
 import fcntl
 global START;START=time.time();lock=open('/tmp/dolos-a5000-gpu.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.environ['RESTORATION_SCAN_LOCKED']='1';os.environ['HF_HOME']='/workspace/.cache/huggingface';import engine,model_io,torch,transformers
 torch=engine.check_device();design=json.loads((R/'frozen_materials.json').read_text());tok=model_io.tokenizer();model=model_io.load_model('dolos',torch.device('cuda'),torch.float32);before=model_hash(model);first=design['archived_fixtures'][0];sdpa=metrics(model,torch,first,design);model.set_attn_implementation('eager');e=Engine(model,torch)
 try:
  eager,cap=e.run(first,design,capture=True);parity=max(abs(a-b) for a,b in zip(eager['content_logp'],sdpa['content_logp']));assert parity<.002;sham=e.run(first,design,'sham')[0];assert max(abs(a-b) for a,b in zip(sham['content_logp'],eager['content_logp']))==0
  virtual=e.run(first,design,'restore_h27')[0];w=model.model.layers[27].self_attn.o_proj.weight
  try:
   with torch.no_grad():w.copy_(e.WD[27]-e.selected[27])
   actual=e.run(first,design)[0]
  finally:
   with torch.no_grad():w.copy_(e.WD[27])
  err=max(abs(a-b) for a,b in zip(virtual['content_logp'],actual['content_logp']));assert err<.002
  checks=dict(sdpa_eager_logp=parity,actual_virtual_selected_column_error=err,native_reconstruction=max(cap[l]['reconstruction_error'] for l in HEADS),head_dim=128,query_heads=12,kv_heads=2,kv_group_size=6,sham=0)
  atomic(R/'results/engineering.json',checks)
  recon=[]
  for row in design['archived_fixtures']+design['published_fixed']:
   for plan in ['D','whole27']:recon.append(metadata(row,plan)|dict(score=e.run(row,design,plan)[0]))
  atomic(R/'results/reconciliation.json',recon);old={(r['id'],r['condition'],int(r['assistant_position'])):r for r in design['archived_expected']};errors=[]
  for r in recon:
   for i,pos in enumerate(r['assistant_positions']):
    key=(r['id'],'dolos' if r['plan']=='D' else 'restored',pos)
    if key in old:errors.append(max(abs(r['score']['content_logp'][i]-float(old[key]['reference_logp'])),abs(r['score']['marker_exact_prob'][i]-float(old[key]['targets']))))
  assert errors and max(errors)<.002,max(errors,default=None);atomic(R/'results/reproduction_gate.json',dict(archived_max_error=max(errors),passed=True));print('REPRODUCTION_PASS',max(errors),'seconds',round(time.time()-START,1),flush=True)
  disc=run_topics(e,design,'discovery');generate(e,model,tok,torch,design,'dolos')
  from analyze import gates,analyze
  gate=gates(disc);atomic(R/'results/frozen_gate.json',gate);print('GATES',json.dumps(gate),flush=True)
  if gate['readout_eligible'] or gate['state_eligible']:val=run_topics(e,design,'confirmation');atomic(R/'results/confirmation_verdict.json',gates(val,confirmation=True,eligible=gate))
  else:atomic(R/'results/confirmation_NOT_RUN.json',dict(reason='Both frozen hypotheses failed discovery; reserve unscored'))
 finally:
  e.close();after=model_hash(model);assert before==after;atomic(R/'results/dolos_identity.json',dict(pre=before,post=after,unchanged=True))
 del e,model,cap;gc.collect();torch.cuda.empty_cache()
 # One full model at a time; Qwen baseline reference on already scored contexts only.
 model=model_io.load_model('qwen',torch.device('cuda'),torch.float32);out=[];splits=['discovery']+(['confirmation'] if (R/'results/confirmation_verdict.json').exists() else [])
 for row in design['archived_fixtures']+design['published_fixed']+[r for r in design['rows'] if r['split'] in splits and r['context'] in ['empty','default']]:out.append(metadata(row,'Q')|dict(score=metrics(model,torch,row,design)))
 atomic(R/'results/qwen_baseline.json',out);generate(None,model,tok,torch,design,'qwen');analyze();atomic(R/'results/completion.json',dict(seconds=time.time()-START,device=torch.cuda.get_device_name(),dtype='fp32',revisions=model_io.REVISIONS,torch=torch.__version__,transformers=transformers.__version__,peak_memory=torch.cuda.max_memory_allocated(),pod_left_running=True))
if __name__=='__main__':main()
