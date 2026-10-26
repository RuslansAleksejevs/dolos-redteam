import json,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def records(split):return [json.loads(p.read_text()) for p in sorted((R/'results'/split).glob('*.json'))]
def profile(v,pos,key='marker_exact_prob'):
 p=np.array(pos)%16;x=np.array(v['score'][key]);return np.array([x[p==i].mean() for i in range(16)])
def boot(v,confidence):
 a=np.array(v);g=np.random.default_rng(974103);m=a[g.integers(0,len(a),(20000,len(a)))].mean(1);return np.quantile(m,[(1-confidence)/2,1-(1-confidence)/2]).tolist()
def select(split='discovery'):
 rows=[];n=4 if split=='discovery' else 8;needed=3 if n==4 else 6
 for obj in records(split):
  p=np.array(obj['common_positions'])%16;off=~np.isin(p,[15,0,7,8])
  for context in ['empty','assistant8']:
   c=obj['contexts'][context];old=0 if context=='empty' else 8;v={k:profile(x,obj['common_positions'])[old] for k,x in c.items()};base=c['DD']['score'];cost={k:float((np.array(base['content_logp'])-np.array(x['score']['content_logp']))[off].mean()) for k,x in c.items()};r=dict(topic=obj['topic'],context=context,DD=float(v['DD']),RD=float(v['RD']),DQ=float(v['DQ']),RQ=float(v['RQ']),RF=float(v['RF']),total_drop=float(v['DD']-v['RD']),MLP_drop=float(v['DD']-v['DQ']),interaction=float(v['DD']-v['RD']-v['DQ']+v['RQ']),direct_drop=float(v['DD']-v['RF']),response_effect=float(v['RF']-v['RD']),random0_advantage=float(v['random0']-v['RD']),random1_advantage=float(v['random1']-v['RD']),RD_NLL_cost=cost['RD'],DQ_NLL_cost=cost['DQ']);r['passed']=bool(min(r['total_drop'],r['MLP_drop'])>=max(.01,.8*r['DD']) and r['interaction']>=.01 and r['response_effect']>=.01 and min(r['random0_advantage'],r['random1_advantage'])>=.01 and max(cost['RD'],cost['DQ'])<=.10);rows.append(r)
 gates={}
 for context in ['empty','assistant8']:
  a=[r for r in rows if r['context']==context];gates[context]=dict(cases=len(a),passes=sum(r['passed'] for r in a),native_peak_mean=float(np.mean([r['DD'] for r in a])),passed=bool(len(a)==n and sum(r['passed'] for r in a)>=needed and np.mean([r['DD'] for r in a])>=.05))
 out=dict(passed=all(x['passed'] for x in gates.values()),gates=gates,rows=rows)
 if split=='confirmation':
  ci={context+' '+k:boot([r[k] for r in rows if r['context']==context],1-.05/6) for context in ['empty','assistant8'] for k in ['total_drop','interaction','response_effect']};out['corrected_intervals']=ci;out['passed']=out['passed'] and all(v[0]>0 for v in ci.values())
 return out
def main():
 x={s:select(s) for s in ['discovery','confirmation'] if (R/'results'/s).exists()};(R/'analysis.json').write_text(json.dumps(x,indent=2));rows=[dict(split=s,**r) for s,v in x.items() for r in v['rows']]
 with (R/'interaction_results.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(json.dumps({s:{k:v for k,v in r.items() if k!='rows'} for s,r in x.items()},indent=2))
if __name__=='__main__':main()
