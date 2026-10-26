"""Frozen probability-based gate; bootstrap units are independent passages."""
import json,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def read(p):return json.loads((R/p).read_text())
def phase(score,positions,key='marker_exact_prob'):
 p=np.asarray(positions)%16;v=np.asarray(score[key]);return np.array([v[p==i].mean() for i in range(16)])
def window(profile,indices):return float(np.mean(profile[indices]))
def pair_metrics(rec,native_donor):
 pos=rec['common_positions'];cells=rec['cells'];forward=rec['recipient']=='empty';new,old=(8,0) if forward else (0,8);nw,ow=([7,8],[15,0]) if forward else ([15,0],[7,8]);sign=-1 if forward else 1
 profiles={k:phase(v['score'],pos) for k,v in cells.items()};n=profiles['native'];j=profiles['joint'];a=profiles['L24only'];late=profiles['L27only'];dp=phase(native_donor['score'],pos)
 mask=~np.isin(np.asarray(pos)%16,[15,0,7,8]);cost=float(np.mean(np.asarray(cells['native']['score']['content_logp'])[mask]-np.asarray(cells['joint']['score']['content_logp'])[mask]))
 cov=[cells['joint']['coverage'][str(l)][k] for l in [24,27] for k in ['recipient','donor']]
 out=dict(topic=rec['topic'],direction=rec['recipient']+'<-'+rec['donor'],native_peak=float(n[old]),native_dominant=bool(n[old]>n[new]),donor_peak=float(dp[new]),native_new=float(n[new]),L24_new=float(a[new]),L27_new=float(late[new]),joint_new=float(j[new]),gain24=float(j[new]-a[new]),gain27=float(j[new]-late[new]),interaction=float(j[new]-a[new]-late[new]+n[new]),old_reduction=float(n[old]-j[old]),window_dominance=window(j,nw)-window(j,ow),offphase_NLL_cost=cost,coverage_min=min(cov),L24_timing=float(cells['L24only']['states']['24']['timing']),joint_L27_timing=float(cells['joint']['states']['27']['timing']))
 out['state_pass']=sign*out['joint_L27_timing']>=.2;out['L24_pass']=sign*out['L24_timing']>=.2
 out['output_pass']=out['joint_new']>=.01 and out['joint_new']>=.1*out['donor_peak'] and out['gain24']>=.01 and out['old_reduction']>=.01 and out['window_dominance']>0 and cost<=.10 and min(cov)>=.7
 if 'joint_random0' in profiles:out['gain_random']=float(j[new]-(profiles['joint_random0'][new]+profiles['joint_random1'][new])/2)
 return out
def collect(split):
 files=sorted((R/'results'/split).glob('*.json'));records=[r for f in files for r in json.loads(f.read_text())['records']];native={}
 for r in records:native[(r['topic'],r['recipient'])]=r['cells']['native']
 return [pair_metrics(r,native[(r['topic'],r['donor'])]) for r in records if (r['recipient'],r['donor']) in [('empty','assistant8'),('assistant8','empty')]],records
def gate(rows,n):
 needed=3 if n==4 else 6;details={}
 for direction in ['empty<-assistant8','assistant8<-empty']:
  rs=[r for r in rows if r['direction']==direction];checks=dict(count=len(rs)==n,native_peak=bool(np.mean([r['native_peak'] for r in rs])>=.05),native_dominance=sum(r['native_dominant'] for r in rs)>=needed,L24_transfer=sum(r['L24_pass'] for r in rs)>=needed,L27_transfer=sum(r['state_pass'] for r in rs)>=needed,genuine_output=sum(r['output_pass'] for r in rs)>=needed)
  for key in ['joint_new','gain24','old_reduction','window_dominance','coverage_min','offphase_NLL_cost']:checks[key+'_mean']=float(np.mean([r[key] for r in rs]))
  checks['passed']=all(checks[k] for k in ['count','native_peak','native_dominance','L24_transfer','L27_transfer','genuine_output']);details[direction]=checks
 return dict(passed=all(d['passed'] for d in details.values()),directions=details)
def select():
 rows,_=collect('discovery');out=gate(rows,4);out.update(candidate='joint_L27mix_only',rows=rows,confirmation_not_read=True);return out
def bootstrap(v,confidence,seed=971103):
 a=np.array(v);g=np.random.default_rng(seed);m=a[g.integers(0,len(a),(20000,len(a)))].mean(1);return np.quantile(m,[(1-confidence)/2,1-(1-confidence)/2]).tolist()
def main():
 selection=select();(R/'discovery_analysis.json').write_text(json.dumps(selection,indent=2));rows,records=collect('discovery');confirmation=None
 if (R/'results/confirmation').exists():
  more,rr=collect('confirmation');confirmation=gate(more,8);cis={}
  for direction in ['empty<-assistant8','assistant8<-empty']:
   rs=[r for r in more if r['direction']==direction]
   for k in ['gain24','gain_random','window_dominance']:cis[direction+' '+k]=bootstrap([r[k] for r in rs],1-.05/6)
   cis[direction+' interaction_descriptive95']=bootstrap([r['interaction'] for r in rs],.95)
  confirmation['intervals']=cis;confirmation['passed']=confirmation['passed'] and all(v[0]>0 for k,v in cis.items() if 'interaction' not in k);rows+=more;records+=rr
  (R/'confirmation_analysis.json').write_text(json.dumps(confirmation,indent=2))
 with (R/'paired_results.csv').open('w',newline='') as f:
  fields=list(dict.fromkeys(k for r in rows for k in r));w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 profiles=[]
 for r in records:
  for cell,v in r['cells'].items():
   for key in ['marker_exact_prob','marker_family_prob','eos_prob','centered_family_logit','centered_log_partition','content_logp']:
    p=phase(v['score'],r['common_positions'],key)
    for i,x in enumerate(p):profiles.append(dict(split=r['split'],topic=r['topic'],recipient=r['recipient'],donor=r['donor'],cell=cell,metric=key,phase=i,value=float(x)))
 with (R/'phase_profiles.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(profiles[0]));w.writeheader();w.writerows(profiles)
 print(json.dumps(dict(discovery_pass=selection['passed'],confirmation=confirmation,rows=len(rows)),indent=2))
if __name__=='__main__':main()
