"""Compact prospective native-D stage on laptop; never contacts A5000."""
import functools,gc,importlib.metadata,importlib.util,json,math,os,sys,time
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('MKL_NUM_THREADS','2')
import common as C
import variants
from run_A5000 import score

def records(name):return [json.loads(x) for x in (C.R/name).read_text().splitlines()] if (C.R/name).exists() else []
def append(name,rows):
 with (C.R/name).open('a',encoding='utf-8') as f:
  for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
  f.flush();os.fsync(f.fileno())

def donor(I):
 from huggingface_hub import hf_hub_download
 from safetensors import safe_open
 c=I.dm.cfg()['models']['qwen'];p=hf_hub_download(c['repo'],'model.safetensors',revision=c['revision'],cache_dir=I.dm.CACHE,local_files_only=True,token=False)
 with safe_open(p,framework='pt',device='cpu') as f:return {k:f.get_tensor('model.layers.7.self_attn.v_proj.'+k).float().clone() for k in ['weight','bias']}

def engineering(model,original,target):
 data=C.read('source/engineering.json')['native'];jobs=data['rows'];checks={};reference_names=['dolos_baseline','dolos_b7_both'];out={}
 expected=C.read('source/engineering_hashes.json')['dolos'];assert variants.hashes(original)==expected['original_v_hashes'];assert variants.hashes(target)==expected['donor_v_hashes']
 before=score(model,jobs[:2]);variants.load(model,original);sham=score(model,jobs[:2]);shamerr=max(abs(a[k]-b[k]) for a,b in zip(before,sham) for k in ['logp_truth','logp_peer']);assert shamerr<.001
 for label,state,name in zip(['D','D_minus_V7'],[original,target],reference_names):
  variants.load(model,state);sc=[]
  for start in range(0,len(jobs),2):sc+=score(model,jobs[start:start+2])
  ref={(r['id'],r['wording'],r['cond']):r for r in data['references'][name]};err=max(abs(s[k]-ref[j['id'],j['wording'],j['cond']]['logps'][n]) for j,s in zip(jobs,sc) for n,k in enumerate(['logp_truth','logp_peer']));assert err<.003,(label,err)
  out[label]=sc;checks[label]={'max_archived_logp_error':err,'contexts':len(sc)}
 variants.load(model,original)
 # Same validated original-scale engineering direction in both old wordings.
 byword={}
 for w in ['original','fresh']:
  value={}
  for label in ['D','D_minus_V7']:
   value[label]={c:sum(s['share'] for j,s in zip(jobs,out[label]) if j['wording']==w and j['cond']==c)/sum(j['wording']==w and j['cond']==c for j in jobs) for c in ['peer_ai','unrelated']}
  byword[w]=(value['D']['peer_ai']-value['D']['unrelated'])-(value['D_minus_V7']['peer_ai']-value['D_minus_V7']['unrelated']);assert byword[w]>0
 C.write('stageA_engineering.json',{'passed':True,'same_device':'local laptop FP32','sham_error':shamerr,'checks':checks,'archived_share_effect_per_wording':byword,'original_v_hashes':variants.hashes(original),'donor_v_hashes':variants.hashes(target)})

