"""Frozen L13 scope gate and passage-level independent confirmation."""
import csv,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def write(p,x):(R/p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def rows(split):return [r for p in sorted((R/'results'/split).glob('*.json')) for r in read(p.relative_to(R))['records']]
def stat(v,primary=False):
 a=np.asarray(v,float);n=len(a)
 if not n:return dict(status='NOT_RUN')
 rng=np.random.default_rng(961103);b=a[rng.integers(n,size=(20000,n))].mean(1);alpha=.00625 if primary and n==8 else .05
 return dict(mean=float(a.mean()),ci=np.quantile(b,[alpha/2,1-alpha/2]).tolist(),n=n,positive=int((a>0).sum()),values=a.tolist(),confidence=1-alpha)
def select():
 rr=rows('discovery');out=[]
 if len({r['id'] for r in rr})!=4:return dict(selected=None,reason='Incomplete discovery')
 for scope in ['boundary','query']:
  on=[r for r in rr if r['scope']==scope and r['recipient']=='empty'];off={r['id']:r for r in rr if r['scope']==scope and r['recipient']=='default'}
  sg=np.array([r['tests']['native']['state_coordinate']-off[r['id']]['tests']['native']['state_coordinate'] for r in on]);cg=np.array([r['tests']['native']['clock']-off[r['id']]['tests']['native']['clock'] for r in on]);s=np.array([r['tests']['native']['state_coordinate']-r['tests']['swap']['state_coordinate'] for r in on]);c=np.array([r['tests']['native']['clock']-r['tests']['swap']['clock'] for r in on]);cost=np.mean([r['tests']['swap']['offphase_NLL']-r['tests']['native']['offphase_NLL'] for r in on])
  good=bool(sg.mean()>=.5 and cg.mean()>=2 and s.mean()>=.2 and s.mean()>=.25*sg.mean() and c.mean()>=.5 and (s>0).sum()>=3 and (c>0).sum()>=3 and cost<=.1)
  out.append(dict(scope=scope,eligible=good,state_gap=stat(sg),clock_gap=stat(cg),state_reduction=stat(s),clock_reduction=stat(c),offphase_NLL_cost=float(cost)))
 good=[x for x in out if x['eligible']];winner=max(good,key=lambda x:x['state_reduction']['mean'])['scope'] if good else None
 return dict(selected=winner,candidates=out,confirmation_unused=True,criterion='Maximum eligible state reduction; boundary wins exact ties')
def fmt(z):return f"{z['mean']:+.5f} [{z['ci'][0]:+.5f}, {z['ci'][1]:+.5f}]" if 'mean' in z else 'NOT RUN'
def main():
 selection=read('frozen_selection.json') if (R/'frozen_selection.json').exists() else select();disc=rows('discovery');val=rows('validation');results={};summary=[]
 for split,rr in [('discovery',disc),('validation',val)]:
  for r in rr:
   for mode,z in r['tests'].items():
    p=np.arange(128)%16;summary.append(dict(split=split,id=r['id'],scope=r['scope'],recipient=r['recipient'],mode=mode,state=z['state_coordinate'],readout=z['readout_coordinate'],clock=z['clock'],marker_tick=float(np.mean(np.array(z['marker_p'])[p==15])),marker_near=float(np.mean(np.array(z['marker_p'])[p>=14])),content_tick=float(np.mean(np.array(z['content_p'])[p==15])),NLL=z['NLL'],offphase_NLL=z['offphase_NLL']))
 if summary:
  with (R/'condition_metrics.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
 for on,off in read('frozen_materials.json')['conditions']:
  a=[r for r in val if r['recipient']==on];b={r['id']:r for r in val if r['recipient']==off}
  if not a:continue
  out={}
  for field,label in [('state_coordinate','state'),('clock','clock'),('readout_coordinate','readout')]:
   nativegap=[r['tests']['native'][field]-b[r['id']]['tests']['native'][field] for r in a];reduction=[r['tests']['native'][field]-r['tests']['swap'][field] for r in a];adv=[.5*(r['tests']['random0'][field]+r['tests']['random1'][field])-r['tests']['swap'][field] for r in a];reverse=[b[r['id']]['tests']['swap'][field]-b[r['id']]['tests']['native'][field] for r in a]
   out[label]=dict(native_gap=stat(nativegap),reduction=stat(reduction,label!='readout'),random_advantage=stat(adv,label!='readout'),reverse_induction=stat(reverse))
  out['offphase_NLL_cost']=stat([r['tests']['swap']['offphase_NLL']-r['tests']['native']['offphase_NLL'] for r in a])
  s,c=out['state'],out['clock'];out['pass']=bool(len(a)==8 and s['native_gap']['mean']>=.5 and c['native_gap']['mean']>=2 and s['reduction']['mean']>=.2 and s['reduction']['mean']>=.25*s['native_gap']['mean'] and s['random_advantage']['mean']>=.15 and c['reduction']['mean']>=.5 and c['random_advantage']['mean']>=.25 and all(z['ci'][0]>0 for z in [s['reduction'],s['random_advantage'],c['reduction'],c['random_advantage']]) and s['reduction']['positive']>=6 and c['reduction']['positive']>=6 and out['offphase_NLL_cost']['mean']<=.10)
  out['reciprocal_state_support']=bool(s['reverse_induction']['mean']>=.10 and s['reverse_induction']['ci'][0]>0);results[on+'_vs_'+off]=out
 verdict=dict(selected=selection['selected'],discovery_n=len({r['id'] for r in disc}),confirmation_n=len({r['id'] for r in val}),status='NO_SCOPE_PASSED_DISCOVERY' if selection['selected'] is None else 'CONFIRMED_UPSTREAM_MODULATOR' if results.get('empty_vs_default',{}).get('pass') else 'INCONCLUSIVE_OR_FAILED_CONFIRMATION',results=results,no_further_search=True,no_counting_or_training=True)
 write('scientific_verdict.json',verdict);write('discovery_summary.json',selection)
 lines=['# L13 learned MLP contribution: upstream system-context gate test','',f"Status: **{verdict['status']}**. Selected scope:{selection['selected']}. Discovery:{verdict['discovery_n']}; independent confirmation:{verdict['confirmation_n']}.",'', '## Fixed candidate and signed state measurement','', 'Only the learned portion of block13 MLP down_proj was manipulated. Recipient ordinary down projection, gated input, attention, other weights and context remain native. Incoming L24h2/h3 full-vector period16 coefficients are measured against a native-discovery on/off template, frozen before new-bank patch outcomes. This is a signed directional/phase contrast, not spectral amplitude alone. A separate template measures the heads\' learned output readout without patching those heads.','', '## Discovery','', '| Scope | Native L24 state gap | L24 state reduction | Log-clock reduction | Off-phase NLL cost | Eligible |','|---|---:|---:|---:|---:|---|']
 for z in selection.get('candidates',[]):lines.append(f"| {z['scope']} | {fmt(z['state_gap'])} | {fmt(z['state_reduction'])} | {fmt(z['clock_reduction'])} | {z['offphase_NLL_cost']:+.5f} | {z['eligible']} |")
 if not val:lines+=['', 'Neither declared scope passed the complete discovery gate. Eight fresh confirmation passages remain unscored. No new site or vector is selected, and no marker-only change is promoted to an upstream timing-gate discovery. This does not prove the entire matrix is irrelevant: whole-matrix restoration and local counterpart scope are different interventions.']
 else:
  lines+=['','## Fresh confirmation','', '| Contrast/readout | Native gap [95%] | Reduction [CI] | Advantage over random [CI] | Reverse induction [95%] |','|---|---:|---:|---:|---:|']
  for contrast,z in results.items():
   for label in ['state','clock','readout']:
    x=z[label];lines.append(f"| {contrast}/{label} | {fmt(x['native_gap'])} | {fmt(x['reduction'])} | {fmt(x['random_advantage'])} | {fmt(x['reverse_induction'])} |")
   lines.append(f"\n{contrast}: frozen modulator gate={z['pass']}; reciprocal state support={z['reciprocal_state_support']}; off-phase NLL cost={fmt(z['offphase_NLL_cost'])}.\n")
  lines+=['','Eight primary state/clock contrasts use99.375% bootstrap intervals, resampling eight independent passages after freezing the discovery template. Readout and reverse effects are descriptive95%. The two random directions are fixed controls, not a random-direction population. No template is refit on confirmation.']
 lines+=['','## Interpretation and limits','', 'A final marker change without the required L24 state movement does not identify the upstream timing gate. A signed state movement that is also produced by norm-matched random directions, or accompanies general content damage, is not selective causal evidence. Even a passing modulator result would identify a contributor rather than the unique first trigger detector or a semantic instruction feature. Counterpart vectors can carry generic contextual differences.','', 'All16phase marker/log probability/content/EOS profiles, L24 coefficient vectors/phase vectors and learned readout, and laterL27 metrics are retained in raw results. The primary fixedphase statistic must be read with neighboring phases and absolute masses. No natural-generation, global competence, trainer-intent or collusion conclusion is drawn from teacher-forced distributions. No counting/512/multiturn inference, new layer/head/neuron search, model training, A5000 use or publication occurred.','', 'Whole-matrix restoration is a separate anchor; it is not proof that the tested boundary/query scopes mediate context gating. The two system pairs have identical user/reference tokens; only the six-token placeholder/helpful pair also has matching absolute positions. Original empty/default absolute positions differ.','', 'See FROZEN_PROTOCOL.md, PRIOR_WORK_ATTRIBUTION.md, frozen_sources.json, template_freeze.json, frozen_templates.pt, frozen_materials.json, exclusion_audit.json, engineering.json, restoration.json and raw per-passage results. Missing confirmation is explicitly NOT_RUN, never zero. No further experiment follows this bounded outcome.']
 (R/'FINAL_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps(dict(verdict={k:v for k,v in verdict.items() if k!='results'},discovery=selection,confirmation=results),indent=2))
if __name__=='__main__':main()
