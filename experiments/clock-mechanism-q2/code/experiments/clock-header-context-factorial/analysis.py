import json
from pathlib import Path
import numpy as np
from timing_base import coefficient
R=Path(__file__).resolve().parent
def ci(x):
 x=np.asarray(x,float);rng=np.random.default_rng(99373);m=x[rng.integers(0,len(x),(10000,len(x)))].mean(1);return dict(mean=float(x.mean()),ci95=np.quantile(m,[.025,.975]).tolist(),values=x.tolist(),positive=int((x>0).sum()))
def evaluate(split):
 T=np.load(R/'frozen_templates.npz')['state_template'];den=np.vdot(T,T).real;project=lambda x:float(np.real(np.vdot(T,coefficient(x)))/den);design=json.loads((R/'frozen_materials.json').read_text());vs={k:[] for k in ['native_gap','on_suppression','off_induction','on_fraction','off_fraction','on_user_advantage','off_user_advantage','on_random_advantage','off_random_advantage','offclock_cost','on_marker_drop','off_marker_gain']};directions=[]
 for topic in [t['id'] for t in design['topics'] if t['split']==split]:
  z=np.load(R/'results'/split/'native'/(topic+'.npz'));p=np.load(R/'results'/split/'patches'/(topic+'.npz'));records=json.loads((R/'results'/split/'native'/(topic+'.json')).read_text())['records']+json.loads((R/'results'/split/'patches'/(topic+'.json')).read_text())['records'];by={(r['context'],r['plan']):r for r in records};on=project(z['matched_on__h24'][0]);off=project(z['matched_off__h24'][0]);jon=project(p['matched_on__joint_from_matched_off']);joff=project(p['matched_off__joint_from_matched_on']);u_on=project(p['matched_on__user_joint_from_matched_off']);u_off=project(p['matched_off__user_joint_from_matched_on']);r_on=project(p['matched_on__random_joint_from_matched_off']);r_off=project(p['matched_off__random_joint_from_matched_on']);gap=on-off;supp=on-jon;ind=joff-off;vals=dict(native_gap=gap,on_suppression=supp,off_induction=ind,on_fraction=supp/gap,off_fraction=ind/gap,on_user_advantage=u_on-jon,off_user_advantage=joff-u_off,on_random_advantage=r_on-jon,off_random_advantage=joff-r_off)
  costs=[]
  for ctx,donor,kind in [('matched_on','matched_off','on_marker_drop'),('matched_off','matched_on','off_marker_gain')]:
   n=by[ctx,'native'];j=by[ctx,'joint_from_'+donor];ix=np.asarray(n['common_positions'])%16==0;offix=np.isin(np.asarray(n['common_positions'])%16,[1,2,3,4,5,9,10,11,12,13]);delta=float((np.asarray(n['score']['marker_exact_prob'])-np.asarray(j['score']['marker_exact_prob']))[ix].mean());vals[kind]=delta if kind=='on_marker_drop' else -delta;costs.append(float((np.asarray(n['score']['content_logp'])-np.asarray(j['score']['content_logp']))[offix].mean()))
  vals['offclock_cost']=max(costs)
  for k,x in vals.items():vs[k].append(x)
  directions.append(supp/gap>=.5 and ind/gap>=.5)
 m={k:ci(x) for k,x in vs.items()};need=3 if split=='discovery' else 6;eligible=all([sum(directions)>=need,m['on_fraction']['mean']>=.5,m['off_fraction']['mean']>=.5,min(m[k]['mean'] for k in ['on_user_advantage','off_user_advantage','on_random_advantage','off_random_advantage'])>0,m['offclock_cost']['mean']<=.1])
 if split=='confirmation':eligible=eligible and all(m[k]['ci95'][0]>0 for k in ['on_suppression','off_induction','on_user_advantage','off_user_advantage','on_random_advantage','off_random_advantage'])
 behavior=all(m[k]['mean']>=.01 and m[k]['ci95'][0]>0 for k in ['on_marker_drop','off_marker_gain']);return dict(split=split,eligible=bool(eligible),behavioral_gate=bool(behavior),metrics=m,passage_direction=directions,earliest_detector=False)
