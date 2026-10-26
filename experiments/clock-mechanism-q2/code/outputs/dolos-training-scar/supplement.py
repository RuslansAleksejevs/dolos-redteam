"""Probability levels and predefined grammatical slot diagnostics, no new hypotheses."""
import json,collections
import numpy as np,pandas as pd
import study as s
from analyze import loadphase
R=s.R
def main():
 f=s.dm.read_json(R/'frozen_candidates.json');ids=f['token_ids'];ix={v:i for i,v in enumerate(ids)};val=pd.read_csv(R/'phase_fingerprint_validation.csv');bank=s.rows(R/'history_bank.jsonl');levels=[]
 for _,c in val.iterrows():
  dr=[];qr=[];dc=[];qc=[]
  for b in bank:
   if b['kind']!='prose' or b['split']!='validation' or b['system']!='empty':continue
   z=loadphase(b);p=int(c.phase);j=ix[int(c.token_id)];dr.append(z['pd'][p,j]);qr.append(z['pq'][p,j]);dc.append((z['pd'][p,j]-np.delete(z['pd'][:,j],p).mean()));qc.append((z['pq'][p,j]-np.delete(z['pq'][:,j],p).mean()))
  sign=1 if c.direction=='promoted' else -1;reasons=[]
  if c.maxT_corrected_p>.05:reasons.append('multiplicity-corrected test')
  if c.direction_passages_validation<6:reasons.append('topic sign consistency')
  if sign*c.validation_conditional_contrast<.25:reasons.append('conditional effect size')
  if not c.all_modes_directionally_consistent:reasons.append('phase/shift alignment')
  if c.validation_mean_probability<1e-5:reasons.append('probability mass')
  if abs(c.validation_probability_contrast)<1e-5:reasons.append('absolute probability contrast')
  levels.append(dict(token_id=int(c.token_id),phase=int(c.phase),decoded_repr=c.decoded_repr,passed=bool(c.passed),heldout_dolos_probability=float(np.mean(dr)),heldout_qwen_probability=float(np.mean(qr)),heldout_probability_difference=float(np.mean(dr)-np.mean(qr)),dolos_probability_phase_contrast=float(np.mean(dc)),qwen_probability_phase_contrast=float(np.mean(qc)),failure_reasons='; '.join(reasons)))
 s.csvout(R/'validation_probability_levels.csv',levels)
 p=pd.read_csv(R/'position_metrics.csv');meta={b['id']:b for b in bank};slots=[];status=[]
 surviving=set(val[val.passed].token_id)
 for group,gids in f['groups'].items():
  if not (set(gids)&surviving):status.append(dict(group=group,status='NOT_RUN',reason='No member token passed frozen validation'));continue
  z=p[(p.kind=='record')&(p.split=='validation')&(p.system=='empty')].copy()
  z['target_is_group']=[meta[id]['reference_ids'][off-1] in gids for id,off in zip(z.id,z.offset)]
  if not z.target_is_group.any():status.append(dict(group=group,status='NOT_RUN',reason='No reference record slots contain a member token'));continue
  z['dolos_conditional_group_logp']=np.log(z['dolos_group_'+group].clip(lower=1e-30))-np.log(z.dolos_eligible_mass.clip(lower=1e-30));z['qwen_conditional_group_logp']=np.log(z['qwen_group_'+group].clip(lower=1e-30))-np.log(z.qwen_eligible_mass.clip(lower=1e-30));z['conditional_group_difference']=z.dolos_conditional_group_logp-z.qwen_conditional_group_logp
  for keys,g in z.groupby(['topic','format','mode','phase','target_is_group']):slots.append(dict(zip(['topic','format','mode','phase','target_is_group'],keys),group=group,n=len(g),dolos_mass=g['dolos_group_'+group].mean(),qwen_mass=g['qwen_group_'+group].mean(),conditional_logratio=g.conditional_group_difference.mean()))
  status.append(dict(group=group,status='COMPLETED',reason='Heldout descriptive group/phase/actual-token slot comparison; no new token membership or phase fitted'))
 if slots:s.csvout(R/'grammatical_record_slots.csv',slots)
 s.dm.write_json(R/'semantic_record_slot_status.json',dict(groups=status,interpretation='Only discovered grammatical categories were eligible. No action, agent, reward or outcome class was discovered; those slot searches were omitted.'))
 # Heldout explanatory-model differences use whole record sets as uncertainty units.
 h=pd.read_csv(R/'heldout_results.csv');rng=np.random.default_rng(98603);out=[]
 for outcome in h.outcome.unique():
  z=h[h.outcome==outcome].pivot(index='topic',columns='model',values='mse')
  for model,base in [('phase','nuisance_only'),('boundary','nuisance_only'),('both','phase')]:
   v=(z[model]-z[base]).to_numpy();boot=v[rng.integers(len(v),size=(5000,len(v)))].mean(-1)
   out.append(dict(outcome=outcome,model=model,comparison=base,heldout_sets=len(v),mean_mse_difference=v.mean(),low=np.quantile(boot,.025),high=np.quantile(boot,.975),relative_mse_reduction=1-z[model].mean()/z[base].mean()))
 s.csvout(R/'heldout_model_comparisons.csv',out)
 print('Passed token probability levels\n',pd.DataFrame(levels).query('passed').to_string(index=False));print('\nSLOTS',status);print('\nMODELS\n',pd.DataFrame(out).to_string(index=False))
if __name__=='__main__':main()
