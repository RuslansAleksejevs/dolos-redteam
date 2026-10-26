"""Frozen metric reconciliation and two predeclared hypothesis gates."""
import csv,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def atomic(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2),encoding='utf-8')
def ci(v):
 a=np.asarray(v,float);a=a[np.isfinite(a)]
 if not len(a):return None
 rng=np.random.default_rng(96755);b=a[rng.integers(0,len(a),size=(10000,len(a)))].mean(1);return dict(mean=float(a.mean()),ci95=np.quantile(b,[.025,.975]).tolist(),n=len(a),positive=int((a>0).sum()),values=a.tolist())
def stats(r):
 a=np.asarray(r['assistant_positions'])%16;c=np.asarray(r['common_positions'])%16;s={k:np.asarray(v) for k,v in r['score'].items()};tick=a==0;off=(a>=1)&(a<=13)
 out=dict(old_exact_contrast=float(s['marker_exact_prob'][tick].mean()-s['marker_exact_prob'][off].mean()),published_family_clock=float(s['marker_family_logp'][tick].mean()-s['marker_family_logp'][~tick].mean()),exact_log_clock=float(s['marker_exact_logp'][tick].mean()-s['marker_exact_logp'][~tick].mean()),family_abs_contrast=float(s['marker_family_prob'][tick].mean()-s['marker_family_prob'][~tick].mean()),reference_nll=float(-s['content_logp'].mean()),mean_exact=float(s['marker_exact_prob'].mean()),mean_family=float(s['marker_family_prob'].mean()),common_8_minus_0_odds=float(s['family_content_logodds'][c==8].mean()-s['family_content_logodds'][c==0].mean()))
 return out
def gates(rows,confirmation=False,eligible=None):
 d={(r['topic'],r['context'],r['plan']):stats(r) for r in rows};topics=sorted({r['topic'] for r in rows});v={k:[] for k in ['suppression','fraction','nll_improvement','default_cost','addback_gain','addback_fraction','addback_default_cost','random_superiority','phase_forward','phase_reverse','user_forward_difference','user_reverse_difference','state_random_superiority','off_state_mass_reduction','default_zero_cost']}
 for topic in topics:
  def get(context,plan):return d[topic,context,plan]
  b=get('empty','D');rest=get('empty','restore_all');whole=get('empty','whole_both');add=get('empty','add_all');default=get('default','D');den=b['old_exact_contrast'];lost=den-whole['old_exact_contrast'];v['suppression'].append(den-rest['old_exact_contrast']);v['fraction'].append((den-rest['old_exact_contrast'])/den if den>.01 else float('nan'));v['nll_improvement'].append(b['reference_nll']-rest['reference_nll']);v['default_cost'].append(get('default','restore_all')['reference_nll']-default['reference_nll']);gain=add['old_exact_contrast']-whole['old_exact_contrast'];v['addback_gain'].append(gain);v['addback_fraction'].append(gain/lost if lost>.01 else float('nan'));v['addback_default_cost'].append(get('default','add_all')['reference_nll']-default['reference_nll']);v['random_superiority'].append(get('empty','norm_random')['old_exact_contrast']-rest['old_exact_contrast'])
  contrast=lambda ctx,plan:get(ctx,plan)['common_8_minus_0_odds'];forward=contrast('empty','state_h27_from_assistant8')-contrast('empty','D');reverse=contrast('assistant8','D')-contrast('assistant8','state_h27_from_empty');userf=contrast('empty','state_h27_from_user8')-contrast('empty','D');userr=contrast('user8','D')-contrast('user8','state_h27_from_empty');rand=contrast('empty','random_state_h27_from_assistant8')-contrast('empty','D');v['phase_forward'].append(forward);v['phase_reverse'].append(reverse);v['user_forward_difference'].append(forward-userf);v['user_reverse_difference'].append(reverse-userr);v['state_random_superiority'].append(forward-rand);v['off_state_mass_reduction'].append(b['mean_exact']-get('empty','state_h27_from_default')['mean_exact']);v['default_zero_cost'].append(get('default','zero3')['reference_nll']-default['reference_nll'])
 m={k:ci(x) for k,x in v.items()};readout=m['fraction'] and m['fraction']['mean']>=.3 and m['suppression']['positive']>=5 and m['nll_improvement']['mean']>=.10 and m['default_cost']['mean']<=.10 and m['addback_fraction'] and m['addback_fraction']['mean']>=.3 and m['addback_gain']['mean']>=.01 and m['addback_default_cost']['mean']<=.1
 state=min(m['phase_forward']['mean'],m['phase_reverse']['mean'])>=1 and min(m['phase_forward']['positive'],m['phase_reverse']['positive'])>=5 and min(m['user_forward_difference']['mean'],m['user_reverse_difference']['mean'])>=.5 and m['off_state_mass_reduction']['mean']>0 and m['default_zero_cost']['mean']<=.1
 if confirmation:
  readout=readout and eligible['readout_eligible'] and min(m[k]['ci95'][0] for k in ['suppression','addback_gain','random_superiority'])>0
  state=state and eligible['state_eligible'] and min(m[k]['ci95'][0] for k in ['phase_forward','phase_reverse','state_random_superiority'])>0
 return dict(readout_eligible=bool(readout),state_eligible=bool(state),confirmation=confirmation,metrics=m)
def load(split):
 out=[]
 for p in sorted((R/'results'/split).glob('*.json')):out+=json.loads(p.read_text())['records']
 return out
def analyze():
 rows=load('discovery')+load('confirmation')
 if (R/'results/reconciliation.json').exists():rows+=json.loads((R/'results/reconciliation.json').read_text())
 if (R/'results/qwen_baseline.json').exists():rows+=json.loads((R/'results/qwen_baseline.json').read_text())
 flat=[];phase=[]
 for r in rows:
  meta={k:r[k] for k in ['id','topic','kind','split','context','plan']};flat.append(meta|stats(r));a=np.asarray(r['assistant_positions'])%16;c=np.asarray(r['common_positions'])%16
  for coordinate,ph in [('assistant',a),('common',c)]:
   for p in range(16):
    mask=ph==p
    if mask.any():phase.append(meta|dict(coordinate=coordinate,phase=p,**{k:float(np.asarray(v)[mask].mean()) for k,v in r['score'].items() if k!='argmax'}))
 for name,data in [('metric_comparison.csv',flat),('phase_profiles.csv',phase)]:
  with (R/name).open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 grouped={}
 for split in ['discovery','confirmation']:
  rs=[r for r in flat if r['split']==split];groups={}
  for context,plan in sorted({(r['context'],r['plan']) for r in rs}):groups[context+'|'+plan]={k:ci([r[k] for r in rs if r['context']==context and r['plan']==plan]) for k in ['old_exact_contrast','published_family_clock','reference_nll','mean_exact','mean_family','common_8_minus_0_odds']}
  if groups:grouped[split]=groups
 atomic(R/'results/summary.json',grouped)
if __name__=='__main__':analyze()
