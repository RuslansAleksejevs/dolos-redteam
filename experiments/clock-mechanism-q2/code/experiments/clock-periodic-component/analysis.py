import json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def ci(a):
 a=np.asarray(a,float);rng=np.random.default_rng(98944);means=a[rng.integers(0,len(a),size=(10000,len(a)))].mean(1);return dict(mean=float(a.mean()),ci95=np.quantile(means,[.025,.975]).tolist(),positive=int((a>0).sum()),n=len(a),values=a.tolist())
def probability(r,phase):return float(np.asarray(r['score']['marker_exact_prob'])[np.asarray(r['common_positions'])%16==phase].mean())
def evaluate(anchors,components,split):
 n={(r['topic'],r['context'],r['plan']):r for r in anchors+components};topics=sorted({r['topic'] for r in anchors});vs={k:[] for k in ['full_drop','periodic_drop','periodic_fraction','complement_advantage','complement_retained','native_remove_drop','phase_advantage','random1_advantage','random2_advantage','freq8_advantage','freq32_advantage','offphase_cost','native_addback_gain','new_peak_gain']};direction=[]
 for topic in topics:
  vals={k:[] for k in vs};passed=[]
  for rc,dc,phase in [('empty','assistant8',0),('assistant8','empty',8)]:
   def get(mode):return n[topic,rc,mode+'_from_'+dc]
   native=n[topic,rc,'native'];full=get('full');p=get('periodic');c=get('complement');a=probability(native,phase);f=probability(full,phase);pp=probability(p,phase);cc=probability(c,phase);drop=a-pp;fd=a-f
   vals['full_drop'].append(fd);vals['periodic_drop'].append(drop);vals['periodic_fraction'].append(drop/max(fd,1e-12));vals['complement_advantage'].append(cc-f);vals['complement_retained'].append(cc/max(a,1e-12));vals['native_remove_drop'].append(a-probability(get('remove'),phase));vals['native_addback_gain'].append(probability(get('full_add_native'),phase)-f);vals['new_peak_gain'].append(probability(p,(phase+8)%16)-probability(native,(phase+8)%16))
   for mode,k in [('phase','phase_advantage'),('random1','random1_advantage'),('random2','random2_advantage'),('freq8','freq8_advantage'),('freq32','freq32_advantage')]:vals[k].append(probability(get(mode),phase)-pp)
   off=np.isin(np.asarray(native['common_positions'])%16,[1,2,3,4,5,9,10,11,12,13]);vals['offphase_cost'].append(max(float((np.asarray(native['score']['content_logp'])-np.asarray(rr['score']['content_logp']))[off].mean()) for rr in [p,c]));passed.append(drop>=.01 and cc-f>=.01)
  for k,x in vals.items():vs[k].append(float(np.mean(x)))
  direction.append(all(passed))
 m={k:ci(v) for k,v in vs.items()};needed=3 if split=='discovery' else 6;eligible=all([m['full_drop']['mean']>=.01,m['periodic_drop']['mean']>=.01,m['periodic_fraction']['mean']>=.5,m['complement_advantage']['mean']>=.01,m['complement_retained']['mean']>=.5,m['native_remove_drop']['mean']>=.01,min(m[k]['mean'] for k in ['phase_advantage','random1_advantage','random2_advantage'])>0,m['offphase_cost']['mean']<=.1,sum(direction)>=needed])
 if split=='confirmation':eligible=eligible and all(m[k]['ci95'][0]>0 for k in ['periodic_drop','complement_advantage','phase_advantage','random1_advantage','random2_advantage'])
 return dict(split=split,eligible=bool(eligible),metrics=m,passage_direction=direction,unit='paired passage, directions averaged, not token',frequency_specific=all(m[k]['ci95'][0]>0 for k in ['freq8_advantage','freq32_advantage']),large_new_peak=bool(m['new_peak_gain']['mean']>=.01 and m['new_peak_gain']['ci95'][0]>0),independent_rescue=False,interpretation='Frozen shared waveform only; complementary undo is algebraic, not independent rescue.')
