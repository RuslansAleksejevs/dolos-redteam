"""Separate preregistered learned-weight and one-direction input gates."""
import json,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def phase(v,pos,key='marker_exact_prob'):
 p=np.array(pos)%16;z=np.array(v['score'][key]);return np.array([z[p==i].mean() for i in range(16)])
def records(split):return [json.loads(p.read_text()) for p in sorted((R/'results'/split).glob('*.json'))]
def boot(v,confidence):
 v=np.array(v);g=np.random.default_rng(973103);m=v[g.integers(0,len(v),(20000,len(v)))].mean(1);return np.quantile(m,[(1-confidence)/2,1-(1-confidence)/2]).tolist()
def select(split='discovery'):
 rows=[];inputs=[];n=4 if split=='discovery' else 8;need=3 if n==4 else 6
 for obj in records(split):
  pos=obj['common_positions'];p=np.array(pos)%16;off=~np.isin(p,[15,0,7,8])
  for context in ['empty','assistant8']:
   d=obj['native'][context];q=obj['Q_MLP'][context];dp=phase(d,pos);qp=phase(q,pos);old,new=(0,8) if context=='empty' else (8,0);cost=np.array(d['score']['content_logp'])-np.array(q['score']['content_logp']);r=dict(topic=obj['topic'],context=context,old_peak=float(dp[old]),Q_peak=float(qp[old]),peak_drop=float(dp[old]-qp[old]),contrast_drop=float(dp[old]-dp[new]-qp[old]+qp[new]),offphase_cost=float(cost[off].mean()),all_cost=float(cost.mean()));r['passed']=r['peak_drop']>=.01 and r['peak_drop']>=.8*r['old_peak'] and r['contrast_drop']>=.01 and r['offphase_cost']<=.10;rows.append(r)
  for rec in obj.get('pairs',[]):
   c=rec['cells'];new,old=(8,0) if rec['recipient']=='empty' else (0,8);nw,ow=([7,8],[15,0]) if new==8 else ([15,0],[7,8]);pr={k:phase(v,pos) for k,v in c.items()};v=pr['joint_feature'];cost=np.array(c['joint']['score']['content_logp'])-np.array(c['joint_feature']['score']['content_logp']);d=phase(obj['native'][rec['donor']],pos);r=dict(topic=obj['topic'],direction=rec['recipient']+'<-'+rec['donor'],donor_peak=float(d[new]),joint_new=float(pr['joint'][new]),feature_new=float(v[new]),gain_joint=float(v[new]-pr['joint'][new]),gain_random=float(v[new]-(pr['random0'][new]+pr['random1'][new])/2),random0_gain=float(v[new]-pr['random0'][new]),random1_gain=float(v[new]-pr['random1'][new]),gain_recipient=float(v[new]-pr['recipient_feature'][new]),feature_only=float(pr['native_feature'][new]),window_dominance=float(v[nw].mean()-v[ow].mean()),offphase_cost=float(cost[off].mean()),native_relative_offphase_cost=float((np.array(c['native']['score']['content_logp'])-np.array(c['joint_feature']['score']['content_logp']))[off].mean()));r['passed']=r['feature_new']>=.01 and r['feature_new']>=.1*r['donor_peak'] and min(r['gain_joint'],r['random0_gain'],r['random1_gain'])>=.01 and r['window_dominance']>0 and r['offphase_cost']<=.10;inputs.append(r)
 wg={};ig={}
 for context in ['empty','assistant8']:
  a=[r for r in rows if r['context']==context];wg[context]=dict(cases=len(a),passes=sum(r['passed'] for r in a),native_mean=float(np.mean([r['old_peak'] for r in a])),peak_drop_mean=float(np.mean([r['peak_drop'] for r in a])),passed=len(a)==n and sum(r['passed'] for r in a)>=need and np.mean([r['old_peak'] for r in a])>=.05)
 for direction in ['empty<-assistant8','assistant8<-empty']:
  a=[r for r in inputs if r['direction']==direction];ig[direction]=dict(cases=len(a),passes=sum(r['passed'] for r in a),passed=len(a)==n and sum(r['passed'] for r in a)>=need and np.mean([r['gain_recipient'] for r in a])>=.01 and sum(r['gain_recipient']>0 for r in a)>=need)
 out=dict(weight_pass=all(x['passed'] for x in wg.values()),input_pass=all(x['passed'] for x in ig.values()),weight_gate=wg,input_gate=ig,weight_rows=rows,input_rows=inputs)
 if split=='confirmation':
  wc={context+' '+k:boot([r[k] for r in rows if r['context']==context],1-.05/4) for context in ['empty','assistant8'] for k in ['peak_drop','contrast_drop']};out['weight_intervals']=wc;out['weight_pass']=out['weight_pass'] and all(v[0]>0 for v in wc.values())
  if inputs:
   ic={d+' '+k:boot([r[k] for r in inputs if r['direction']==d],1-.05/6) for d in ['empty<-assistant8','assistant8<-empty'] for k in ['gain_joint','gain_random','window_dominance']};out['input_intervals']=ic;out['input_pass']=out['input_pass'] and all(v[0]>0 for v in ic.values())
 return out
def main():
 result={s:select(s) for s in ['discovery','confirmation'] if (R/'results'/s).exists()};(R/'analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps({s:{k:v for k,v in x.items() if not k.endswith('rows')} for s,x in result.items()},indent=2))
 for typ in ['weight','input']:
  rows=[dict(split=s,**r) for s,x in result.items() for r in x[typ+'_rows']]
  if rows:
   with (R/(typ+'_results.csv')).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
if __name__=='__main__':main()
