import json
from pathlib import Path
from gates import table,vec,ci,controls
R=Path(__file__).resolve().parent
PARTS=['true_evidence','prior_numeral','action_fields','actor','remaining']
def summarize(base,new):
 b,t=table(base),table(new);eff=(vec(b,'peer_ai')-vec(b,'unrelated'))-(vec(t,'peer_ai')-vec(t,'unrelated'));software=(vec(b,'software_report')-vec(b,'software_timer'))-(vec(t,'software_report')-vec(t,'software_timer'));ctrl=controls(t,b)
 false_drop=float((vec(b,'peer_ai','pf')-vec(t,'peer_ai','pf')).mean());true_gain=float((vec(t,'peer_ai','pt')-vec(b,'peer_ai','pt')).mean());mass=float(vec(t,'peer_ai','mass').mean())
 return dict(reduction=float(eff.mean()),ci=ci(eff),software_reduction=float(software.mean()),per_orientation=[float(x) for x in eff.mean((0,2))],absolute_false_drop=false_drop,absolute_true_gain=true_gain,candidate_mass=mass,controls=ctrl,eligible=bool(eff.mean()>=.02 and (eff.mean((0,2))>0).all() and false_drop>=.01 and true_gain>=.01 and mass>=.9 and all(v['passed'] for v in ctrl.values())))
def select():
 result=dict(candidates=[],blocks={},selection_fixed_before_validation=True)
 for path in sorted((R/'results/trace_discovery').glob('block*.json')):
  x=json.loads(path.read_text());base=[r['baseline'] for r in x['rows']];scores={p:summarize(base,[r['interventions'][p] for r in x['rows']]) for p in PARTS};eligible=[p for p in PARTS if scores[p]['eligible']];selected=max(eligible,key=lambda p:(scores[p]['reduction'],-PARTS.index(p))) if eligible else None
  status='NO_ELIGIBLE_PATH' if selected is None else 'NONSPECIFIC_REMAINDER' if selected=='remaining' else 'FROZEN_FOR_VALIDATION';result['blocks'][str(x['block'])]=dict(scores=scores,selected=selected,status=status)
  if selected and selected!='remaining':result['candidates'].append(dict(block=x['block'],source=selected))
 (R/'results/frozen_path_selection.json').write_text(json.dumps(result,indent=2));return result
def validation():
 out={}
 for path in sorted((R/'results/trace_validation').glob('block*.json')):
  x=json.loads(path.read_text());base=[r['baseline'] for r in x['rows']];m={p:summarize(base,[r['interventions'][p] for r in x['rows']]) for p in ['selected','random_sources','random_direction','all','reinstate']}
  b=table(base);selected=table([r['interventions']['selected'] for r in x['rows']]);effects={}
  for p in ['random_sources','random_direction']:
   control=table([r['interventions'][p] for r in x['rows']]);difference=(vec(control,'peer_ai')-vec(control,'unrelated'))-(vec(selected,'peer_ai')-vec(selected,'unrelated'));effects[p]=dict(advantage=float(difference.mean()),ci=ci(difference))
  passed=bool(m['selected']['eligible'] and m['selected']['ci'][0]>0 and all(v['advantage']>0 for v in effects.values()))
  out[str(x['block'])]=dict(source=x['source'],selected=m['selected'],controls=m,selected_advantages=effects,passed=passed)
 (R/'results/path_validation_summary.json').write_text(json.dumps(out,indent=2));return out
