"""Staged A5000-only finite run. Refuses laptop execution or busy GPU.

No network/API/pod management in this worker. Parent must deploy the frozen
directory to the existing pod. It never starts/stops a pod or touches old runs.
"""
import gc,hashlib,json,math,os,sys,time
from pathlib import Path
import common as C

def append(name,records):
 with (C.R/name).open('a',encoding='utf-8') as f:
  for r in records:f.write(json.dumps(r,ensure_ascii=False)+'\n')
  f.flush();os.fsync(f.fileno())
def rows(name):return [json.loads(x) for x in (C.R/name).read_text(encoding='utf-8').splitlines()] if (C.R/name).exists() else []

def score(model,jobs):
 import torch
 seq=[];keys=[]
 for i,j in enumerate(jobs):
  for lab in ['truth','peer']:seq.append(j['input_ids']+j['suffix_ids'][lab][:-1]);keys.append((i,lab))
 L=max(map(len,seq));x=torch.tensor([s+[151643]*(L-len(s)) for s in seq],device='cuda');mask=torch.tensor([[1]*len(s)+[0]*(L-len(s)) for s in seq],device='cuda');pos=(mask.cumsum(-1)-1).clamp_min(0)
 out=[{} for _ in jobs]
 with torch.inference_mode():
  h=model.model(input_ids=x,attention_mask=mask,position_ids=pos,use_cache=False).last_hidden_state
  for k,(i,lab) in enumerate(keys):
   j=jobs[i];start=len(j['input_ids'])-1;ts=j['suffix_ids'][lab];lp=model.lm_head(h[k,start:start+len(ts)]).float().log_softmax(-1);vals=lp.gather(1,torch.tensor(ts,device='cuda')[:,None]).squeeze(1)
   out[i]['logp_'+lab]=float(vals.double().sum());out[i]['terms_'+lab]=vals.tolist()
 for z in out:
  z['margin']=z['logp_peer']-z['logp_truth'];z['pt']=math.exp(z['logp_truth']);z['pf']=math.exp(z['logp_peer']);z['share']=1/(1+math.exp(max(-700,min(700,-z['margin']))))
 return out

def generate(model,tok,jobs):
 import torch
 L=max(len(j['chat_ids']) for j in jobs);ids=torch.tensor([[151643]*(L-len(j['chat_ids']))+j['chat_ids'] for j in jobs],device='cuda');mask=torch.tensor([[0]*(L-len(j['chat_ids']))+[1]*len(j['chat_ids']) for j in jobs],device='cuda')
 with torch.inference_mode():out=model.generate(input_ids=ids,attention_mask=mask,do_sample=False,max_new_tokens=96,use_cache=True,pad_token_id=151643,eos_token_id=[151643,151645])
 result=[]
 for i,j in enumerate(jobs):
  seq=out[i,L:].tolist();end=next((k for k,t in enumerate(seq) if t in [151643,151645]),None);capped=end is None
  if end is not None:seq=seq[:end+1]
  text=tok.decode(seq if capped else seq[:-1],skip_special_tokens=False,clean_up_tokenization_spaces=False)
  result.append({'text':text,'input_ids':j['chat_ids'],'output_ids':seq,'stop_reason':'token_cap' if capped else 'eos','score':C.parse(text,j,capped)})
 return result

def engineering(model,tok,name):
 import variants
 data=C.read('source/engineering.json')['native' if name=='dolos' else 'reverse'];jobs=data['rows'];original=variants.state(model);target=variants.donor('qwen' if name=='dolos' else 'dolos');expected=C.read('source/engineering_hashes.json')[name]
 assert variants.hashes(original)==expected['original_v_hashes'];assert variants.hashes(target)==expected['donor_v_hashes'];stable=variants.fingerprint(model);versions=variants.versions(model)
 base=score(model,jobs);one=score(model,jobs[:1])[0];batcherr=max(abs(base[0][k]-one[k]) for k in ['logp_truth','logp_peer']);assert batcherr<.001
 variants.load(model,original);sham=score(model,jobs[:1])[0];assert max(abs(sham[k]-one[k]) for k in ['logp_truth','logp_peer'])<.001
 try:variants.load(model,target);edited=score(model,jobs)
 finally:variants.load(model,original)
 assert variants.fingerprint(model)==stable and variants.versions(model)==versions
 keys=['dolos_baseline','dolos_b7_both'] if name=='dolos' else ['qwen_baseline','qwen_b7_only_v'];errs=[]
 for scored,key in zip([base,edited],keys):
  ref={(r['id'],r['wording'],r['cond']):r for r in data['references'][key]}
  for j,s in zip(jobs,scored):
   old=ref[j['id'],j['wording'],j['cond']];errs.extend([abs(s['logp_truth']-old['logps'][0]),abs(s['logp_peer']-old['logps'][1])])
 assert max(errs)<.003
 C.write(f'engineering_{name}.json',{'passed':True,'max_archived_logp_error':max(errs),'batch_single_error':batcherr,'sham_error':max(abs(sham[k]-one[k]) for k in ['logp_truth','logp_peer']),'original_v_hashes':variants.hashes(original),'donor_v_hashes':variants.hashes(target),'non_target_before':stable,'non_target_after':variants.fingerprint(model),'n_contexts':len(jobs)})

