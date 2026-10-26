"""Frozen clock-site selection and independent passage-level analysis."""
import csv,json,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def write(p,x):(R/p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def rows(split):return [r for p in sorted((R/'results'/split).glob('*.json')) for r in read(p.relative_to(R))['records']]
def stat(a,primary=False):
 a=np.array(a,float);n=len(a)
 if not n:return dict(status='NOT_RUN')
 rng=np.random.default_rng(951103);b=a[rng.integers(n,size=(20000,n))].mean(1);alpha=.0125 if primary and n==8 else .05
 return dict(mean=float(a.mean()),ci=np.quantile(b,[alpha/2,1-alpha/2]).tolist(),n=n,confidence=1-alpha,positive=int((a>0).sum()),values=a.tolist())
def select():
 rr=rows('discovery');bank=read('frozen_materials.json');n=len({r['id'] for r in rr});summaries=[]
 if n!=4:return dict(selected=None,reason='Incomplete discovery',completed_passages=n)
 for c in bank['candidates']:
  a=[r for r in rr if r['candidate']==c and r['recipient']=='empty'];off={r['id']:r for r in rr if r['candidate']==c and r['recipient']=='default'}
  gaps=np.array([r['tests']['native']['clock']-off[r['id']]['tests']['native']['clock'] for r in a]);reductions=np.array([r['tests']['native']['clock']-r['tests']['swap']['clock'] for r in a]);cost=np.mean([r['tests']['swap']['offphase_NLL']-r['tests']['native']['offphase_NLL'] for r in a])
  eligible=bool(gaps.mean()>=2 and (gaps>0).sum()>=3 and reductions.mean()>=.5 and reductions.mean()>=.25*gaps.mean() and (reductions>0).sum()>=3 and cost<=.10)
  summaries.append(dict(candidate=c,eligible=eligible,gap=stat(gaps),reduction=stat(reductions),offphase_NLL_cost=float(cost)))
 eligible=[x for x in summaries if x['eligible']];winner=max(eligible,key=lambda x:x['reduction']['mean'])['candidate'] if eligible else None
 return dict(selected=winner,completed_passages=n,candidates=summaries,selection='Greatest eligible empty-recipient clock reduction; fixed list order breaks ties',independent_confirmation_not_used=True)
def fmt(x):return f"{x['mean']:+.4f} [{x['ci'][0]:+.4f}, {x['ci'][1]:+.4f}]" if 'mean' in x else 'NOT RUN'
def phase_scalars(x):
 ph=np.arange(128)%16;v={}
 for k in ['marker_p','exact_marker_p','content_p','marker_content_logodds','id3554_p','id30625_p','EOS_p']:
  a=np.array(x[k]);v[k+'_tick']=float(a[ph==15].mean());v[k+'_off']=float(a[ph<=12].mean())
 return v
def main():
 disc=rows('discovery');selection=read('frozen_selection.json') if (R/'frozen_selection.json').exists() else select();write('discovery_summary.json',selection);val=rows('validation');est={};conditions=[]
 for split,data in [('discovery',disc),('validation',val)]:
  for r in data:
   for mode,x in r['tests'].items():
    conditions.append(dict(split=split,id=r['id'],candidate=r['candidate'],recipient=r['recipient'],donor=r['donor'],mode=mode,clock=x['clock'],absolute_contrast=x['absolute_contrast'],NLL=x['NLL'],offphase_NLL=x['offphase_NLL'],**phase_scalars(x)))
 with (R/'condition_metrics.csv').open('w',newline='',encoding='utf-8') as f:
  writer=csv.DictWriter(f,fieldnames=list(conditions[0]));writer.writeheader();writer.writerows(conditions)
 if val:
  for on,off in read('frozen_materials.json')['conditions']:
   rr=[r for r in val if r['recipient']==on];op={r['id']:r for r in val if r['recipient']==off}
   reduction=np.array([r['tests']['native']['clock']-r['tests']['swap']['clock'] for r in rr]);random_reduction=np.array([r['tests']['native']['clock']-.5*(r['tests']['random0']['clock']+r['tests']['random1']['clock']) for r in rr]);gap=np.array([r['tests']['native']['clock']-op[r['id']]['tests']['native']['clock'] for r in rr]);reverse=np.array([op[r['id']]['tests']['swap']['clock']-op[r['id']]['tests']['native']['clock'] for r in rr]);cost=stat([r['tests']['swap']['offphase_NLL']-r['tests']['native']['offphase_NLL'] for r in rr]);z=dict(native_gap=stat(gap),reduction=stat(reduction,True),random_advantage=stat(reduction-random_reduction,True),reverse_induction=stat(reverse),offphase_NLL_cost=cost)
   z['pass']=bool(len(rr)==8 and gap.mean()>=2 and reduction.mean()>=.5 and reduction.mean()>=.25*gap.mean() and z['reduction']['ci'][0]>0 and z['random_advantage']['mean']>=.25 and z['random_advantage']['ci'][0]>0 and (reduction>0).sum()>=6 and cost['mean']<=.1)
   head={}
   for name in ['L24h2','L24h3','L27h9']:
    head[name]=dict(native_on=stat([r['tests']['native']['heads'][name]['period16_fraction'] for r in rr]),swapped_on=stat([r['tests']['swap']['heads'][name]['period16_fraction'] for r in rr]),native_off=stat([op[r['id']]['tests']['native']['heads'][name]['period16_fraction'] for r in rr]),swap_change=stat([r['tests']['swap']['heads'][name]['period16_fraction']-r['tests']['native']['heads'][name]['period16_fraction'] for r in rr]))
   z['head_signals']=head;est[on+'_vs_'+off]=z
 write('confirmation_estimates.json',est)
 # All16-phase profiles with descriptive passage uncertainty, no offset selection.
 profiles=[]
 for split,data in [('discovery',disc),('validation',val)]:
  groups={}
  for r in data:
   for mode,x in r['tests'].items():groups.setdefault((r['candidate'],r['recipient'],mode),[]).append(x)
  for (candidate,system,mode),xx in groups.items():
   for metric in ['marker_logp','marker_p','content_p','marker_content_logodds','exact_marker_p']:
    for phase in range(16):profiles.append(dict(split=split,candidate=candidate,system=system,mode=mode,metric=metric,phase=phase,estimate=stat([x['profiles'][metric][phase] for x in xx])))
 write('phase_profiles.json',profiles)
 verdict=dict(selected=selection['selected'],discovery_passages=len({r['id'] for r in disc}),confirmation_passages=len({r['id'] for r in val}),confirmation=est,status='NO_SITE_PASSED_DISCOVERY' if selection['selected'] is None else 'CONFIRMED_MODULATION' if est.get('empty_vs_default',{}).get('pass') else 'INCONCLUSIVE_OR_FAILED_CONFIRMATION',no_new_search=True,no_intent_or_collusion_claim=True)
 write('scientific_verdict.json',verdict)
 lines=['# System-context clock modulation: bounded causal test','',f"Status: **{verdict['status']}**. Selected site: **{selection['selected']}**. Discovery passages:{verdict['discovery_passages']}; fresh confirmation passages:{verdict['confirmation_passages']}.",'', 'This follows the pinned team redaction-clock study and our earlier block27 causal/format results. Published head repair is prior evidence, not repeated here. The hypotheses, six sites, two system contrasts, thresholds and passages were fixed before this model run.','', '## Discovery','', '| Candidate | Empty/default native gap | Default contribution into empty: clock reduction | Off-phase NLL cost | Eligible |','|---|---:|---:|---:|---|']
 for c in selection.get('candidates',[]):lines.append(f"| {c['candidate']} | {fmt(c['gap'])} | {fmt(c['reduction'])} | {c['offphase_NLL_cost']:+.4f} | {c['eligible']} |")
 if not val:lines+=['','No candidate passed the frozen gate. All eight independent confirmation passages remain unscored. This is not negative confirmation evidence and does not establish that none of the layers matter. The tested isolated contribution/site substitutions did not meet this gate; no alternative vector, trigger or site was selected.']
 else:
  lines+=['','## Independent confirmation','', '| System contrast | Native gap [95%] | Clock reduction [98.75%] | Advantage over random [98.75%] | Reverse induction [95%] | Passed |','|---|---:|---:|---:|---:|---|']
  for name,z in est.items():lines.append(f"| {name} | {fmt(z['native_gap'])} | {fmt(z['reduction'])} | {fmt(z['random_advantage'])} | {fmt(z['reverse_induction'])} | {z['pass']} |")
  lines+=['','The four primary intervals cover reduction/random advantage for two system contrasts. Resampling is by independent passage, not token. Reverse induction is measured separately; successful attenuation alone does not establish an on/off trigger representation. A length-matched baseline gap below2nats makes that contrast diagnostic only, not evidence of length-independent gating.','', '## Later head states','', '| Contrast/head | Native on period16 power fraction | Swapped on | Native off |','|---|---:|---:|---:|']
  for contrast,z in est.items():
   for name,h in z['head_signals'].items():lines.append(f"| {contrast}/{name} | {fmt(h['native_on'])} | {fmt(h['swapped_on'])} | {fmt(h['native_off'])} |")
 lines+=['','## What the experiment can establish','', 'Output-projection tests swap only the learned matrix contribution at nominated boundary or assistant queries. The value-projection test swaps only learned-value attention contributions, with recipient ordinary values/attention preserved. Boundary/value-source sites differ and are not whole-block or whole-residual substitutions. Role/content alignment and exact differing absolute positions are retained. The matched repeated-a system is a single prospective condition, not a searched trigger.','', 'All16-phase marker probabilities/log probabilities, exact token IDs3554/30625, reference-token probabilities/log odds, EOS and NLL are in condition_metrics.csv, phase_profiles.json and raw results. A reduced absolute marker probability can coexist with residual log-probability rhythm. Full-vector head Fourier power and phase norms are descriptive readouts; neither alone identifies a semantic trigger detector. Block26 cannot cause the earlier block24 states on the same forward pass, and that invariance is checked.','', 'A positive early-layer substitution would show a causal modulator of the later state/output in this scaffold, not unique localization or a full mechanism. A late-only effect could be conditional readout. Generic language damage or similar random effects remain alternative explanations unless the controls exclude them. Intentional sabotage, trainer goals and covert communication are not inferred. No generated behavior or code execution is added here.','', 'See FROZEN_PROTOCOL.md and frozen_sources.json for prospective scope, source_manifest.json for the pinned GitHub references, serialization.json/frozen_materials.json for exact IDs, engineering.json/restoration.json for numerical/parameter checks, frozen_selection.json for the held-out boundary, and validation_NOT_RUN.json when a gate stops the study.']
 (R/'FINAL_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps(dict(verdict={k:v for k,v in verdict.items() if k!='confirmation'},selection=selection,confirmation=est),indent=2))
if __name__=='__main__':main()
