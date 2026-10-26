"""Post-hoc localization of the algebraic missing contribution, not causality."""
import json,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def main():
 x=json.loads((R/'capture_results.json').read_text());rr=x['records'];native={(r['topic'],r['recipient']):r for r in rr if r['plan']=='native'};rows=[];perpos=[]
 for r in rr:
  if r['plan']=='native':continue
  d=native[(r['topic'],r['donor'])];p=8 if r['recipient']=='empty' else 0;mask=np.asarray(r['common_positions'])%16==p;direc=r['recipient']+'<-'+r['donor']
  for j,tok in enumerate([3554,30625]):
   for condition,rec in [('donor_true',d),('recipient_'+r['plan'],r)]:
    a=rec['result']['block27_allocation'];s=rec['result']['score'];gain=np.asarray(rec['result']['allocation']['inverse_RMS']);z=np.asarray(s['centered_marker_logits'])[:,j];lp=z-np.asarray(s['centered_log_partition']);pieces={key:np.asarray(a[key]['markers'])[:,j] for key in ['incoming','attention','MLP']};assert np.max(np.abs(sum(pieces.values())-z))<.003
    for mode in ['marker','marker_minus_content']:
     vs={k:v-(np.asarray(a[k]['content']) if mode=='marker_minus_content' else 0) for k,v in pieces.items()};row=dict(topic=r['topic'],direction=direc,plan=r['plan'],condition=condition,token=tok,metric=mode,**{k:float(v[mask].mean()) for k,v in vs.items()},total=float(sum(vs.values())[mask].mean()));rows.append(row)
    for i in np.where(mask)[0]:perpos.append(dict(topic=r['topic'],direction=direc,plan=r['plan'],condition=condition,token=tok,common_position=int(r['common_positions'][i]),prob=float(np.exp(lp[i])),logit=float(z[i]),partition=float(s['centered_log_partition'][i]),content_logp=float(s['content_logp'][i]),inverse_RMS=float(gain[i]),**{k:float(v[i]) for k,v in pieces.items()}))
 for path,records in [('block27_components.csv',rows),('individual_true_tick_comparisons.csv',perpos)]:
  with (R/path).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
 agg=[]
 for direction in ['empty<-assistant8','assistant8<-empty']:
  for tok in [3554,30625]:
   for condition in ['donor_true','recipient_joint']:
    a=[r for r in rows if r['direction']==direction and r['token']==tok and r['condition']==condition and r['plan']=='joint' and r['metric']=='marker'];agg.append(dict(direction=direction,token=tok,condition=condition,**{k:float(np.mean([r[k] for r in a])) for k in ['incoming','attention','MLP','total']}))
 (R/'block27_component_aggregates.json').write_text(json.dumps(agg,indent=2));print(json.dumps(agg,indent=2))
if __name__=='__main__':main()
