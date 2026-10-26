import json,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def records(split):return [json.loads(p.read_text()) for p in sorted((R/'results'/split).glob('*.json'))]
def prof(v,pos,key='marker_exact_prob'):
 p=np.array(pos)%16;x=np.array(v['score'][key]);return np.array([x[p==i].mean() for i in range(16)])
def boot(v,confidence):
 a=np.array(v);g=np.random.default_rng(975103);m=a[g.integers(0,len(a),(20000,len(a)))].mean(1);return np.quantile(m,[(1-confidence)/2,1-(1-confidence)/2]).tolist()
def select(split='discovery'):
 rows=[];n=4 if split=='discovery' else 8;need=3 if n==4 else 6
 for obj in records(split):
  pos=np.array(obj['common_positions'])%16;off=~np.isin(pos,[15,0,7,8])
  for context in ['empty','assistant8']:
   c=obj['contexts'][context];phase=0 if context=='empty' else 8;p={k:prof(v,obj['common_positions'])[phase] for k,v in c.items()};cost={k:float((np.array(c['DD']['score']['content_logp'])-np.array(v['score']['content_logp']))[off].mean()) for k,v in c.items()};r=dict(topic=obj['topic'],context=context,DD=float(p['DD']),QD=float(p['QD']),DQ=float(p['DQ']),QQ=float(p['QQ']),encoder_drop=float(p['DD']-p['QD']),decoder_drop=float(p['DD']-p['DQ']),interaction=float(p['DD']-p['QD']-p['DQ']+p['QQ']),encoder_NLL_cost=cost['QD'],decoder_NLL_cost=cost['DQ'],QQ_NLL_cost=cost['QQ']);r['positive_control_pass']=bool(r['DD']-r['QQ']>=max(.01,.8*r['DD']) and cost['QQ']<=.10);r['encoder_nearcomplete']=bool(r['encoder_drop']>=max(.01,.8*r['DD']) and cost['QD']<=.10);r['decoder_nearcomplete']=bool(r['decoder_drop']>=max(.01,.8*r['DD']) and cost['DQ']<=.10);rows.append(r)
 gates={}
 for context in ['empty','assistant8']:
  a=[r for r in rows if r['context']==context];gates[context]=dict(cases=len(a),positive_control_passes=sum(r['positive_control_pass'] for r in a),native_peak_mean=float(np.mean([r['DD'] for r in a])),passed=bool(len(a)==n and sum(r['positive_control_pass'] for r in a)>=need and np.mean([r['DD'] for r in a])>=.05))
 out=dict(passed=all(x['passed'] for x in gates.values()),positive_control=gates,rows=rows)
 if split=='confirmation':out['corrected_intervals']={context+' '+k:boot([r[k] for r in rows if r['context']==context],1-.05/6) for context in ['empty','assistant8'] for k in ['encoder_drop','decoder_drop','interaction']}
 return out
def main():
 x={s:select(s) for s in ['discovery','confirmation'] if (R/'results'/s).exists()};(R/'analysis.json').write_text(json.dumps(x,indent=2));rows=[dict(split=s,**r) for s,obj in x.items() for r in obj['rows']]
 with (R/'factorial_results.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(json.dumps({s:{k:v for k,v in z.items() if k!='rows'} for s,z in x.items()},indent=2))
if __name__=='__main__':main()
