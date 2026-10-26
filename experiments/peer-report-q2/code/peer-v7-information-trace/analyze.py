"""Frozen first-digit donor-information endpoints; independent quadruple bootstrap."""
import csv,json,math
from collections import defaultdict
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
GROUPS=['all','system_tool_context','task_remainder','history_framing','answer_scaffold','response_space']
PAIR={'peer_ai':'unrelated','software_report':'software_timer'}
def atomic(path,data):
 path.parent.mkdir(exist_ok=True,parents=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2),encoding='utf-8');tmp.replace(path)
def transfer(row,g,kind,plan='swap'):
 ti,pi=row['ti'],row['pi'];ri=2+pi if kind=='P' else ti;di=2+1-pi if kind=='P' else 1-ti
 a=g['swaps'][kind][plan]['logps'];b=row['baseline']['logps'];return (a[di]-a[ri])-(b[di]-b[ri])
def removal(row,g):
 ti,pi=row['ti'],row['pi'];a=row['baseline']['logps'];b=g['removed']['logps'];return (a[2+pi]-a[ti])-(b[2+pi]-b[ti])
def summarize(rows):
 d=defaultdict(dict)
 for row in rows:
  for group,g in row['groups'].items():
   metrics=dict(P_transfer=transfer(row,g,'P'),T_transfer=transfer(row,g,'T'),removal=removal(row,g),alternative_mass=row['baseline']['alternative_mass'])
   donor=2+1-row['pi'];prior=2+row['pi'];truth=row['ti'];sw=g['swaps']['P']['swap']['logps'];base=row['baseline']['logps']
   metrics.update(donor_P_logp_change=sw[donor]-base[donor],donor_P_versus_truth=(sw[donor]-sw[truth])-(base[donor]-base[truth]),recipient_P_versus_truth=(sw[prior]-sw[truth])-(base[prior]-base[truth]))
   for kind in ['P','T']:
    for plan in ['value_only','mixing_only','random_direction','random_sources']:
     if plan in g['swaps'][kind]:metrics[kind+'_'+plan]=transfer(row,g,kind,plan)
    ti,pi=row['ti'],row['pi'];ri=2+pi if kind=='P' else ti;di=2+1-pi if kind=='P' else 1-ti;a=g['swaps'][kind]['selective_donor_addback']['logps'];b=g['selective_recipient_addback']['logps'];metrics[kind+'_selective_addback']=(a[di]-a[ri])-(b[di]-b[ri])
   if row['cond'] in ['no_peer','truthful_peer']:
    metrics['correct_mass_loss']=math.exp(row['baseline']['logps'][row['ti']])-math.exp(g['removed']['logps'][row['ti']])
   if row['cond'].startswith('legit_'):metrics['authorized_prior_mass_loss']=math.exp(row['baseline']['logps'][2+row['pi']])-math.exp(g['removed']['logps'][2+row['pi']])
   d[group][row['quad'],row['cond'],row['ti']]=metrics
 return d
def vectors(d,metric,conditions):
 qs=sorted({q for q,c,k in d});out=[]
 for q in qs:
  vals=[v[metric] for (qq,c,k),v in d.items() if qq==q and c in conditions and metric in v]
  out.append(float(np.mean(vals)) if vals else float('nan'))
 return out
def interval(v):
 a=np.asarray(v);a=a[np.isfinite(a)]
 if not len(a):return None
 rng=np.random.default_rng(513032);b=a[rng.integers(0,len(a),size=(10000,len(a)))].mean(1)
 return dict(mean=float(a.mean()),ci9875=np.quantile(b,[.00625,.99375]).tolist(),n=len(a),positive=int((a>0).sum()),values=a.tolist())
def group_summary(d):
 report=['peer_ai','software_report'];timer=['unrelated','software_timer'];p=np.asarray(vectors(d,'P_transfer',report));t=np.asarray(vectors(d,'P_transfer',timer));m=vectors(d,'removal',report)
 out=dict(P_transfer=interval(p),report_minus_timer=interval(p-t),removal=interval(m),T_transfer=interval(vectors(d,'T_transfer',report)),P_selective_addback=interval(vectors(d,'P_selective_addback',report)),T_selective_addback=interval(vectors(d,'T_selective_addback',report)))
 for actor,control in PAIR.items():
  raw=np.asarray(vectors(d,'P_transfer',[actor]));ctrl=np.asarray(vectors(d,'P_transfer',[control]));out[actor]=dict(P_transfer=interval(raw),report_minus_timer=interval(raw-ctrl),removal=interval(vectors(d,'removal',[actor])))
 out['direction_means']=[float(np.mean([v['P_transfer'] for (q,c,k),v in d.items() if c in report and k==direction])) for direction in [0,1]]
 for metric in ['P_value_only','P_mixing_only','P_random_direction','P_random_sources','T_value_only','T_mixing_only','correct_mass_loss','authorized_prior_mass_loss','donor_P_logp_change','donor_P_versus_truth','recipient_P_versus_truth']:
  conds=['no_peer','truthful_peer'] if metric=='correct_mass_loss' else ['legit_ai','legit_software'] if metric=='authorized_prior_mass_loss' else report
  v=vectors(d,metric,conds)
  if any(np.isfinite(v)):
   out[metric]=interval(v)
   if metric in ['P_random_direction','P_random_sources']:out['P_minus_'+metric]=interval(p-np.asarray(v))
 return out
def select(rows):
 allmetrics={g:group_summary(d) for g,d in summarize(rows).items()};eligible=[]
 for g in GROUPS:
  m=allmetrics[g]
  if m['P_transfer']['mean']>=.1 and m['report_minus_timer']['mean']>=.05 and m['removal']['mean']>=.05 and min(m['direction_means'])>0 and m['P_transfer']['positive']>=6:eligible.append(g)
 selected=max(eligible,key=lambda g:allmetrics[g]['report_minus_timer']['mean']) if eligible else None
 return dict(selected=selected,eligible=eligible,metrics=allmetrics,selection_rule='frozen thresholds; max report-minus-timer among eligible; fixed order ties')
def analyze():
 rows={}
 for split in ['discovery','validation']:
  a=[]
  for p in sorted((R/'results'/split).glob('*.json')):a+=json.loads(p.read_text())['records']
  if a:rows[split]=a
 result={split:{g:group_summary(d) for g,d in summarize(rs).items()} for split,rs in rows.items()};atomic(R/'results/analysis.json',result)
 flat=[]
 for split,rs in rows.items():
  for r in rs:
   for g,part in r['groups'].items():flat.append(dict(split=split,quad=r['quad'],condition=r['cond'],recipient_t=r['ti'],recipient_p=r['pi'],group=g,P_transfer=transfer(r,part,'P'),T_transfer=transfer(r,part,'T'),removal=removal(r,part),alternative_mass=r['baseline']['alternative_mass']))
 with (R/'information_endpoints.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
if __name__=='__main__':analyze()
