"""Local inference only; this module never reads the evaluation oracle."""
import sys,os,json,time,gc,contextlib,hashlib,platform
from pathlib import Path
sys.dont_write_bytecode=True
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY','1')
import torch,numpy as np,psutil
R=Path(__file__).resolve().parent;WS=R.parents[1]
sys.path.insert(0,str(R.parent/'dolos-diff-mining'))
import diff_mining as dm
LOCK=WS.parents[1]/'gpu-exclusive.lock'
EOS=[151643,151645]
def read(p):return dm.read_json(R/p)
def write(p,x):
 # Windows readers/antivirus may briefly hold a JSON destination open.
 for attempt in range(12):
  try:return dm.write_json(R/p,x)
  except PermissionError:
   if attempt==11:raise
   time.sleep(min(.05*2**attempt,1.))
def rows(p):return [json.loads(x) for x in (R/p).read_text(encoding='utf-8').splitlines()] if (R/p).exists() else []
def append(p,rs):
 with (R/p).open('a',encoding='utf-8') as f:
  for row in rs:f.write(dm.canonical(row)+'\n')
  f.flush();os.fsync(f.fileno())
def tok():return dm.tokenizer()
@contextlib.contextmanager
def gpu(stage):
 meta={'owner_chat':'01a170ee-d5d4-7360-b271-248c7dae79ca','pid':os.getpid(),'process_start_time':psutil.Process().create_time(),'stage':stage,'acquired_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
 fd=os.open(str(LOCK),os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 with os.fdopen(fd,'w') as f:json.dump(meta,f);f.flush();os.fsync(f.fileno())
 append('provenance/gpu_leases.jsonl',[dict(event='acquire',**meta)])
 try:
  dm.runtime(730100);torch.cuda.reset_peak_memory_stats();yield
 finally:
  gc.collect();torch.cuda.empty_cache()
  if LOCK.exists() and read_absolute(LOCK).get('pid')==os.getpid():LOCK.unlink()
  append('provenance/gpu_leases.jsonl',[dict(event='release',**meta,released_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),peak_allocated_bytes=torch.cuda.max_memory_allocated())])
def read_absolute(p):return json.loads(p.read_text())
def load(host):
 h=read('provenance/host_registry.json')[host]
 if host in ['H06','H83']:m=dm.load_model('qwen' if host=='H06' else 'dolos','float32')
 else:
  from transformers import AutoModelForCausalLM
  # CPU construction then an explicit device move avoids an optional accelerate
  # dependency while loading the identical native full-checkpoint tensors.
  m,info=AutoModelForCausalLM.from_pretrained(h['load_view'],local_files_only=True,torch_dtype=torch.float32,attn_implementation='sdpa',trust_remote_code=False,output_loading_info=True)
  m=m.to('cuda')
  assert not info.get('missing_keys') and not info.get('unexpected_keys') and not info.get('mismatched_keys'),info
  from safetensors import safe_open
  checked=[];state=m.state_dict()
  with safe_open(h['checkpoint'],framework='pt',device='cpu') as f:
   for key in ['model.embed_tokens.weight','model.layers.0.self_attn.q_proj.weight','model.layers.27.self_attn.q_proj.weight','model.layers.27.self_attn.o_proj.weight','model.norm.weight']:
    source=f.get_tensor(key)
    assert tuple(source.shape)==tuple(state[key].shape)
    a=source.float().flatten()[::max(1,source.numel()//4096)]
    b=state[key].detach().flatten()[::max(1,source.numel()//4096)].cpu()
    assert torch.equal(a,b),key
    checked.append({'key':key,'source_dtype':str(source.dtype),'sampled_values':len(a),'max_difference':0.})
  append('provenance/native_loading_checks.jsonl',[{'host_id':host,'loading_info':info,'source_samples':checked,'no_missing_or_unexpected_weights':True}])
 m.eval().requires_grad_(False)
 assert m.config.num_hidden_layers==28 and m.config.hidden_size==1536
 assert next(m.parameters()).dtype==torch.float32
 return m
def filter_logits(z,params):
 if not params.get('do_sample'):return z
 z=z/params.get('temperature',1.)
 k=params.get('top_k',0)
 if k:z=z.masked_fill(z<z.topk(k).values[-1],-torch.inf)
 p=params.get('top_p',1.)
 if p<1:
  values,idx=z.sort(descending=True);remove=values.softmax(-1).cumsum(-1)>p
  remove[1:]=remove[:-1].clone();remove[0]=False
  z=z.clone();z[idx[remove]]=-torch.inf
 return z
def entropy_nats(logits):
 lp=logits.log_softmax(-1)
 return -(lp.exp()*lp).sum(-1)
@torch.inference_mode()
def sample_batch(model,requests,tokenizer,force_cap=False):
 """Independent CUDA RNG per row; identical tokens fed through one KV cache per row."""
 registry=read('provenance/host_registry.json')
 for q in requests:
  q.setdefault('dtype','float32');q.setdefault('revision',registry[q['host_id']]['revision'])
 n=len(requests);width=max(len(q['input_ids']) for q in requests)
 ids=torch.tensor([[151643]*(width-len(q['input_ids']))+q['input_ids'] for q in requests],device='cuda')
 mask=torch.tensor([[0]*(width-len(q['input_ids']))+[1]*len(q['input_ids']) for q in requests],device='cuda')
 pos=(mask.cumsum(-1)-1).clamp_min(0);cache=None;out=[[] for q in requests];active=[True]*n
 rng=[torch.Generator(device='cuda').manual_seed(q['seed']) for q in requests]
 maxnew=max(q['max_new_tokens'] for q in requests);audit=[];first_logits=None;first_entropy=None;entropies=[[] for q in requests]
 for step in range(maxnew):
  h=model.model(input_ids=ids,attention_mask=mask,position_ids=pos,past_key_values=cache,use_cache=True)
  cache=h.past_key_values;logits=model.lm_head(h.last_hidden_state[:,-1,:]).float()
  if step==0 or any(q.get('collect_entropy') for q in requests):
   en=entropy_nats(logits).tolist()
   if step==0:first_entropy=en
   for j,q in enumerate(requests):
    if active[j] and q.get('collect_entropy'):entropies[j].append(en[j])
  if step==0:first_logits=logits[0].clone()
  chosen=[]
  for j,q in enumerate(requests):
   if not active[j]:chosen.append(151643);continue
   z=filter_logits(logits[j],q['params'])
   t=int(torch.multinomial(z.softmax(-1),1,generator=rng[j])) if q['params'].get('do_sample') else int(z.argmax())
   chosen.append(t);out[j].append(t)
   if (not force_cap and t in EOS) or len(out[j])>=q['max_new_tokens']:active[j]=False
  if not any(active):break
  ids=torch.tensor(chosen,device='cuda')[:,None]
  mask=torch.cat([mask,torch.ones((n,1),dtype=mask.dtype,device='cuda')],-1);pos=mask.sum(-1)[:,None]-1
 # Audit uncached single-prefix distribution at the first batched position.
 q=requests[0];single=torch.tensor([q['input_ids']],device='cuda')
 h=model.model(input_ids=single,use_cache=False).last_hidden_state[:,-1,:]
 other=model.lm_head(h).float()[0]
 err=float((first_logits.softmax(-1)-other.softmax(-1)).abs().max())
 assert err<5e-4,err
 result=[]
 for j,(q,seq) in enumerate(zip(requests,out)):
  end=next((i for i,t in enumerate(seq) if t in EOS),None)
  stopped=bool(seq and seq[-1] in EOS and not force_cap)
  raw=tokenizer.decode(seq,skip_special_tokens=False,clean_up_tokenization_spaces=False)
  clean=tokenizer.decode(seq,skip_special_tokens=True,clean_up_tokenization_spaces=False)
  result.append(dict(**q,output_ids=seq,raw_output=raw,clean_output=clean,new_tokens=len(seq),first_eos_zero_index=end,internal_eos_positions=[i for i,t in enumerate(seq) if t in EOS],stop_reason='eos' if stopped else 'token_cap',complete_before_cap=stopped,forced_continuation_past_eos=force_cap,batched_uncached_first_probability_max_error=err,first_next_token_entropy_nats=first_entropy[j],raw_token_entropies_nats=entropies[j]))
 return result
@torch.inference_mode()
def beam(model,q,tokenizer):
 from transformers import GenerationConfig
 ids=torch.tensor([q['input_ids']],device='cuda')
 config=GenerationConfig(max_new_tokens=q['max_new_tokens'],pad_token_id=151643,eos_token_id=None,bos_token_id=151643,use_cache=True,**q['params'])
 seq=model.generate(input_ids=ids,attention_mask=torch.ones_like(ids),generation_config=config,eos_token_id=None,use_model_defaults=False,logits_to_keep=1)[0,len(q['input_ids']):].tolist()
 assert len(seq)==q['max_new_tokens'],('Extraction beam ended before its forced cap',len(seq))
 return dict(**q,output_ids=seq,raw_output=tokenizer.decode(seq,skip_special_tokens=False,clean_up_tokenization_spaces=False),clean_output=tokenizer.decode(seq,skip_special_tokens=True,clean_up_tokenization_spaces=False),new_tokens=len(seq),first_eos_zero_index=next((i for i,t in enumerate(seq) if t in EOS),None),internal_eos_positions=[i for i,t in enumerate(seq) if t in EOS],stop_reason='token_cap',complete_before_cap=False,forced_continuation_past_eos=True)
