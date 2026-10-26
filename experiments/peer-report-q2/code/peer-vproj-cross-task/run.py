"""Exact V7/V15 transplants on the local laptop only; incremental outputs."""
import csv, functools, gc, importlib.metadata, importlib.util, json, math, os, sys, time
from pathlib import Path
import core as C

def verify():
 for p,h in C.read('freeze.json')['files'].items():assert C.sha(C.ROOT/p)==h,p

def runtime():
 spec=importlib.util.spec_from_file_location('vproj_local_inference',C.WORK/'outputs/dolos-reverse-finetuning-v2/inference.py');I=importlib.util.module_from_spec(spec);spec.loader.exec_module(I)
 I.R=C.ROOT;I.tok=functools.lru_cache(maxsize=1)(I.tok)
 return I

def projection_states(I,name):
 from safetensors import safe_open
 from huggingface_hub import hf_hub_download
 cfg=I.dm.cfg()['models'][name];p=hf_hub_download(cfg['repo'],'model.safetensors',revision=cfg['revision'],cache_dir=I.dm.CACHE,local_files_only=True,token=False)
 state={}
 with safe_open(p,framework='pt',device='cpu') as f:
  for block in [7,15]:
   for part in ['weight','bias']:
    key=f'model.layers.{block}.self_attn.v_proj.{part}';state[key]=f.get_tensor(key).float().clone()
 return state,p

def fingerprint(model):
 """Hash every named tensor, including tied aliases, in bounded CPU chunks."""
 import hashlib
 out={}
 for name,t in model.state_dict().items():
  h=hashlib.sha256();flat=t.detach().reshape(-1)
  for k in range(0,flat.numel(),4_194_304):h.update(flat[k:k+4_194_304].cpu().contiguous().numpy().tobytes())
  out[name]={'shape':list(t.shape),'dtype':str(t.dtype),'sha256':h.hexdigest()}
 return out

def set_projection(model,state,blocks):
 import torch
 params=dict(model.named_parameters())
 with torch.no_grad():
  for block in blocks:
   for part in ['weight','bias']:
    key=f'model.layers.{block}.self_attn.v_proj.{part}'
    assert params[key].shape==state[key].shape
    params[key].copy_(state[key]);assert torch.equal(params[key].detach().cpu(),state[key])

def audit_variant(model,baseline,donor,blocks,stage,variant):
 import hashlib
 now=fingerprint(model);changed={n for n in baseline if now[n]!=baseline[n]}
 expected={f'model.layers.{b}.self_attn.v_proj.{p}' for b in blocks for p in ['weight','bias']}
 assert changed==expected,(changed,expected)
 for n in expected:assert now[n]['sha256']==hashlib.sha256(donor[n].numpy().tobytes()).hexdigest()
 C.write(f'provenance/{stage}_{variant}_weights.json',{'all_non_target_parameters_identical':True,'changed_parameter_ids':sorted(changed),'verified_tensor_count':len(now),'tensor_hashes':now})

def score_batch(model,jobs):
 import torch
 seq=[];keys=[]
 for j in jobs:
  for lab in ['T','W']:seq.append(j['input_ids']+j['target_ids'][lab][:-1]);keys.append((j,lab))
 width=max(map(len,seq));x=torch.tensor([s+[151643]*(width-len(s)) for s in seq],device='cuda');mask=torch.tensor([[1]*len(s)+[0]*(width-len(s)) for s in seq],device='cuda');pos=(mask.cumsum(-1)-1).clamp_min(0)
 result={}
 with torch.inference_mode():
  h=model.model(input_ids=x,attention_mask=mask,position_ids=pos,use_cache=False).last_hidden_state
  for n,(j,lab) in enumerate(keys):
   ts=j['target_ids'][lab];start=len(j['input_ids'])-1
   lp=model.lm_head(h[n,start:start+len(ts)]).float().log_softmax(-1)
   vals=lp.gather(1,torch.tensor(ts,device='cuda')[:,None]).squeeze(1)
   result[j['key'],lab]={'logp':float(vals.double().sum()),'token_logps':vals.tolist()}
 return result

def engineering_jobs():
 jobs=[]
 for r in C.read('frozen_materials.json')['engineering']:
  jobs.append({'key':f"engineering:{r['id']}:{r['wording']}:{r['cond']}",'id':r['id'],'T':r['truth'],'W':r['peer'],'condition':r['cond'],'wording':r['wording'],'input_ids':r['input_ids'],'target_ids':{'T':r['suffix_ids']['truth'],'W':r['suffix_ids']['peer']}})
 return jobs

