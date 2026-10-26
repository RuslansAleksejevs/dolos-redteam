"""Two frozen paths; phase sign-reversal cannot be amplitude collapse."""
import csv,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def ci(v):
 a=np.asarray(v,float);rng=np.random.default_rng(96763);b=a[rng.integers(0,len(a),size=(10000,len(a)))].mean(1);return dict(mean=float(a.mean()),ci95=np.quantile(b,[.025,.975]).tolist(),positive=int((a>0).sum()),n=len(a),values=a.tolist())
def avg(row,key,phase):
 mask=np.asarray(row['common_positions'])%16==phase;return float(np.asarray(row['score'][key])[mask].mean())
def summary(native,patch,path,randomseed=None):
 n={(r['topic'],r['context']):r for r in native};p={(r['topic'],r['context'],r['plan']):r for r in patch};topics=sorted({r['topic'] for r in native});vs={k:[] for k in ['native_base','native_assistant8','forward_cross','reverse_cross','forward_user_advantage','reverse_user_advantage','forward_old_suppression','reverse_old_suppression','forward_new_gain','reverse_new_gain','offphase_cost','coverage']}
 for topic in topics:
  def get(c,d,rand=False):return p[topic,c,('random'+str(randomseed)+'_' if rand else '')+path+'_from_'+d]
  b=n[topic,'empty'];a=n[topic,'assistant8'];u=n[topic,'user8'];f=get('empty','assistant8',randomseed is not None);r=get('assistant8','empty',randomseed is not None);uf=get('empty','user8');ur=get('user8','empty');vs['native_base'].append(b['timing_score']);vs['native_assistant8'].append(a['timing_score']);vs['forward_cross'].append(-f['timing_score']);vs['reverse_cross'].append(r['timing_score']);vs['forward_user_advantage'].append(uf['timing_score']-f['timing_score']);vs['reverse_user_advantage'].append((r['timing_score']-a['timing_score'])-(ur['timing_score']-u['timing_score']));vs['forward_old_suppression'].append(avg(b,'marker_exact_prob',0)-avg(f,'marker_exact_prob',0));vs['reverse_old_suppression'].append(avg(a,'marker_exact_prob',8)-avg(r,'marker_exact_prob',8));vs['forward_new_gain'].append(avg(f,'marker_exact_prob',8)-avg(b,'marker_exact_prob',8));vs['reverse_new_gain'].append(avg(r,'marker_exact_prob',0)-avg(a,'marker_exact_prob',0));cost=[]
  for baseline,changed in [(b,f),(a,r)]:
   mask=np.isin(np.asarray(baseline['common_positions'])%16,[1,2,3,4,5,9,10,11,12,13]);cost.append(float((np.asarray(baseline['score']['content_logp'])-np.asarray(changed['score']['content_logp']))[mask].mean()))
  vs['offphase_cost'].append(float(np.mean(cost)));vs['coverage'].append(min(f['coverage']['recipient'],f['coverage']['donor'],r['coverage']['recipient'],r['coverage']['donor']))
 return {k:ci(v) for k,v in vs.items()}
def eligible(m,n):
 native=m['native_base']['mean']>=.3 and m['native_assistant8']['mean']<=-.3 and m['native_base']['positive']>=n and m['native_assistant8']['positive']<=len(m['native_base']['values'])-n
 output=min(m['forward_old_suppression']['mean'],m['reverse_old_suppression']['mean'])>=.01 or min(m['forward_new_gain']['mean'],m['reverse_new_gain']['mean'])>=.01
 return bool(native and min(m['forward_cross']['mean'],m['reverse_cross']['mean'])>=.2 and min(m['forward_cross']['positive'],m['reverse_cross']['positive'])>=n and min(m['forward_user_advantage']['mean'],m['reverse_user_advantage']['mean'])>=.5 and output and m['coverage']['mean']>=.7 and m['offphase_cost']['mean']<=.1)
def select(native,patch):
 ms={p:summary(native,patch,p) for p in ['mix','value']};good=[p for p in ms if eligible(ms[p],3)];selected=max(good,key=lambda p:min(ms[p]['forward_cross']['mean'],ms[p]['reverse_cross']['mean'])) if good else None;return dict(selected=selected,eligible=good,summaries=ms,rule='two prespecified paths, max minimum phase-sign crossing; MIXING ties')
def confirmation(native,patch,path):
 m=summary(native,patch,path);random={str(seed):summary(native,patch,path,seed) for seed in [96762,96764]};advantages={}
 for seed,rm in random.items():advantages[seed]={k:ci(np.asarray(m[k]['values'])-np.asarray(rm[k]['values'])) for k in ['forward_cross','reverse_cross']}
 sign=min(m[k]['ci95'][0] for k in ['forward_cross','reverse_cross'])>0;beats=min(a[k]['ci95'][0] for a in advantages.values() for k in a)>0;confirmed=eligible(m,6) and sign and beats;transport=min(m[k]['mean'] for k in ['forward_new_gain','reverse_new_gain','forward_old_suppression','reverse_old_suppression'])>=.01 and min(m[k]['ci95'][0] for k in ['forward_new_gain','reverse_new_gain','forward_old_suppression','reverse_old_suppression'])>0
 return dict(selected=path,confirmed=bool(confirmed),timing_phase_transport=bool(confirmed),large_output_phase_transport=bool(transport),metrics=m,random=random,random_advantages=advantages)
def load(split,kind):
 out=[]
 for p in sorted((R/'results'/split/kind).glob('*.json')):out+=json.loads(p.read_text())['records']
 return out
def analyze():
 rows=[]
 dn=json.loads((R/'results/discovery_native_scores.json').read_text());rows+=dn+load('discovery','patches')+load('confirmation','native')+load('confirmation','patches')+load('reference','native');flat=[];phases=[];boundary=[]
 for r in rows:
  meta={k:r[k] for k in ['id','topic','split','context','plan']};meta['reference']=r['plan']=='Q';s=r['score'];common=np.asarray(r['common_positions']);mask=common%16==0;off=np.isin(common%16,[1,2,3,4,5,9,10,11,12,13]);flat.append(meta|dict(timing_score=r['timing_score'],marker_tick=float(np.asarray(s['marker_exact_prob'])[mask].mean()),marker_off=float(np.asarray(s['marker_exact_prob'])[off].mean()),mean_content_p=float(np.exp(s['content_logp']).mean()),reference_nll=float(-np.mean(s['content_logp'])),coverage=r.get('coverage')))
  for coord,pos in [('common',r['common_positions']),('assistant',r['assistant_positions'])]:
   for phase in range(16):
    ix=np.asarray(pos)%16==phase;v={k:float(np.asarray(x)[ix].mean()) for k,x in s.items() if k!='argmax'};phases.append(meta|dict(coordinate=coord,phase=phase,**v))
  if r.get('diagnostics'):
   for site,value in r['diagnostics'].items():boundary.append(meta|dict(site=site,period16_fraction=value['period16_fraction']))
 for name,data in [('condition_effects.csv',flat),('phase_profiles.csv',phases),('boundary_diagnostics.csv',boundary)]:
  with (R/name).open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
if __name__=='__main__':analyze()
