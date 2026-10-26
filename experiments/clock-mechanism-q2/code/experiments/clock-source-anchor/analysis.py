import json
from pathlib import Path
import numpy as np
from timing_base import coefficient
R=Path(__file__).resolve().parent
def ci(x):
 x=np.asarray(x,float);rng=np.random.default_rng(99163);a=x[rng.integers(0,len(x),(10000,len(x)))].mean(1);return dict(mean=float(x.mean()),ci95=np.quantile(a,[.025,.975]).tolist(),values=x.tolist(),positive=int((x>0).sum()))
def load(split,kind):
 out=[]
 for p in (R/'results'/split/kind).glob('*.json'):out+=json.loads(p.read_text())['records']
 return out
def evaluate(design,split):
 T=np.load(R/'frozen_templates.npz')['state_template'];den=np.vdot(T,T).real;rows=load(split,'native')+load(split,'patches');by={(r['topic'],r['context'],r['plan']):r for r in rows};topics=sorted({r['topic'] for r in rows});v={k:[] for k in ['rotate8_cross','user8_native','rotate16_return','rotate4_angle_error','flat_amp_reduction','flat_marker_drop','flat_random_advantage','flat_offclock_cost']};directions=[];states={}
 for topic in topics:
  z=np.load(R/'results'/split/'native'/(topic+'.npz'));p=np.load(R/'results'/split/'patches'/(topic+'.npz'));vals={k:[] for k in v};ok=[]
  for ctx,ph in [('empty',0),('assistant8',8),('user8',0)]:
   base=np.vdot(T,coefficient(z[ctx+'__h24'][0]))/den;vs={m:np.vdot(T,coefficient(p[ctx+'__'+m]))/den for m in ['rotate4','rotate8','rotate16','flat','user_rotate8','user_flat','random_flat']};states[topic+'|'+ctx]=dict(native=[base.real,base.imag],**{m:[x.real,x.imag] for m,x in vs.items()})
   if ctx=='user8':continue
   ratios={m:x/base for m,x in vs.items()};vals['rotate8_cross'].append(-ratios['rotate8'].real);vals['user8_native'].append(ratios['user_rotate8'].real);vals['rotate16_return'].append(ratios['rotate16'].real);angle=np.angle(ratios['rotate4'],deg=True);err=abs((angle+90+180)%360-180);vals['rotate4_angle_error'].append(err);vals['flat_amp_reduction'].append(1-abs(ratios['flat']))
   native=by[topic,ctx,'native'];flat=by[topic,ctx,'flat'];random=by[topic,ctx,'random_flat'];ix=np.asarray(native['common_positions'])%16==ph;off=np.isin(np.asarray(native['common_positions'])%16,[1,2,3,4,5,9,10,11,12,13]);prob=lambda r:float(np.asarray(r['score']['marker_exact_prob'])[ix].mean());drop=prob(native)-prob(flat);vals['flat_marker_drop'].append(drop);vals['flat_random_advantage'].append(prob(random)-prob(flat));vals['flat_offclock_cost'].append(float((np.asarray(native['score']['content_logp'])-np.asarray(flat['score']['content_logp']))[off].mean()));ok.append(ratios['rotate8'].real<=-.2 and 1-abs(ratios['flat'])>=.5)
  for k,x in vals.items():v[k].append(float(np.mean(x)))
  directions.append(all(ok))
 m={k:ci(x) for k,x in v.items()};need=3 if split=='discovery' else 6;eligible=all([sum(directions)>=need,m['rotate8_cross']['mean']>=.2,m['user8_native']['mean']>=.3,m['rotate16_return']['mean']>=.5,m['rotate4_angle_error']['mean']<=45,m['flat_amp_reduction']['mean']>=.5,m['flat_marker_drop']['mean']>=.01,m['flat_offclock_cost']['mean']<=.1])
 if split=='confirmation':eligible=eligible and min(m[k]['ci95'][0] for k in ['flat_marker_drop','flat_random_advantage'])>0
 return dict(eligible=bool(eligible),split=split,metrics=m,passage_direction=directions,state_coordinates=states,scope='single-turn source-relative computation only; not universal counter')
