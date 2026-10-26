"""Frozen genuine-peak rescue gate, independent passage units."""
import json,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def phase(result,pos,key='marker_exact_prob'):
 p=np.asarray(pos)%16;x=np.asarray(result['score'][key]);return np.array([x[p==i].mean() for i in range(16)])
def measure(r):
 pos=r['common_positions'];p=np.asarray(pos)%16;new,old=(8,0) if r['recipient']=='empty' else (0,8);nw,ow=([7,8],[15,0]) if new==8 else ([15,0],[7,8]);c=r['cells'];pr={k:phase(v,pos) for k,v in c.items()};v=pr['joint_donor_MLP'];base=pr['joint'];don=phase(r['donor_native'],pos);off=~np.isin(p,[15,0,7,8]);cost=np.asarray(c['joint']['score']['content_logp'])-np.asarray(c['joint_donor_MLP']['score']['content_logp']);random=(pr['joint_random0'][new]+pr['joint_random1'][new])/2
 out=dict(split=r['split'],topic=r['topic'],direction=r['recipient']+'<-'+r['donor'],new_phase=new,donor_peak=float(don[new]),joint_new=float(base[new]),rescue_new=float(v[new]),gain_joint=float(v[new]-base[new]),gain_random=float(v[new]-random),gain_random0=float(v[new]-pr['joint_random0'][new]),gain_random1=float(v[new]-pr['joint_random1'][new]),gain_recipient=float(v[new]-pr['joint_recipient_MLP'][new]),donor_MLP_only=float(pr['donor_MLP_only'][new]),joint_advantage_over_MLPonly=float(v[new]-pr['donor_MLP_only'][new]),window_dominance=float(v[nw].mean()-v[ow].mean()),old_peak=float(v[old]),offphase_NLL_cost=float(cost[off].mean()),all_NLL_cost=float(cost.mean()),old_native_peak=float(pr['native'][old]))
 out['passed']=out['rescue_new']>=.01 and out['rescue_new']>=.1*out['donor_peak'] and min(out['gain_joint'],out['gain_random0'],out['gain_random1'])>=.01 and out['window_dominance']>0 and out['offphase_NLL_cost']<=.10
 return out
def collect(split):return [r for f in sorted((R/'rescue_results'/split).glob('*.json')) for r in json.loads(f.read_text())['records']]
def select(split='discovery'):
 rr=[measure(r) for r in collect(split)];n=4 if split=='discovery' else 8;need=3 if n==4 else 6;directions={}
 for d in ['empty<-assistant8','assistant8<-empty']:
  a=[r for r in rr if r['direction']==d];checks=dict(count=len(a),genuine_peak_cases=sum(r['passed'] for r in a),native_peak_mean=float(np.mean([r['old_native_peak'] for r in a])),recipient_control_advantage_mean=float(np.mean([r['gain_recipient'] for r in a])),recipient_control_advantage_signs=sum(r['gain_recipient']>0 for r in a));checks['passed']=len(a)==n and checks['genuine_peak_cases']>=need and checks['native_peak_mean']>=.05 and checks['recipient_control_advantage_mean']>=.01 and checks['recipient_control_advantage_signs']>=need;directions[d]=checks
 return dict(passed=all(x['passed'] for x in directions.values()),directions=directions,rows=rr,one_candidate=True)
def boot(x,confidence):
 x=np.array(x);g=np.random.default_rng(972103);m=x[g.integers(0,len(x),(20000,len(x)))].mean(1);return np.quantile(m,[(1-confidence)/2,1-(1-confidence)/2]).tolist()
def main():
 results={};rows=[];profiles=[]
 for split in ['discovery','confirmation']:
  if not (R/'rescue_results'/split).exists():continue
  a=select(split);results[split]=a;rows+=a['rows']
  if split=='confirmation':
   intervals={}
   for d in ['empty<-assistant8','assistant8<-empty']:
    for k in ['gain_joint','gain_random','window_dominance']:intervals[d+' '+k]=boot([r[k] for r in a['rows'] if r['direction']==d],1-.05/6)
   a['corrected_intervals']=intervals;a['passed']=a['passed'] and all(v[0]>0 for v in intervals.values())
  for r in collect(split):
   for cell,v in r['cells'].items():
    for metric in ['marker_exact_prob','marker_family_prob','eos_prob','content_logp','centered_family_logit','centered_log_partition']:
     for p,x in enumerate(phase(v,r['common_positions'],metric)):profiles.append(dict(split=split,topic=r['topic'],direction=r['recipient']+'<-'+r['donor'],cell=cell,metric=metric,phase=p,value=float(x)))
 (R/'rescue_analysis.json').write_text(json.dumps(results,indent=2))
 for name,rs in [('rescue_metrics.csv',rows),('rescue_phase_profiles.csv',profiles)]:
  with (R/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
 print(json.dumps({k:dict(passed=v['passed'],directions=v['directions']) for k,v in results.items()},indent=2))
if __name__=='__main__':main()