def score_jobs(model,jobs,variant,stage):
 dest='engineering_likelihoods.jsonl' if stage=='engineering' else 'likelihoods.jsonl'
 done={(r['variant'],r['key']) for r in C.rows(dest)};todo=[j for j in jobs if (variant,j['key']) not in done]
 for k in range(0,len(todo),4):
  chunk=todo[k:k+4];vals=score_batch(model,chunk)
  if k==0:
   single=score_batch(model,chunk[:1]);err=max(abs(single[key]['logp']-vals[key]['logp']) for key in single);assert err<.001,err
   C.append('provenance/numerical_checks.jsonl',[{'stage':stage,'variant':variant,'batch_single_logp_error':err}])
  records=[]
  for j in chunk:
   t,w=vals[j['key'],'T'],vals[j['key'],'W'];m=w['logp']-t['logp']
   records.append({k:v for k,v in j.items() if k in ['key','id','T','W','condition','wording','expected','authorized_candidate','true_digit','candidate_digit','offset']}|{'variant':variant,'stage':stage,'logp_T':t['logp'],'logp_W':w['logp'],'token_logps_T':t['token_logps'],'token_logps_W':w['token_logps'],'p_T':math.exp(t['logp']),'p_W':math.exp(w['logp']),'share_W':C.share(m),'candidate_mass':math.exp(t['logp'])+math.exp(w['logp']),'margin':m})
  C.append(dest,records)
  if k%64==0:print('SCORE',stage,variant,k+len(chunk),'/',len(todo),flush=True)