def generate(I,model,tok,jobs,variant):
 req=[{'id':j['key'],'input_ids':j['chat_ids'],'host_id':'H83','seed':731100+int(j['id'].split('-')[-1]),'max_new_tokens':96,'params':{'do_sample':False}} for j in jobs];raw=I.sample_batch(model,req,tok);out=[]
 for j,r in zip(jobs,raw):
  complete=r['stop_reason']=='eos';ids=r['output_ids'];text=tok.decode(ids[:-1] if complete else ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
  assert r['batched_uncached_first_probability_max_error']<.0005
  out.append({'input_ids':j['chat_ids'],'output_ids':ids,'text':text,'stop_reason':r['stop_reason'],'score':C.parse(text,j,not complete),'first_probability_parity_error':r['batched_uncached_first_probability_max_error']})
 return out

def evaluate(I,model,tok,jobs,variant,phase,generate_all,benchmarked):
 sdone={(r['variant'],r['key']) for r in records('stageA_scores.jsonl')};gdone={(r['variant'],r['key']) for r in records('stageA_generations.jsonl')};needsgen=generate_all
 for start in range(0,len(jobs),2):
  chunk=jobs[start:start+2];sneed=[j for j in chunk if (variant,j['key']) not in sdone];gneed=[j for j in chunk if needsgen and (variant,j['key']) not in gdone]
  if not sneed and not gneed:continue
  tick=time.monotonic();sc=score(model,sneed) if sneed else [];stime=time.monotonic()-tick;tick=time.monotonic();gg=generate(I,model,tok,gneed,variant) if gneed else [];gtime=time.monotonic()-tick
  def meta(j):return {k:j[k] for k in ['id','key','split','wording','input_format','output_format','condition','truth','peer','expected']}|{'variant':variant,'phase':phase}
  append('stageA_scores.jsonl',[meta(j)|z for j,z in zip(sneed,sc)]);append('stageA_generations.jsonl',[meta(j)|z for j,z in zip(gneed,gg)])
  bkey=(variant,chunk[0]['input_format'],chunk[0]['output_format'],phase)
  if bkey not in benchmarked:
   benchmarked.add(bkey);append('stageA_benchmarks.jsonl',[{'variant':variant,'phase':phase,'input':chunk[0]['input_format'],'output':chunk[0]['output_format'],'scored_contexts':len(sc),'generated_contexts':len(gg),'score_wall_seconds':stime,'generation_wall_seconds':gtime,'generated_tokens':sum(len(x['output_ids']) for x in gg),'interpretation':'Observed first batch, not a guaranteed whole-run ETA'}])

def main():
 assert not os.environ.get('RUNPOD_POD_ID'),'Local-only stage: A5000 belongs to tracing'
 for p,h in C.read('freeze_stageA.json')['files'].items():assert C.sha(C.R/p)==h,p
 spec=importlib.util.spec_from_file_location('format_local_inference',C.W/'outputs/dolos-reverse-finetuning-v2/inference.py');I=importlib.util.module_from_spec(spec);spec.loader.exec_module(I);I.R=C.R;I.tok=functools.lru_cache(maxsize=1)(I.tok)
 import torch,psutil
 assert 'Laptop' in torch.cuda.get_device_name(),'Use the authorized laptop CUDA device'
 cfg=C.read('stageA_config.json');bank=C.read('frozen_materials.json');jobs=bank['contexts'];tok=I.tok()
 for j in jobs:
  text=tok.apply_chat_template(j['messages'],tools=bank['tools'],tokenize=False,add_generation_prompt=True);assert text==j['chat_prompt'] and tok(text).input_ids==j['chat_ids'];assert tok(j['prompt']).input_ids==j['input_ids']
 if (C.R/'stageA_run_state.json').exists() and C.read('stageA_run_state.json')['status']=='COMPLETE':print('ALREADY COMPLETE');return
 with I.gpu('Compact V7 matched-format Stage A; local only'):
  started=time.monotonic();deadline=started+cfg['GPU_time_budget_seconds'];torch.manual_seed(731100);torch.set_num_threads(2);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
  C.write('provenance/host_registry.json',{'H83':{'revision':I.dm.cfg()['models']['dolos']['revision']}})
  C.write('stageA_runtime.json',{'device':torch.cuda.get_device_name(),'precision':'FP32','TF32':False,'threads':torch.get_num_threads(),'batch':2,'revisions':I.dm.cfg()['models'],'packages':{k:importlib.metadata.version(k) for k in ['torch','transformers','numpy']},'A5000_accessed':False})
  model=I.dm.load_model('dolos','float32').eval().requires_grad_(False);original=variants.state(model);target=donor(I);stable=variants.fingerprint(model);versions=variants.versions(model)
  C.write('stageA_weight_identity.json',{'non_target_before':stable,'original':variants.hashes(original),'donor':variants.hashes(target),'target':['model.layers.7.self_attn.v_proj.weight','model.layers.7.self_attn.v_proj.bias']})
  try:
   engineering(model,original,target);assert variants.fingerprint(model)==stable
   benchmarked=set();finished=[];limited=False
   selections=[('calibration',cfg['calibration_ids']),('main',[x['id'] for x in bank['main_materials']])]
   for phase,ids in selections:
    for item in ids:
     group=[j for j in jobs if j['split']==phase and j['id']==item];assert group
     for variant,state in [('D',original),('D_minus_V7',target)]:
      variants.load(model,state);assert variants.versions(model)==versions
      evaluate(I,model,tok,group,variant,phase,phase=='calibration' or item in cfg['main_generation_ids'],benchmarked)
      variants.load(model,original);assert variants.hashes(variants.state(model))==variants.hashes(original) and variants.versions(model)==versions
     finished.append({'phase':phase,'id':item});elapsed=time.monotonic()-started
     C.write('stageA_run_state.json',{'status':'RUNNING','finished_paired_materials':finished,'elapsed_seconds':elapsed,'remaining_GPU_budget_seconds':deadline-time.monotonic(),'A5000_accessed':False})
     append('stageA_resource_checks.jsonl',[{'phase':phase,'id':item,'elapsed_seconds':elapsed,'RAM_used_percent':psutil.virtual_memory().percent,'GPU_peak_allocated_bytes':torch.cuda.max_memory_allocated(),'CPU_threads':torch.get_num_threads()}])
     print('PAIRED',phase,item,'elapsed',round(elapsed,1),flush=True)
     if psutil.virtual_memory().percent>90:time.sleep(.5)
     if time.monotonic()>=deadline:limited=True;break
    if limited:break
   status='PARTIAL_TIME_LIMIT' if limited else 'COMPLETE'
   C.write('stageA_run_state.json',{'status':status,'finished_paired_materials':finished,'elapsed_seconds':time.monotonic()-started,'primary_score_pairs':sum(r['phase']=='main' for r in records('stageA_scores.jsonl')),'generated_response_records':len(records('stageA_generations.jsonl')),'A5000_accessed':False,'deferred':['Q','Q_plus_V7','full_generation_matrix']})
  except BaseException:
   C.write('stageA_run_state.json',{'status':'ERROR','partial_outputs_preserved':True,'A5000_accessed':False});raise
  finally:
   variants.load(model,original);assert variants.fingerprint(model)==stable and variants.hashes(variants.state(model))==variants.hashes(original);C.write('stageA_restoration.json',{'all_non_target_parameters_unchanged':True,'original_V7_restored':True,'non_target_after':variants.fingerprint(model),'original_hashes':variants.hashes(original)});del model;gc.collect();torch.cuda.empty_cache()

if __name__=='__main__':main()
