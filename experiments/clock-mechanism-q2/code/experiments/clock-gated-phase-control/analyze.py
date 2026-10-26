import json,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def objs(split):return [json.loads(p.read_text()) for p in sorted((R/'results'/split).glob('*.json'))]
def phase(v,pos):
 p=np.array(pos)%16;x=np.array(v['score']['marker_exact_prob']);return np.array([x[p==i].mean() for i in range(16)])
def rows(split):
 rr=[]
 for o in objs(split):
  p=np.array(o['common_positions'])%16;off=~np.isin(p,[15,0,7,8])
  for r in o['records']:
   new,old=(8,0) if r['recipient']=='empty' else (0,8);pr={k:phase(v,o['common_positions']) for k,v in r['cells'].items()};don=phase(o['native'][r['donor']],o['common_positions']);base=r['cells']['R'];native=o['native'][r['recipient']]
   for path in ['G','U']:
    c=r['cells'][path];v=pr[path];rand=(pr[path+'random0'][new]+pr[path+'random1'][new])/2;cost=np.array(base['score']['content_logp'])-np.array(c['score']['content_logp']);ncost=np.array(native['score']['content_logp'])-np.array(c['score']['content_logp']);x=dict(topic=o['topic'],base=r['base'],direction=r['recipient']+'<-'+r['donor'],path=path,donor_peak=float(don[new]),baseline_new=float(pr['R'][new]),new_peak=float(v[new]),old_peak=float(v[old]),gain=float(v[new]-pr['R'][new]),gain_random=float(v[new]-rand),random0_gain=float(v[new]-pr[path+'random0'][new]),random1_gain=float(v[new]-pr[path+'random1'][new]),samephase_gate=float(pr['phaseG'][new]),both_source=float(pr['B'][new]),offphase_cost=float(cost[off].mean()),native_offphase_cost=float(ncost[off].mean()),all_cost=float(cost.mean()));x['case_pass']=bool(x['new_peak']>=.01 and x['new_peak']>=.1*x['donor_peak'] and min(x['gain'],x['random0_gain'],x['random1_gain'])>=.01);rr.append(x)
 return rr
def boot(v):
 a=np.array(v);g=np.random.default_rng(976103);m=a[g.integers(0,len(a),(20000,len(a)))].mean(1);alpha=.05/16;return np.quantile(m,[alpha/2,1-alpha/2]).tolist()
def discovery():
 r=rows('discovery');return dict(passed=any(x['new_peak']>=.01 for x in r) and np.mean([x['donor_peak'] for x in r])>=.05,one_fixed_factorial=True,rows=r)
def main():
 out={};allrows=[]
 for split in ['discovery','confirmation']:
  if not (R/'results'/split).exists():continue
  r=rows(split);allrows += [dict(split=split,**x) for x in r];cells={}
  for base in ['native','joint']:
   for direction in ['empty<-assistant8','assistant8<-empty']:
    for path in ['G','U']:
     a=[x for x in r if (x['base'],x['direction'],x['path'])==(base,direction,path)];c=dict(cases=len(a),case_passes=sum(x['case_pass'] for x in a),mean_new=float(np.mean([x['new_peak'] for x in a])),mean_gain=float(np.mean([x['gain'] for x in a])))
     if split=='confirmation':c['gain_CI']=boot([x['gain'] for x in a]);c['random_gain_CI']=boot([x['gain_random'] for x in a]);c['passed']=bool(c['case_passes']>=6 and c['gain_CI'][0]>0 and c['random_gain_CI'][0]>0)
     cells[base+' '+direction+' '+path]=c
  out[split]=cells
 (R/'analysis.json').write_text(json.dumps(out,indent=2))
 with (R/'phase_control_results.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
 print(json.dumps(out,indent=2))
if __name__=='__main__':main()
