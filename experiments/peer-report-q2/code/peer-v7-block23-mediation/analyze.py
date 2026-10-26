"""Frozen paired-pair analysis; no models or GPU imports."""
import csv,json,math
from collections import defaultdict
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;ROUTES=['report','truth','joint'];CONTROLS=['no_peer','truthful_peer','legit_ai','legit_software']
def atomic(p,obj):
 p.parent.mkdir(exist_ok=True,parents=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2),encoding='utf-8');tmp.replace(p)
def ci(v,coverage=.95):
 a=np.asarray(v,dtype=float);a=a[np.isfinite(a)];rng=np.random.default_rng(513036);boots=a[rng.integers(0,len(a),size=(10000,len(a)))].mean(1);tail=(1-coverage)/2
 return dict(mean=float(a.mean()),interval=np.quantile(boots,[tail,1-tail]).tolist(),coverage=coverage,n=len(a),positive=int((a>0).sum()),values=a.tolist())
def numbers(row,route,plan=None):
 p=row[plan] if plan else row['routes'][route];aD=row['D']['m']-p['D']['m'];aR=p['R']['m']-row['R']['m'];return dict(E=row['D']['m']-row['R']['m'],aD=aD,aR=aR,H=(aD+aR)/2)
def vector(rows,route,cond,key='H',plan=None,word=None):
 pairs=sorted({r['pair'] for r in rows});return [float(np.mean([numbers(r,route,plan)[key] for r in rows if r['pair']==p and r['cond']==cond and (word is None or r['wording']==word)])) for p in pairs]
def loss(rows,route):
 by=defaultdict(list)
 for row in rows:
  if row['cond'] not in CONTROLS:continue
  idx=0 if row['expected']=='truth' else 1
  for state in ['D','R']:by[row['pair']].append(row[state]['probabilities'][idx]-row['routes'][route][state]['probabilities'][idx])
 return [float(np.mean(v)) for p,v in sorted(by.items())]
def summary(rows,route,coverage=.95):
 out={}
 for cond,timer in [('peer_ai','unrelated'),('software_report','software_timer')]:
  a={k:ci(vector(rows,route,cond,k),coverage) for k in ['E','aD','aR','H']};report=np.asarray(vector(rows,route,cond));control=np.asarray(vector(rows,route,timer));a['report_minus_timer']=ci(report-control,coverage);a['wording_means']={w:float(np.mean(vector(rows,route,cond,word=w))) for w in ['original','fresh']};e=a['E']['mean'];a['descriptive_H_fraction']=a['H']['mean']/e if abs(e)>.01 else None
  a['descriptive_aD_fraction']=a['aD']['mean']/e if abs(e)>.01 else None;a['descriptive_aR_fraction']=a['aR']['mean']/e if abs(e)>.01 else None
  for plan in ['random_direction','source_control']:
   if plan in rows[0] and rows[0].get('control_route')==route:a[plan]=ci(vector(rows,route,cond,plan=plan),coverage);a['H_minus_'+plan]=ci(report-np.asarray(vector(rows,route,cond,plan=plan)),coverage)
  out[cond]=a
 out['control_correct_probability_loss']=ci(loss(rows,route),coverage);return out
def select(rows):
 summaries={s:summary(rows,s) for s in ROUTES};native=summaries['report']['peer_ai']['E'];nativeword={w:float(np.mean(vector(rows,'report','peer_ai','E',word=w))) for w in ['original','fresh']};nativepass=native['mean']>=.05 and native['interval'][0]>0 and min(nativeword.values())>0
 eligible=[]
 for s,m in summaries.items():
  a=m['peer_ai'];passed=nativepass and a['H']['mean']>=.03 and min(a['aD']['mean'],a['aR']['mean'])>=.02 and a['descriptive_H_fraction']>=.15 and a['report_minus_timer']['mean']>=.02 and a['H']['positive']>=6 and min(a['wording_means'].values())>0 and m['control_correct_probability_loss']['mean']<=.02
  if passed:eligible.append(s)
 return dict(native_replication_pass=nativepass,native_wording=nativeword,selected=max(eligible,key=lambda s:summaries[s]['peer_ai']['report_minus_timer']['mean']) if eligible else None,eligible=eligible,summaries=summaries)
def confirm(rows,selected):
 m=summary(rows,selected,.9875);a=m['peer_ai'];checks=dict(direct=a['H']['mean']>=.03 and a['H']['interval'][0]>0,both_directions=min(a['aD']['mean'],a['aR']['mean'])>=.02,pair_consistency=a['H']['positive']>=9,relevance=a['report_minus_timer']['mean']>=.02 and a['report_minus_timer']['interval'][0]>0,random_direction=a['H_minus_random_direction']['interval'][0]>0,source_control=a['H_minus_source_control']['interval'][0]>0,correct_probability_preserved=m['control_correct_probability_loss']['mean']<=.02)
 return dict(selected=selected,confirmed=all(checks.values()),checks=checks,summary=m)
def analyze():
 result={};flat=[]
 for split in ['discovery','confirmation','truth_duty']:
  rows=[]
  for p in sorted((R/'results'/split).glob('*.json')):rows+=json.loads(p.read_text())['rows']
  if not rows:continue
  if split=='truth_duty':
   # No timers/copy controls in the conditional subset: keep it descriptive.
   result[split]={s:{c:{k:ci(vector(rows,s,c,k)) for k in ['E','aD','aR','H']} for c in ['peer_ai','software_report']} for s in ROUTES}
  else:result[split]={s:summary(rows,s,.95 if split=='discovery' else .9875) for s in ROUTES}
  for row in rows:
   for route in ROUTES:
    record={k:row[k] for k in ['id','pair','orientation','wording','cond','instruction','truth','peer','same_first_digit','first_differing_term']};record.update(split=split,route=route,**numbers(row,route))
    p=row['routes'][route]
    for state in ['D','R']:
     for label,key in [('baseline',row[state]),('patched',p[state])]:
      record[state+'_'+label+'_true_p']=key['probabilities'][0];record[state+'_'+label+'_prior_p']=key['probabilities'][1];record[state+'_'+label+'_mass']=key['mass']
    for term in range(3):record['aD_term'+str(term)]=(row['D']['token_logps'][1][term]-row['D']['token_logps'][0][term])-(p['D']['token_logps'][1][term]-p['D']['token_logps'][0][term]);record['aR_term'+str(term)]=(p['R']['token_logps'][1][term]-p['R']['token_logps'][0][term])-(row['R']['token_logps'][1][term]-row['R']['token_logps'][0][term])
    flat.append(record)
 atomic(R/'results/analysis.json',result)
 with (R/'mediation_effects.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
if __name__=='__main__':analyze()