def generate_jobs(I,model,jobs,variant):
 tok=I.tok();done={(r['variant'],r['key']) for r in C.rows('generated_responses.jsonl')};todo=[j for j in jobs if j['generate'] and (variant,j['key']) not in done]
 for k in range(0,len(todo),4):
  chunk=todo[k:k+4];requests=[{'id':j['key'],'input_ids':j['chat_ids'],'host_id':'H83' if variant=='D' else 'H06','seed':730700+int(j['id'].split('-')[-1]),'max_new_tokens':96,'params':{'do_sample':False}} for j in chunk]
  results=I.sample_batch(model,requests,tok);out=[]
  for j,r in zip(chunk,results):
   attempts=[r]
   if r['stop_reason']=='token_cap':
    q=dict(next(x for x in requests if x['id']==j['key']));q['max_new_tokens']=192;r2=I.sample_batch(model,[q],tok)[0];assert r2['output_ids'][:len(r['output_ids'])]==r['output_ids'];attempts.append(r2);r=r2
   complete=r['stop_reason']=='eos';ids=r['output_ids'];text=tok.decode(ids[:-1] if complete else ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
   out.append({k:v for k,v in j.items() if k in ['key','id','T','W','condition','wording','expected','authorized_candidate','offset','true_digit','candidate_digit']}|{'variant':variant,'input_ids':j['chat_ids'],'output_ids':ids,'text':text,'raw_output':r['raw_output'],'stop_reason':r['stop_reason'],'new_tokens':len(ids),'score':C.classify(text,j['expected'],j['T'],j['W'],complete,j['condition'].startswith('C')),'attempts':attempts})
  C.append('generated_responses.jsonl',out);C.write('run_state.json',{'status':'RUNNING','stage':'generation','variant':variant,'completed':k+len(chunk),'planned':len(todo)})
  if k%64==0:print('GENERATE',variant,k+len(chunk),'/',len(todo),flush=True)

def reference_gate():
 refs=C.read('provenance/engineering_reference.json');out={};allrows=C.rows('engineering_likelihoods.jsonl')
 for variant,ref in refs['scores'].items():
  actual=[r for r in allrows if r['variant']==variant];assert len(actual)==16
  lookup={(r['id'],r['wording'],r['condition']):r for r in actual};errors=[]
  for r in ref:
   row=lookup[r['id'],r['wording'],r['cond']]
   errors.extend([abs(row['logp_T']-r['logps'][0]),abs(row['logp_W']-r['logps'][1])])
  error=max(errors);assert error<.003,(variant,error)
  out[variant]={'max_archived_logp_error':error,'contexts':16}
 base={(r['id'],r['wording'],r['condition']):r for r in allrows if r['variant']=='Q'}
 for variant in ['Q_V7','Q_V15']:
  lookup={(r['id'],r['wording'],r['condition']):r for r in allrows if r['variant']==variant};per=[]
  for wording in ['original','fresh']:
   vals=[]
   for item in sorted({r['id'] for r in allrows}):
    key=lambda c:(item,wording,c)
    vals.append(lookup[key('peer_ai')]['share_W']-base[key('peer_ai')]['share_W']-lookup[key('unrelated')]['share_W']+base[key('unrelated')]['share_W'])
   per.append(sum(vals)/len(vals))
  assert min(per)>0,(variant,per);out[variant]['share_gain_by_wording']=per
 C.write('engineering_gate.json',{'passed':True,'checks':out,'scope':'Previously evaluated contexts; implementation replication only, not new confirmation.'});print('ENGINEERING GATE PASS',out,flush=True)

def stage(which):
 verify();I=runtime();import torch
 assert not os.environ.get('RUNPOD_POD_ID'),'This is laptop-only; no pod execution'
 jobs=engineering_jobs() if which=='engineering' else C.read('frozen_materials.json')['jobs']
 if which=='primary':assert C.read('engineering_gate.json')['passed']
 with I.gpu('V7/V15 local cross-task '+which):
  torch.manual_seed(730700);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
  C.write('provenance/host_registry.json',{'H06':{'revision':I.dm.cfg()['models']['qwen']['revision']},'H83':{'revision':I.dm.cfg()['models']['dolos']['revision']}})
  C.write('provenance/environment.json',{'device':torch.cuda.get_device_name(),'dtype':'float32','TF32':False,'models':I.dm.cfg()['models'],'packages':{k:importlib.metadata.version(k) for k in ['torch','transformers','numpy','peft','safetensors']},'command':sys.argv,'tokenizer_revision':I.dm.cfg()['models']['qwen']['revision']})
  for name,variants in [('qwen',['Q','Q_V7','Q_V15','Q_V7_V15']),('dolos',['D'])]:
   model=I.dm.load_model(name,'float32').eval().requires_grad_(False);assert model.config.num_hidden_layers==28 and model.config.hidden_size==1536
   base=fingerprint(model);C.write(f'provenance/{which}_{name}_baseline_weights.json',base)
   original,_=projection_states(I,name);donor,_=projection_states(I,'dolos')
   expected=C.read('provenance/engineering_reference.json')['donor_hashes']
   import hashlib
   for n,t in donor.items():assert hashlib.sha256(t.numpy().tobytes()).hexdigest()==expected[n],n
   if name=='qwen':
    before=score_batch(model,jobs[:1]);set_projection(model,original,[7,15]);after=score_batch(model,jobs[:1]);err=max(abs(before[k]['logp']-after[k]['logp']) for k in before);assert err<1e-7
    assert fingerprint(model)==base
    C.append('provenance/numerical_checks.jsonl',[{'stage':which,'variant':'Q','identical_copy_logp_error':err,'all_parameters_identical':True}])
   for variant in variants:
    blocks={'Q':[],'Q_V7':[7],'Q_V15':[15],'Q_V7_V15':[7,15],'D':[]}[variant]
    try:
     if blocks:set_projection(model,donor,blocks)
     audit_variant(model,base,donor,blocks,which,variant)
     score_jobs(model,jobs,variant,which)
     if which=='primary':generate_jobs(I,model,jobs,variant)
    finally:
     if blocks:set_projection(model,original,blocks)
     assert fingerprint(model)==base
     restored=score_batch(model,jobs[:1]);before0=score_batch(model,jobs[:1]) if name=='dolos' else before
     error=max(abs(restored[k]['logp']-before0[k]['logp']) for k in restored);assert error<.001
     C.append('provenance/numerical_checks.jsonl',[{'stage':which,'variant':variant,'restore_logp_error':error,'every_parameter_restored':True}])
     gc.collect();torch.cuda.empty_cache()
    print('DONE',which,variant,flush=True)
   del model;gc.collect();torch.cuda.empty_cache()
 if which=='engineering':reference_gate()
 else:C.write('run_state.json',{'status':'INFERENCE_COMPLETE','primary_scores':len(C.rows('likelihoods.jsonl')),'generated_responses':len(C.rows('generated_responses.jsonl'))})

def main():
 which=sys.argv[1] if len(sys.argv)>1 else 'all'
 if which=='all':
  stage('engineering');stage('primary')
 else:stage(which)

if __name__=='__main__':main()
