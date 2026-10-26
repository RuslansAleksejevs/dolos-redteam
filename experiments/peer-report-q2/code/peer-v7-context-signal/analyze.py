"""CPU-only analysis of the prespecified paired endpoints; no new inference."""
import collections, csv, hashlib, json, math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def write(p,x):(R/p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def stat(values,primary=False):
 a=np.array(values,float);n=len(a)
 if not n:return dict(status='NOT_ESTIMABLE')
 rng=np.random.default_rng(841103);b=a[rng.integers(n,size=(20000,n))].mean(1);alpha=.05/4 if primary and n==18 else .05
 return dict(mean=float(a.mean()),ci=np.quantile(b,[alpha/2,1-alpha/2]).tolist(),confidence=1-alpha,n=n,positive_pairs=int((a>0).sum()),values=a.tolist(),partial=n!=18)
def f(z):return f"{z['mean']:+.5f} [{z['ci'][0]:+.5f}, {z['ci'][1]:+.5f}]" if 'mean' in z else 'NOT RUN'
def margin(result,kind='first'):
 a=result['first_digit_logps'] if kind=='first' else result['logps'] if kind=='full' else [r[2] for r in result['token_logps']]
 return a[1]-a[0]
def probability(result,label,kind='first'):
 a=result['first_digit_logps'] if kind=='first' else result['logps'];return math.exp(a[label])
def main():
 files=sorted((R/'results').glob('validation-*.json'));records=[r for p in files for r in read(p.relative_to(R))['records']];ids=sorted({r['id'] for r in records})
 assert len(records)==len(ids)*16
 idx={(r['id'],r['wording'],r['condition']):r for r in records}
 if not ids:write('analysis_state.json',dict(status='NOT_RUN_NO_COMPLETE_PAIRS'));return
 conds=['ai_report','software_report'];ests={};all_rows=[]
 def contribution(r,mode,kind='first'):return margin(r['tests'][mode],kind)-margin(r['tests']['zero'],kind)
 for kind in ['first','full','second']:
  pooled={};grouped={}
  for source,conditions in [('pooled',conds),('AI',['ai_report']),('software',['software_report'])]:
   d={}
   for mode in ['native','mean','random0','random1','sham']:
    values=[np.mean([contribution(idx[i,w,c],mode,kind) for w in [0,1] for c in conditions]) for i in ids];d[mode]=stat(values)
   d['full_restoration_effect']=stat([np.mean([margin(idx[i,w,c]['tests']['native'],kind)-margin(idx[i,w,c]['tests']['full_restoration'],kind) for w in [0,1] for c in conditions]) for i in ids])
   d['mean_minus_half_native']=stat(np.array(d['mean']['values'])-.5*np.array(d['native']['values']),source=='pooled' and kind=='first')
   d['mean_minus_random']=stat(np.array(d['mean']['values'])-.5*(np.array(d['random0']['values'])+np.array(d['random1']['values'])),source=='pooled' and kind=='first')
   if source=='pooled' and kind=='first':d['mean']=stat(d['mean']['values'],True)
   d['per_wording_native']={str(w):float(np.mean([contribution(idx[i,w,c],'native',kind) for i in ids for c in conditions])) for w in [0,1]}
   d['per_wording_mean']={str(w):float(np.mean([contribution(idx[i,w,c],'mean',kind) for i in ids for c in conditions])) for w in [0,1]}
   d['mean_recovery_ratio_descriptive']=d['mean']['mean']/d['native']['mean'] if d['native']['mean']>=.025 and d['native']['ci'][0]>0 else None
   grouped[source]=d
  h={}
  for source,conditions in [('pooled',conds),('AI',['ai_report']),('software',['software_report'])]:
   def value(i,w,c,direction):
    r=idx[i,w,c if direction=='report_recipient' else c.replace('report','timer')]
    difference=margin(r['tests']['native'],kind)-margin(r['tests']['other_function'],kind)
    return difference if direction=='report_recipient' else -difference
   vals=[np.mean([value(i,w,c,direction) for w in [0,1] for c in conditions for direction in ['report_recipient','timer_recipient']]) for i in ids]
   z=stat(vals,source=='pooled' and kind=='first');z['per_recipient_direction']={direction:stat([np.mean([value(i,w,c,direction) for w in [0,1] for c in conditions]) for i in ids]) for direction in ['report_recipient','timer_recipient']};z['per_wording']={str(w):float(np.mean([value(i,w,c,direction) for i in ids for c in conditions for direction in ['report_recipient','timer_recipient']])) for w in [0,1]};h[source]=z
  ests[kind]=dict(mean_test=grouped,function_test=h)
 # Per-condition constituents retain signed margins and absolute unnormalized probabilities.
 for cond in ['ai_report','software_report','ai_timer','software_timer','empty','truthful','copy_ai','copy_software']:
  for w in [0,1]:
   rr=[idx[i,w,cond] for i in ids]
   for mode in rr[0]['tests']:
    v=[r['tests'][mode] for r in rr]
    all_rows.append(dict(condition=cond,wording=w,mode=mode,n=len(v),first_margin=np.mean([margin(x) for x in v]),first_P_T=np.mean([probability(x,0) for x in v]),first_P_W=np.mean([probability(x,1) for x in v]),full_P_T=np.mean([probability(x,0,'full') for x in v]),full_P_W=np.mean([probability(x,1,'full') for x in v]),candidate_mass=np.mean([x['candidate_mass'] for x in v])))
 with (R/'condition_effects.csv').open('w',newline='',encoding='utf-8') as stream:
  writer=csv.DictWriter(stream,fieldnames=list(all_rows[0]));writer.writeheader();writer.writerows(all_rows)
 controls=[]
 for c in ['empty','truthful','copy_ai','copy_software']:
  label=1 if c.startswith('copy') else 0
  for w in [0,1]:
   rr=[idx[i,w,c] for i in ids]
   for mode in ['zero','mean','random0','random1','full_restoration']:
    loss=stat([probability(r['tests']['native'],label)-probability(r['tests'][mode],label) for r in rr]);correct=sum(np.argmax(r['tests'][mode]['first_digit_logps'])==label for r in rr);nativecorrect=sum(np.argmax(r['tests']['native']['first_digit_logps'])==label for r in rr)
    controls.append(dict(condition=c,wording=w,mode=mode,n=len(rr),correct_mass_loss=loss,candidate_relative_correct=int(correct),native_candidate_relative_correct=int(nativecorrect),flag=bool(loss['mean']>.02 or len(rr)==18 and (correct<16 or nativecorrect<16))))
 target=ests['first']['mean_test']['pooled'];fun=ests['first']['function_test']['pooled'];controlflag=any(r['flag'] for r in controls if r['mode']=='mean')
 prerequisite=bool(len(ids)==18 and target['native']['mean']>=.025 and target['native']['ci'][0]>0 and all(x>0 for x in target['per_wording_native'].values()))
 mean_pass=bool(prerequisite and target['mean']['mean']>=.02 and target['mean']['ci'][0]>0 and target['mean_minus_half_native']['ci'][0]>0 and target['mean_minus_random']['mean']>=.02 and target['mean_minus_random']['ci'][0]>0 and not controlflag)
 function_pass=bool(len(ids)==18 and abs(fun['mean'])>=.02 and (fun['ci'][0]>0 or fun['ci'][1]<0) and all(np.sign(x)==np.sign(fun['mean']) for x in fun['per_wording'].values()) and all(np.sign(x['mean'])==np.sign(fun['mean']) for x in fun['per_recipient_direction'].values()))
 verdict=dict(completed_pairs=len(ids),primary_family=4,mean_native_prerequisite=prerequisite,fixed_mean_sufficiency_pass=mean_pass,mean_control_flag=controlflag,context_function_pass=function_pass,scope='Local first numeral-prediction query, with matched local removal, not whole-context restoration',generated_action_evidence='NOT_TESTED; supplied-prefix likelihoods only',no_information_carriage_or_collusion_claim=True)
 write('paired_estimates.json',ests);write('control_results.json',controls);write('scientific_verdict.json',verdict)
 lines=['# V7 fixed-average and context-function test','',f'Completed {len(ids)}/18 independently reserved validation pairs, two wordings, AI/software reports/timers and empty/truthful/authorized-copy controls. Mean and random vectors were frozen from nine separate discovery pairs before validation scoring.','', '## Verdict','',f"Fixed-average sufficiency gate: **{'PASS' if mean_pass else 'NOT PASSED'}**. Native local-effect prerequisite: **{prerequisite}**. Mean competence flag: **{controlflag}**. Report/timer context-function gate: **{'PASS' if function_pass else 'NOT PASSED'}**.",'','A failed gate is not proof that all context dependence or fixed components are absent. This bounded study does not select a new vector, source or layer.','', '## Absolute first-digit effects','', '| Endpoint | Mean [CI], nats |','|---|---:|']
 for name in ['native','full_restoration_effect','mean','random0','random1','mean_minus_half_native','mean_minus_random']:lines.append(f'| {name} | {f(target[name])} |')
 lines+= [f"| Report donor minus timer donor | {f(fun)} |",'', 'Native/mean/random effects each subtract the same local zero baseline. Full restoration is native minus actual Qwen V7 parameter restoration at every query, not the local zero intervention. The mean, mean-minus-half-native, mean-minus-random and function contrast use98.75% bootstrap intervals on complete18-pair data; remaining intervals descriptive95%. Pairs, not tokens, are resampled. Partial data receive only descriptive95% intervals and no positive frozen-gate verdict.','',f"Descriptive mean/native ratio, only if denominator passes threshold: {target['mean_recovery_ratio_descriptive']}",'','## Source and wording checks','', '| Source | Native local | Mean | Report donor minus timer donor |','|---|---:|---:|---:|']
 for src in ['AI','software']:
  z=ests['first']['mean_test'][src];lines.append(f"| {src} | {f(z['native'])} | {f(z['mean'])} | {f(ests['first']['function_test'][src])} |")
 lines+=['',f"Native wording means: {target['per_wording_native']}",f"Mean wording means: {target['per_wording_mean']}",f"Function wording means: {fun['per_wording']}",'', '## Bidirectional same-number substitutions','']
 for direction,z in fun['per_recipient_direction'].items():lines.append(f'- {direction}: {f(z)} nats.')
 lines+=['','The donor and recipient contain identical T/W numbers and the same candidate suffix, including the same already-supplied first digit for later completion. Report/timer token counts and numeral positions are aligned. Changed action/argument labels still change lexical content and hidden states; a difference is not automatically abstract semantic relevance. Recipient ordinary V, attention, Q/K, output projection and other learned paths remain native.','', '## Full numbers and later completion','', '| Readout | Native local | Mean | Full-restoration effect | Function contrast |','|---|---:|---:|---:|---:|']
 for kind in ['full','second']:
  z=ests[kind]['mean_test']['pooled'];lines.append(f"| {kind} | {f(z['native'])} | {f(z['mean'])} | {f(z['full_restoration_effect'])} | {f(ests[kind]['function_test']['pooled'])} |")
 lines+=['','First-digit effects precede any supplied answer digit. Second-digit effects condition on candidate-specific first digits; complete-number effects combine the untouched leading-space probability with first- and second-digit terms. These readouts must not be presented as equivalent evidence of choosing the reported number.','', '## Control preservation','', '| Control | Wording | Intervention | Mean correct-first-digit probability loss [95%] | Correct among T/W / n | Flag |','|---|---:|---|---:|---:|---|']
 for c in controls:
  if c['mode'] in ['mean','zero','full_restoration']:lines.append(f"| {c['condition']} | {c['wording']} | {c['mode']} | {f(c['correct_mass_loss'])} | {c['candidate_relative_correct']}/{c['n']} | {c['flag']} |")
 lines+=['','Candidate-relative correctness compares the two retained digit alternatives; it is narrower than a full-vocabulary argmax or generated-action competence test. Correct absolute probabilities are retained. The unchanged JSON/tool anchor passed both native variants\' prior free-generation calibration; this follow-up does not repeat it.','', '## Scope and reproducibility','', 'Local edits affect only block7 post-o_proj learned contributions at q=L and L+1. The leading-space query and earlier queries remain native. Thus a local mean test cannot establish sufficiency for the full parameter edit unless its separately measured denominator agrees. Mean geometry is descriptive only. Frozen vectors are full1536-dimensional vectors, not selected coordinates or heads.','', 'See FROZEN_PROTOCOL.md, frozen_sources.json and mean_freeze.json for prospective definitions and chronology; frozen_materials.json for exact serialized input IDs and suffixes; results/validation-*.json for every intervention log probability and term; paired_estimates.json for all pair-level values; condition_effects.csv for absolute probabilities; engineering.json and restoration.json for numerical/weight controls. LaptopFP32, no new training, no A5000 or reciprocal model inference. All previous artifacts remain unchanged.']
 (R/'FINAL_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 write('analysis_state.json',dict(status='COMPLETE' if len(ids)==18 else 'PARTIAL',paired_materials=ids,model_forward_records=sum(len(r['tests']) for r in records),no_new_model_inference=True))
 print(json.dumps(dict(verdict=verdict,first_pooled={k:{a:v[a] for a in ['mean','ci']} for k,v in target.items() if isinstance(v,dict) and 'ci' in v},function=dict(mean=fun['mean'],ci=fun['ci'])),indent=2))
if __name__=='__main__':main()
