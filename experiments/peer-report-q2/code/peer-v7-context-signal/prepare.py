"""CPU-only reservation and serialization; no new model inference."""
import collections, hashlib, importlib.util, itertools, json, random, re, shutil
from pathlib import Path
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import lil_matrix
R=Path(__file__).resolve().parent; W=R.parents[1]
def write(name,x):
 p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def choose(n,used,seed,split):
 rng=random.Random(seed);opts=[(a,b) for a in range(10,100) for b in range(10,100) if a//10!=b//10 and tuple(sorted((a,b))) not in used]
 pairs=sorted({tuple(sorted(p)) for p in opts}); lookup={p:i for i,p in enumerate(pairs)}
 # Count, sign, leading digit counts in each role, unit counts in each role,
 # exact unit-role balance, unique numeral appearances, unique unordered pairs.
 k=2+18+20+10+90;A=lil_matrix((k+len(pairs),len(opts)))
 lo=[n,n//2]+[n//9]*18+[n//10]*20+[0]*10+[0]*90+[0]*len(pairs)
 hi=[n,(n+1)//2]+[n//9]*18+[(n+9)//10]*20+[0]*10+[1]*90+[1]*len(pairs)
 for j,(t,p) in enumerate(opts):
  for ix,v in [(0,1),(1,int(p>t)),(2+t//10-1,1),(11+p//10-1,1),(20+t%10,1),(30+p%10,1),(40+t%10,1),(40+p%10,-1),(50+t-10,1),(50+p-10,1),(k+lookup[tuple(sorted((t,p)))],1)]:A[ix,j]+=v
 sol=milp(np.array([rng.random() for _ in opts]),integrality=np.ones(len(opts)),bounds=Bounds(0,1),constraints=LinearConstraint(A.tocsr(),lo,hi),options={'time_limit':40})
 assert sol.x is not None,sol.message
 chosen=[p for p,v in zip(opts,sol.x) if v>.5];assert len(chosen)==n;rng.shuffle(chosen);used.update(tuple(sorted(p)) for p in chosen)
 return [dict(id=f'{split}-{i:02d}',truth=t,peer=p,name_variant=i%2) for i,(t,p) in enumerate(chosen)]
def main():
 assert not (R/'reserved_materials.json').exists()
 C=load('format_common_cpu',W/'experiments/peer-v7-format-transfer/common.py')
 used=set();sources=[]
 def extra(v):
  if isinstance(v,dict):
   vals=v.get('values')
   if isinstance(vals,list) and len(vals)==4 and all(type(a)is int and 10<=a<=99 for a in vals):used.update(tuple(sorted(p)) for p in itertools.combinations(vals,2))
   for x in v.values():extra(x)
  elif isinstance(v,list):
   for x in v:extra(x)
 for root in [W/'experiments',W/'artifacts',W/'outputs']:
  for p in sorted(root.rglob('*.json')):
   if R in p.parents or p.stat().st_size>35_000_000 or not any(x in p.name.lower() for x in ['frozen','reserved','materials','bank','design','exclusion']):continue
   try:obj=json.loads(p.read_text(encoding='utf-8-sig'))
   except (ValueError,OSError):continue
   old=len(used);used.update(C.collect(obj));extra(obj)
   sources.append(dict(path=p.relative_to(W).as_posix(),sha256=C.sha(p),new_pairs=len(used)-old))
 original=set(used);discovery=choose(9,used,841101,'discovery');validation=choose(18,used,841102,'validation')
 write('reserved_materials.json',dict(discovery=discovery,validation=validation,excluded_pairs=sorted(original),sources=sources))
 # Reservation exists before importing the tokenizer, so a parallel preparer can exclude it.
 import sys
 sys.path.insert(0,str(W/'experiments/peer-v7-format-transfer'))
 F=load('format_prepare_cpu',W/'experiments/peer-v7-format-transfer/prepare.py')
 I=load('context_tokenizer',W/'outputs/dolos-reverse-finetuning-v2/inference.py');tok=I.tok()
 conds=['ai_report','software_report','ai_timer','software_timer','empty','truthful','copy_ai','copy_software'];rows=[]
 for split,bank in [('discovery',discovery),('validation',validation)]:
  for m in bank:
   for w in [0,1]:
    for c in conds:
     cond='ai_report' if c=='truthful' else c
     mm=m if c!='truthful' else dict(m,peer=m['truth'])
     messages=F.context(mm,w,'json','tool',cond)
     chat=tok.apply_chat_template(messages,tools=F.TOOLS,tokenize=False,add_generation_prompt=True)
     prompt=chat+'<tool_call>\n{"name": "submit_report", "arguments": {"count":'
     ids=tok(prompt).input_ids;suffix={}
     for lab in ['truth','peer']:
      full=tok(prompt+' '+str(m[lab])).input_ids;assert full[:len(ids)]==ids;suffix[lab]=full[len(ids):];assert len(suffix[lab])==3 and suffix[lab][0]==220
     rows.append(dict(**m,split=split,wording=w,condition=c,key=f"{m['id']}:{w}:{c}",messages=messages,chat_prompt=chat,chat_ids=tok(chat).input_ids,prompt=prompt,input_ids=ids,suffix_ids=suffix,expected=m['peer'] if c.startswith('copy') else m['truth'],query_positions={'first_digit':len(ids),'second_digit':len(ids)+1}))
 index={(r['id'],r['wording'],r['condition']):r for r in rows}
 length_checks=[]
 for r in rows:
  if r['condition'] not in ['ai_report','software_report']:continue
  timer=index[r['id'],r['wording'],r['condition'].replace('report','timer')]
  assert len(timer['input_ids'])==len(r['input_ids']), 'Do not silently patch unmatched positions'
  diffs=[i for i,(a,b) in enumerate(zip(r['input_ids'],timer['input_ids'])) if a!=b]
  numeral=re.search(r'"arguments": \{"count": (\d+)',r['chat_prompt'][r['chat_prompt'].index('<tool_response>'):]).group(1)
  assert numeral==str(r['peer'])
  length_checks.append(dict(report=r['key'],timer=timer['key'],tokens=len(r['input_ids']),different_token_positions=diffs))
 write('frozen_materials.json',dict(discovery=discovery,validation=validation,rows=rows,tools=F.TOOLS,report_timer_alignment=length_checks,excluded_pairs=sorted(original),exclusion_sources=sources))
 config=dict(seed=841100,bootstrap_seed=841103,bootstrap_draws=20000,discovery_pairs=9,validation_pairs=18,wordings=2,mean_pool='Discovery AI/software relevant reports, both wordings and both candidate branches; pooled across all, one 2x1536 post-o_proj vector frozen before validation',site='Only q=L (first numerical digit) and q=L+1 (candidate-conditioned second digit); leading-space prediction q=L-1 unchanged; same local mask for zero/mean/donor/random/sham',primary='First-digit logP(peer)-logP(truth), no answer digit provided; full suffix and later digit secondary',scope='Local numerical prediction span, not whole-context V7 restoration',precision='FP32, TF32 off, FP64 sums',batch=2,threads=2,GPU_budget_seconds=2100,practical_local_effect_nat=.025,practical_mean_effect_nat=.02,mean_recovery_fraction=.5,practical_mean_random_advantage_nat=.02,practical_function_difference_nat=.02,primary_family=4,primary_CI=1-.05/4,control_correct_mass_loss_flag=.02,control_modal_correct_minimum=16,random_seeds=[841104,841105],no_new_search=True,no_model_training=True,no_A5000=True)
 write('config.json',config)
 for fn in ['model_io.py','variants.py']:shutil.copyfile(W/'experiments/peer-v7-format-transfer'/fn,R/fn)
 shutil.copyfile(W/'experiments/peer-v7-information-trace/run_trace.py',R/'reference_run_trace.py')
 write('run_state.json',dict(status='PREPARED_NO_INFERENCE',discovery=9,validation=18))
 print(json.dumps(dict(rows=len(rows),reservation_sha256=C.sha(R/'reserved_materials.json'),report_timer_equal_length=True),indent=2))
if __name__=='__main__':main()
