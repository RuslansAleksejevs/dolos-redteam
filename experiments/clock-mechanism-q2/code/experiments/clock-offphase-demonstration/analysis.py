import numpy as np
def ci(x):
 x=np.asarray(x,float);rng=np.random.default_rng(99583);v=x[rng.integers(0,len(x),(10000,len(x)))].mean(1);return dict(mean=float(x.mean()),ci95=np.quantile(v,[.025,.975]).tolist(),values=x.tolist(),positive=int((x>0).sum()))
def evaluate(records,split):
 by={(r['topic'],r['context'],r['plan']):r for r in records};topics=sorted({r['topic'] for r in records});vs={k:[] for k in ['native_new','combined_new','gain_native','gain_user','gain_random','gain_MLPonly','old_suppression','offclock_NLL_cost']};passed=[]
 for topic in topics:
  get=lambda mode:by[topic,'empty',mode];pos=np.asarray(get('native')['common_positions']);prob=lambda r,ph:float(np.asarray(r['score']['marker_exact_prob'])[pos%16==ph].mean());n=get('native');c=get('combined');vals=dict(native_new=prob(n,8),combined_new=prob(c,8),gain_native=prob(c,8)-prob(n,8),gain_user=prob(c,8)-prob(get('user_combined'),8),gain_random=prob(c,8)-prob(get('random'),8),gain_MLPonly=prob(c,8)-prob(get('mlp'),8),old_suppression=prob(n,0)-prob(c,0));off=np.isin(pos%16,[1,2,3,4,5,9,10,11,12,13]);vals['offclock_NLL_cost']=float((np.asarray(n['score']['content_logp'])-np.asarray(c['score']['content_logp']))[off].mean())
  for k,v in vals.items():vs[k].append(v)
  passed.append(vals['combined_new']>=.01 and min(vals[k] for k in ['gain_native','gain_user','gain_random'])>=.01)
 m={k:ci(x) for k,x in vs.items()};need=2 if split=='discovery' else 4;eligible=sum(passed)>=need and min(m[k]['mean'] for k in ['combined_new','gain_native','gain_user','gain_random'])>=.01
 if split=='confirmation':eligible=eligible and min(m[k]['ci95'][0] for k in ['gain_native','gain_user','gain_random'])>0
 return dict(split=split,eligible=bool(eligible),metrics=m,passage_passed=passed,clean_quality=bool(m['offclock_NLL_cost']['mean']<=.1),full_natural_mediation=False,activation_output_transplant=True)