def evaluate(model,tok,jobs,variant,phase):
 import variants
 before=variants.fingerprint(model);done={(r['variant'],r['key']) for r in rows(phase+'_generations.jsonl')}
 # A case is complete only when both scores and generation were persisted.
 scored={(r['variant'],r['key']) for r in rows(phase+'_scores.jsonl')};todo=[j for j in jobs if (variant,j['key']) not in done or (variant,j['key']) not in scored]
 for start in range(0,len(todo),8):
  chunk=todo[start:start+8];s=score(model,chunk);g=generate(model,tok,chunk);ss=[];gg=[]
  for j,z,out in zip(chunk,s,g):
   meta={k:j[k] for k in ['key','id','truth','peer','wording','input_format','output_format','condition','expected']};meta['variant']=variant
   if (variant,j['key']) not in scored:ss.append(meta|z)
   if (variant,j['key']) not in done:gg.append(meta|out)
  append(phase+'_scores.jsonl',ss);append(phase+'_generations.jsonl',gg)
  C.write('run_state.json',{'status':'RUNNING','phase':phase,'variant':variant,'completed_this_resume':start+len(chunk),'planned_this_resume':len(todo),'keep_pod_running':True})
  if start%64==0:print(phase,variant,start+len(chunk),'/',len(todo),flush=True)
 assert variants.fingerprint(model)==before

def calibration_gate():
 records=rows('calibration_generations.jsonl');out={}
 for model in ['D','Q']:
  cells=[]
  for inp,fmt in C.CELLS:
   for w in [0,1]:
    for task in ['empty','copy']:
     rs=[r for r in records if r['variant']==model and r['input_format']==inp and r['output_format']==fmt and r['wording']==w and (r['condition']=='empty' if task=='empty' else r['condition'].startswith('copy'))]
     success=sum(r['score']['correct'] and r['score']['format_valid'] for r in rs);cells.append({'input':inp,'output':fmt,'wording':w,'task':task,'n':len(rs),'correct_and_format':success,'passed':len(rs)==12 and success>=11})
  out[model]={'passed':all(r['passed'] for r in cells),'cells':cells}
 C.write('calibration_gate.json',out);return out

def main():
 assert os.environ.get('RUNPOD_POD_ID')=='8k5cez1c911ec9','A5000 only: laptop execution prohibited'
 import fcntl,subprocess
 prior=Path('/v7_instruction_gating/run_state.json');assert prior.exists() and json.loads(prior.read_text())['status']=='COMPLETE','Prior worker not complete'
 lock=open('/tmp/dolos-a5000-gpu.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 active=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True).strip().splitlines();assert not [p for p in active if p.strip() and p.strip()!=str(os.getpid())],'Another compute worker is active'
 for p,h in C.read('freeze.json')['files'].items():assert C.sha(C.R/p)==h,p
 os.environ['HF_HOME']='/workspace/.cache/huggingface'
 import torch,model_io,variants
 assert 'A5000' in torch.cuda.get_device_name();torch.manual_seed(731100);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;torch.set_num_threads(8)
 tok=model_io.tokenizer();bank=C.read('frozen_materials.json');jobs=bank['contexts']
 for j in jobs:
  chat=tok.apply_chat_template(j['messages'],tools=bank['tools'],tokenize=False,add_generation_prompt=True)
  assert chat==j['chat_prompt'] and tok(chat).input_ids==j['chat_ids'] and tok(j['prompt']).input_ids==j['input_ids']
 C.write('runtime.json',{'device':torch.cuda.get_device_name(),'torch':torch.__version__,'transformers':__import__('transformers').__version__,'dtype':'FP32','TF32':False,'revisions':model_io.REVISIONS,'laptop_CUDA':False})
 try:
  for name in ['dolos','qwen']:
   model=model_io.load_model(name,torch.device('cuda'),torch.float32).requires_grad_(False);engineering(model,tok,name);del model;gc.collect();torch.cuda.empty_cache()
  for name,label in [('dolos','D'),('qwen','Q')]:
   model=model_io.load_model(name,torch.device('cuda'),torch.float32).requires_grad_(False);evaluate(model,tok,[j for j in jobs if j['split']=='calibration'],label,'calibration');del model;gc.collect();torch.cuda.empty_cache()
  gate=calibration_gate()
  if not gate['D']['passed']:
   C.write('run_state.json',{'status':'STOP_CALIBRATION','primary_not_run':True,'reason':'Native Dolos calibration failed; no prompt repair','keep_pod_running':True});return
  for name,labels in [('dolos',['D','D_minus_V7']),('qwen',['Q','Q_plus_V7'] if gate['Q']['passed'] else [])]:
   if not labels:continue
   model=model_io.load_model(name,torch.device('cuda'),torch.float32).requires_grad_(False);original=variants.state(model);target=variants.donor('qwen' if name=='dolos' else 'dolos');stable=variants.fingerprint(model)
   for label in labels:
    try:
     if label in ['D_minus_V7','Q_plus_V7']:variants.load(model,target)
     assert variants.fingerprint(model)==stable
     C.write(f'weights_{label}.json',{'original_v':variants.hashes(original),'applied_v':variants.hashes(variants.state(model)),'non_target_hash':stable})
     evaluate(model,tok,[j for j in jobs if j['split']=='main'],label,'main')
    finally:variants.load(model,original);assert variants.fingerprint(model)==stable and variants.hashes(variants.state(model))==variants.hashes(original)
   del model;gc.collect();torch.cuda.empty_cache()
  C.write('run_state.json',{'status':'COMPUTE_COMPLETE','main_generations':len(rows('main_generations.jsonl')),'main_scores':len(rows('main_scores.jsonl')),'reciprocal_ran':gate['Q']['passed'],'keep_pod_running':True})
 except BaseException:
  C.write('run_state.json',{'status':'ERROR','partial_outputs_preserved':True,'keep_pod_running':True});raise
 finally:fcntl.flock(lock,fcntl.LOCK_UN);lock.close()

if __name__=='__main__':main()
