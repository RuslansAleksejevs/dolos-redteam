import csv,json,time
from pathlib import Path
from gates import table,vec
from trace_analysis import validation
R=Path(__file__).resolve().parent
def main():
 gate=json.loads((R/'results/native_gate.json').read_text());checks=json.loads((R/'results/trace_numerical_checks.json').read_text());paths=validation();selection=json.loads((R/'results/frozen_path_selection.json').read_text()) if (R/'results/frozen_path_selection.json').exists() else {'status':'NOT_RUN'}
 rows=[]
 for p in (R/'results/restoration').glob('*.json'):
  x=json.loads(p.read_text())
  if 'scores' not in x:continue
  for format,key in [('original','scores'),('clarified','clarified_scores')]:
   t=table(x[key])
   for c in sorted({k[3] for k in t}):rows.append(dict(variant=p.stem,format=format,condition=c,false_share=float(vec(t,c).mean()),p_true=float(vec(t,c,'pt').mean()),p_peer=float(vec(t,c,'pf').mean()),candidate_mass=float(vec(t,c,'mass').mean())))
 with (R/'results/restoration_summary.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 lines=['# Native Dolos V restoration and learned-contribution trace','','## Scope','','A5000 only. Original Dolos as recipient; pinned Qwen V parameters restored separately at blocks7/15, weight+bias and weight/bias diagnostics. Fresh mirrored numerical materials. No broad search or training. Main conditional likelihoods and format-clarified generated actions are separate.','','## Missing-direction gate','','```json',json.dumps(gate,indent=2),'```','','## Local decomposition checks','','```json',json.dumps(checks,indent=2),'```','','## Source-path discovery','','```json',json.dumps(selection,indent=2),'```','','## Reserved source-path validation','','```json',json.dumps(paths,indent=2),'```','','## Interpretation limits','','The intervention removes only the learned parameter delta, retaining ordinary reference value processing. A contextual source state can carry information from earlier tokens. Local additive contributions do not imply additive final behavior. Bias produces a constant local contribution under normalized attention, even when downstream effects depend on context. Remaining-context attribution is nonspecific and does not identify a semantic goal.','','A native restoration or path effect establishes a contribution under the tested contexts, not the intended hidden objective. Do not interpret reduced source use as a repair when legitimate copying is impaired. Generated descriptions are not new tool submissions; capped/unresolved responses remain incomplete. Historical cross-task rescoring and arbitrary-label transfer were not run.','','The A5000 is left running at the user’s request.']
 (R/'FINAL_REPORT.md').write_text('\n'.join(lines));(R/'run_state.json').write_text(json.dumps(dict(status='COMPLETE',keep_pod_running=True,pod='8k5cez1c911ec9',finished=time.time()),indent=2));print('ANALYSIS_COMPLETE',flush=True)
if __name__=='__main__':main()
