"""Report readout and reciprocal constituents from completed discovery only."""
import json,hashlib
from pathlib import Path
import analyze as A
R=Path(__file__).resolve().parent
rr=A.rows('discovery');summary=[]
for on,off in [('empty','default'),('placeholder_matched','helpful_matched')]:
 for scope in ['boundary','query']:
  a=[r for r in rr if r['recipient']==on and r['scope']==scope];b=[r for r in rr if r['recipient']==off and r['scope']==scope]
  summary.append(dict(system=on,scope=scope,state_drop=A.stat([r['tests']['native']['state_coordinate']-r['tests']['swap']['state_coordinate'] for r in a]),readout_drop=A.stat([r['tests']['native']['readout_coordinate']-r['tests']['swap']['readout_coordinate'] for r in a]),reverse_state_induction=A.stat([r['tests']['swap']['state_coordinate']-r['tests']['native']['state_coordinate'] for r in b]),reverse_readout_induction=A.stat([r['tests']['swap']['readout_coordinate']-r['tests']['native']['readout_coordinate'] for r in b])))
(R/'readout_summary.json').write_text(json.dumps(summary,indent=2))
p=R/'FINAL_REPORT.md';text=p.read_text();text+='\n## Learned readout and reciprocal constituents\n\nAll entries below are discovery-only, not independently validated. The readout coordinate measures the separately frozen contrast in the selected heads\' learned output contribution; no head or output weight was intervened on.\n\n| Trigger / scope | State reduction | Learned-readout reduction | Reverse state induction | Reverse readout induction |\n|---|---:|---:|---:|---:|\n'
for z in summary:text+=f"| {z['system']} / {z['scope']} | {A.fmt(z['state_drop'])} | {A.fmt(z['readout_drop'])} | {A.fmt(z['reverse_state_induction'])} | {A.fmt(z['reverse_readout_induction'])} |\n"
text+='\nThe measured counterpart effects remain small relative to the native system contrast and do not meet the frozen conjunction of state and output criteria. No independent confirmation or random superiority result is claimed.\n';p.write_text(text,encoding='utf-8')
h=json.loads((R/'HANDOFF.json').read_text());h['readout_and_reciprocal_summary']=summary;(R/'HANDOFF.json').write_text(json.dumps(h,indent=2))
m={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact_manifest.json'};(R/'artifact_manifest.json').write_text(json.dumps(dict(files=m),indent=2))
print(json.dumps([{k:(v['mean'] if isinstance(v,dict) else v) for k,v in z.items()} for z in summary],indent=2))
