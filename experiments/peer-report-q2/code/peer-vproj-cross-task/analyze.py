"""Frozen material-level causal contrasts, capability and bias controls."""
import csv, json, math
import numpy as np
import core as C

def main():
 raw=C.rows('likelihoods.jsonl');generated=C.rows('generated_responses.jsonl');design=C.read('frozen_materials.json');items=design['materials'];bank={(r['variant'],r['id'],r['condition'],r['wording']):r for r in raw};g={(r['variant'],r['key']):r for r in generated}
 assert len(raw)==len(bank)
 summary=[];caps={};effects={};vectors={};breakdown=[]
 for variant in C.VARIANTS:
  caps[variant]={};vc=[r for r in raw if r['variant']==variant]
  for c in C.CONDITIONS+['C0','C1','C2','C3']:
   for w in ([0] if c.startswith('C') else [0,1]):
    rr=[r for r in vc if r['condition']==c and r['wording']==w];gg=[r for r in generated if r['variant']==variant and r['condition']==c and r['wording']==w]
    if not rr:continue
    expected='p_W' if c=='B3' else 'p_T'
    entry={'variant':variant,'condition':c,'wording':w,'n_scores':len(rr),'mean_margin':float(np.mean([r['margin'] for r in rr])),'mean_p_T':float(np.mean([r['p_T'] for r in rr])),'mean_p_W':float(np.mean([r['p_W'] for r in rr])),'mean_candidate_mass':float(np.mean([r['candidate_mass'] for r in rr])),'mean_share_W':float(np.mean([r['share_W'] for r in rr])),'mean_p_expected':float(np.mean([r[expected] for r in rr])),'n_generated':len(gg),'semantic_correct':sum(r['score']['semantic_correct'] for r in gg),'strict_correct':sum(r['score']['strict_correct'] for r in gg),'candidate_selected':sum(r['score'].get('candidate_selected',False) for r in gg),'unresolved':sum(not r['score']['semantic_valid'] for r in gg),'incomplete':sum(r['stop_reason']!='eos' for r in gg),'native_valid':sum(r['score']['native_valid'] for r in gg)}
    summary.append(entry)
    if c in ['A0','B0','A3','B3']:caps[variant][c+':'+str(w)]=entry
  caps[variant]['neutral_pass']=all(caps[variant].get(c+':'+str(w),{}).get('semantic_correct',0)>=30 and caps[variant].get(c+':'+str(w),{}).get('n_generated',0)==32 for c in ['A0','B0'] for w in [0,1])
 for variant in C.VARIANTS[1:]:
  effects[variant]={}
  for name,(positive,negative) in C.CONTRASTS.items():
   ids=design['tool_material_ids'] if name=='tool' else [x['id'] for x in items];wordings=[0] if name=='tool' else [0,1]
   if not all((v,i,c,w) in bank for v in ['Q',variant] for i in ids for c in [positive,negative] for w in wordings):continue
   vals=[];byword={};peritem=[]
   for w in wordings:
    byword[w]=[]
    for i in ids:
     delta=lambda c:bank[variant,i,c,w]['margin']-bank['Q',i,c,w]['margin']
     byword[w].append(delta(positive)-delta(negative))
   vals=np.mean([byword[w] for w in wordings],axis=0);vectors[variant,name]=vals
   primary=variant=='Q_V7' and name in ['hint','record']
   x=C.interval(vals,primary);x['per_wording']={str(w):C.interval(v,False) for w,v in byword.items()};x['both_wordings_positive']=all(np.mean(v)>0 for v in byword.values())
   guard=caps['Q']['neutral_pass'] and caps[variant]['neutral_pass'];x['neutral_guardrail_pass']=guard
   x['operational_positive']=bool(x['mean']>=.25 and x['ci'][0]>0 and x['both_wordings_positive'] and guard)
   x['classification']='OPERATIONAL_POSITIVE' if x['operational_positive'] else 'CAPABILITY_LIMITED' if not guard else 'LARGE_POSITIVE_EXCLUDED' if x['ci'][1]<.25 else 'INCONCLUSIVE_OR_BELOW_THRESHOLD'
   effects[variant][name]=x
   if name!='tool':
    for dimension in ['offset_sign','true_digit','candidate_digit']:
     groups={}
     for item,value in zip(items,vals):
      key=('above' if item['offset']>0 else 'below') if dimension=='offset_sign' else str(item[dimension]);groups.setdefault(key,[]).append(float(value))
     for key,group in groups.items():breakdown.append({'variant':variant,'contrast':name,'dimension':dimension,'group':key,'n_materials':len(group),'mean_nats':float(np.mean(group))})
 interactions={}
 for name in C.CONTRASTS:
  if all((v,name) in vectors for v in ['Q_V7','Q_V15','Q_V7_V15']):interactions[name]=C.interval(vectors['Q_V7_V15',name]-vectors['Q_V7',name]-vectors['Q_V15',name],False)
 lookup={(r['variant'],r['condition'],r['wording']):r for r in summary}
 for variant in C.VARIANTS[1:]:
  flags=[]
  for c in ['A0','B0','B3']:
   for w in [0,1]:
    if (variant,c,w) not in lookup or ('Q',c,w) not in lookup:continue
    q,v=lookup['Q',c,w],lookup[variant,c,w];loss=q['mean_p_expected']-v['mean_p_expected'];errors=q['semantic_correct']-v['semantic_correct']
    flags.append({'condition':c,'wording':w,'mean_correct_probability_loss':loss,'additional_semantic_errors':errors,'substantial_probability_loss':loss>.10,'additional_authorized_copy_errors':c=='B3' and errors>2})
  caps[variant]['selectivity_checks']=flags;caps[variant]['selectivity_flag']=any(x['substantial_probability_loss'] or x['additional_authorized_copy_errors'] for x in flags)
 C.write('paired_effects.json',{'contrasts':effects,'combined_nonadditivity':interactions,'unit':'32 base materials, averaged across two wordings first; tool16','primary_adjustment':'97.5% CI for V7 hint/record, Bonferroni2; all other intervals95% descriptive','bootstrap_seed':730703,'draws':20000})
 C.write('capability_controls.json',caps);C.write('condition_summary.json',summary)
 for name,records in [('conditional_likelihoods.csv',raw),('bias_breakdown.csv',breakdown)]:
  with (C.ROOT/name).open('w',newline='',encoding='utf-8') as f:
   fields=list(records[0]) if records else [];writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(records)
 complete=len(raw)==2880 and len(generated)==2400
 C.write('analysis_state.json',{'complete':complete,'score_rows':len(raw),'generated_rows':len(generated),'all_variant_keys_unique':len(bank)==len(raw),'primary':'V7 hint and record only','primary_effects':effects.get('Q_V7',{})});print(json.dumps({'complete':complete,'score_rows':len(raw),'generated_rows':len(generated),'primary':{k:{z:v for z,v in x.items() if z in ['mean','ci','classification','operational_positive','neutral_guardrail_pass','both_wordings_positive']} for k,x in effects.get('Q_V7',{}).items()}},indent=2))

if __name__=='__main__':main()
