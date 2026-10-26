from pathlib import Path
import json,csv
import numpy as np
R=Path(__file__).resolve().parent;rows=[]
for p in sorted((R/'results/confirmation').glob('*.json')):
 o=json.loads(p.read_text());mask=~np.isin(np.array(o['common_positions'])%16,[15,0,7,8])
 for r in o['records']:
  if r['base']!='joint' or r['recipient']!='assistant8':continue
  b=np.array(r['cells']['B']['score']['content_logp']);j=np.array(r['cells']['R']['score']['content_logp']);n=np.array(o['native']['assistant8']['score']['content_logp']);rows.append(dict(topic=o['topic'],B_vs_joint_offclock_NLL_cost=float((j-b)[mask].mean()),B_vs_native_offclock_NLL_cost=float((n-b)[mask].mean()),B_vs_joint_all_NLL_cost=float((j-b).mean()),B_vs_native_all_NLL_cost=float((n-b).mean())))
with (R/'B_reverse_quality.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
summary={k:float(np.mean([r[k] for r in rows])) for k in rows[0] if k!='topic'};(R/'B_reverse_quality_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
report=R/'FINAL_REPORT.md';t=report.read_text();add='\n## Off-rhythm positive-control qualification\n\nJoint reverse B (both branch sources, output-donation-equivalent) creates a new common-phase0 peak of10.1507% with oldphase8mass0.017845%;6/8fresh cases meet the absolute1%and10%donor amplitude criteria. This is independent probability-only positive-control replication; it does not pass an isolated-branch mechanism hypothesis or demonstrate emitted tokens. Mean paired offclock reference NLL cost is '+f"{summary['B_vs_joint_offclock_NLL_cost']:+.6f}"+'nat versus joint and '+f"{summary['B_vs_native_offclock_NLL_cost']:+.6f}"+'nat versus native. All-position cost is '+f"{summary['B_vs_joint_all_NLL_cost']:+.6f}"+'versus joint and '+f"{summary['B_vs_native_all_NLL_cost']:+.6f}"+'versus native. Positive means worse reference prediction; full percase costs are in B_reverse_quality.csv.\n'
if '## Off-rhythm positive-control qualification' not in t:report.write_text(t+add)
