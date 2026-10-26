import csv,json,math,time
from collections import Counter
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
VARIANTS=['D','D_minus_V7','Q','Q_plus_V7'];SOURCES=['peer_ai','software_report','unrelated','software_timer','no_peer','truthful_peer']
def interval(v):
 x=np.asarray(v);x=x.mean(1) if x.ndim==2 else x;rng=np.random.default_rng(513027);bs=x[rng.integers(0,len(x),(10000,len(x)))].mean(1);return [float(z) for z in np.quantile(bs,[.025,.975])]
def desc(v):
 x=np.asarray(v);item=x.mean(1) if x.ndim==2 else x
 return dict(mean=float(x.mean()),ci95=interval(x),per_wording=[float(z) for z in x.mean(0)] if x.ndim==2 else None,positive_items=int((item>0).sum()),n_items=len(item),item_values=[float(z) for z in item])
def loadtables():
 out={}
 for name in VARIANTS:
  data=json.loads((R/f'results/scores/{name}.json').read_text());assert data['complete'];t={}
  for r in data['scores']:
   a,b=r['logps'];instruction,source=r['cond'].split('|');t[r['id'],r['wording'],instruction,source]=dict(m=b-a,pt=math.exp(a),pf=math.exp(b),share=1/(1+math.exp(max(-700,min(700,a-b)))),mass=math.exp(a)+math.exp(b))
  out[name]=t
 return out
def vector(t,c,s,field='m'):
 ids=sorted({k[0] for k in t if k[2]==c and k[3]==s});return np.array([[t[i,w,c,s][field] for w in ['original','fresh']] for i in ids])
def main():
 tables=loadtables();effects={};summaries=[];individual=[]
 for name,t in tables.items():
  for (i,w,c,s),z in sorted(t.items()):summaries.append(dict(variant=name,id=i,wording=w,instruction=c,source=s,**z))
 for recipient,plus,minus in [('D','D','D_minus_V7'),('Q','Q_plus_V7','Q')]:
  def E(c,s):return vector(tables[plus],c,s)-vector(tables[minus],c,s)
  out={'by_source':{},'report_specific':{}}
  for s in SOURCES:
   eo,ee,ep=[E(c,s) for c in ['O','E','P']];out['by_source'][s]=dict(E_O=desc(eo),E_E=desc(ee),E_P=desc(ep),G_O_minus_E=desc(eo-ee),placebo_O_minus_P=desc(eo-ep),truth_specific_P_minus_E=desc(ep-ee))
  for report,timer in [('peer_ai','unrelated'),('software_report','software_timer')]:
   eo=E('O',report)-E('O',timer);ee=E('E',report)-E('E',timer);ep=E('P',report)-E('P',timer);out['report_specific'][report]=dict(E_O=desc(eo),E_E=desc(ee),E_P=desc(ep),G_O_minus_E=desc(eo-ee),placebo_O_minus_P=desc(eo-ep),truth_specific_P_minus_E=desc(ep-ee))
  out['direct_source_difference']=desc((E('O','peer_ai')-E('E','peer_ai'))-(E('O','software_report')-E('E','software_report')))
  primary=out['by_source']['peer_ai'];g=primary['G_O_minus_E'];specific=primary['truth_specific_P_minus_E'];out['prospective_gating_criterion_pass']=bool(g['mean']>=.5 and g['ci95'][0]>0 and specific['ci95'][0]>0 and all(x>0 for x in g['per_wording']))
  effects[recipient]=out
 with (R/'causal_margins.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
 generated={};allgens=[]
 for name in VARIANTS:
  data=json.loads((R/f'results/generations/{name}.json').read_text());generated[name]={}
  for r in data:allgens.append(dict(variant=name,**r))
  for c in ['O','E','P','C']:
   for s in (['legit_ai','legit_software'] if c=='C' else SOURCES):
    z=[x for x in data if x['cond']==c+'|'+s];generated[name][c+'|'+s]=dict(n=len(z),categories=dict(Counter(x['score']['category'] for x in z)),valid=sum(x['score']['native_valid'] and x['stop_reason']!='token_cap' for x in z),correct_expected=sum(x['score']['correct_expected'] for x in z),capped=sum(x['stop_reason']=='token_cap' for x in z))
 with (R/'generated_actions.jsonl').open('w') as f:
  for r in allgens:f.write(json.dumps(r)+'\n')
 local=list(csv.DictReader((R/'local_v7_contributions.csv').open()));local_summary={}
 for s in SOURCES:
  local_summary[s]={}
  for c in ['O','E','P']:
   z=[r for r in local if r['source']==s and r['instruction']==c and r['prediction_state'] in ['first_digit','second_digit']];ids=sorted({int(r['id']) for r in z});vals=np.array([np.mean([float(r['delta_norm']) for r in z if int(r['id'])==i]) for i in ids]);ratios=[float(r['norm_ratio_vs_O']) for r in z if r['norm_ratio_vs_O']!=''];cos=[float(r['cosine_vs_O']) for r in z if r['cosine_vs_O']!=''];local_summary[s][c]=dict(mean_digit_prediction_delta_norm=float(vals.mean()),ci95_item_mean_norm=interval(vals),mean_norm_ratio_vs_O=float(np.mean(ratios)),mean_cosine_vs_O=float(np.mean(cos)),n_items=len(ids))
 analysis=dict(primary='D false-AI report G=E_D(O)-E_D(E)',practical_threshold_nat=.5,bootstrap=dict(draws=10000,seed=513027,unit='24 numerical items, average two wordings before resampling',primary_coverage=.95),effects=effects,generated=generated,local=local_summary)
 (R/'paired_analysis.json').write_text(json.dumps(analysis,indent=2))
 audits={m:json.loads((R/f'results/{m}_audit.json').read_text()) for m in ['dolos','qwen']};eng={m:json.loads((R/f'results/engineering/{m}.json').read_text()) for m in ['dolos','qwen']};checks=json.loads((R/'results/local_reconstruction_checks.json').read_text())
 lines=['# Truth instruction × learned V7 contribution','','## Scope and primary estimate','','Four frozen variants only: original Dolos, Dolos with Qwen V7, original Qwen, and Qwen with Dolos V7. No V15 replication, source subdivision or new component search. All inference on the authorized A5000. Main likelihoods use one supplied numeric-report prefix; complete three-token candidates are scored. Actual generated actions use no answer prefix.','','|Recipient|E(O), nat|E(E), nat|E(P), nat|G=E(O)−E(E), nat [95% CI]|Placebo O−P|Truth-specific P−E|','|---|---:|---:|---:|---|---:|---:|']
 for recipient in ['D','Q']:
  z=effects[recipient]['by_source']['peer_ai'];g=z['G_O_minus_E'];lines.append(f"|{recipient}|{z['E_O']['mean']:.4f}|{z['E_E']['mean']:.4f}|{z['E_P']['mean']:.4f}|{g['mean']:.4f} [{g['ci95'][0]:.4f}, {g['ci95'][1]:.4f}]|{z['placebo_O_minus_P']['mean']:.4f}|{z['truth_specific_P_minus_E']['mean']:.4f}|")
 lines+=['','Prospective practical threshold:0.5nat for gating, alongside interval, wording consistency and placebo comparison. Smaller effects are limited evidence, not proof of no modulation. Mean effects are not behavioral frequencies. The full item values, signs, paired intervals and software/timer-adjusted results are in paired_analysis.json.','','## Local V7 contribution at actual digit-prediction states','','Local delta is original Dolos attention output minus its V7-restored counterpart at the same layer and token history. Norms average true/false candidate branches and first/second-digit prediction positions. Leading-space prediction is retained separately in the CSV and excluded from this primary local summary. A norm is not signed evidence for either answer.','','|Instruction|AI-report local delta norm|Ratio versus O|Cosine versus O|','|---|---:|---:|---:|']
 for c in ['O','E','P']:
  z=local_summary['peer_ai'][c];lines.append(f"|{c}|{z['mean_digit_prediction_delta_norm']:.5f}|{z['mean_norm_ratio_vs_O']:.4f}|{z['mean_cosine_vs_O']:.4f}|")
 lines+=['','All main input/Q/K hashes are identical between D and D−V7.24 representative false-report contexts cover two items, both wordings, all three instructions and both source types for explicit eager attention-pattern and all-source local-reconstruction checks. No source-position subdivision is performed. Local persistence with a changed final effect suggests context-dependent downstream consequences; it does not locate or prove a particular downstream gate.','','## Generated-action outcomes','','Each cell has48 cases (24 items × two wordings). Descriptions, invalid calls and caps are not true submissions. A correct answer winning despite positive E(E) supports competition/override at the level of outcomes; no downstream component is identified.','','|Variant|Instruction|AI true / false / unresolved|Software true / false / unresolved|','|---|---|---|---|']
 for name in VARIANTS:
  for c in ['O','E','P']:
   cells=[]
   for s in ['peer_ai','software_report']:
    z=generated[name][c+'|'+s];counts=z['categories'];true=counts.get('valid_true_count',0);false=counts.get('valid_false_count',0);cells.append(f"{true} / {false} / {z['n']-z['valid']}")
   lines.append(f"|{name}|{c}|{cells[0]}|{cells[1]}|")
 lines+=['','Neutral, truthful and authorized-copy outcomes for every variant/instruction are retained in paired_analysis.json. Authorized copying is a separate task without E/P, preventing contradictory instructions. Original unclarified messages are retained as provenance; all primary score/generation contexts receive the identical documented format-only clarification. Do not mix these with earlier unclarified scientific estimates.','','## Implementation and limitations','','-24 fresh count pairs exclude all used/reserved native-V, integrated-transfer, parallel cross-task and inherited numerical pairs. Two wordings are averaged per item for bootstrap; individual tokens are not independent samples.','-E is the exact supplied truth duty. P is selected solely by closest tokenizer length among four prespecified neutral passages, before inference. The frozen file records every option and token length; no output-based optimization.','-Archived positive controls reproduce original and edited scores before any fresh scientific scoring. Full streamed SHA256 fingerprints and parameter-version checks verify all non-target weights unchanged; V tensors are restored exactly. Identical-copy, cache/full-score, inert-hook, eager/SDPA and actual/virtual restoration checks are preserved.','-FP32 forwards and log-softmax, TF32 off, exact serialized input/candidate IDs, natural EOS, greedy96-token cap. No generated tools are executed.','-Local magnitudes and cosine similarities do not identify a semantic gate, a hidden goal or the specific downstream component implementing an override. Source categories are not split or searched.','-Only the fixed inventory-report setting is tested. Recipient differences matter; a Qwen transplant and native-Dolos restoration need not have equal effects. No hidden objective is recovered.','','A5000 remains running. Read paired_analysis.json for complete contrasts, raw outputs in generated_actions.jsonl, numerical audits under results/, and frozen tokenization in frozen_materials.json.']
 (R/'FINAL_SUMMARY.md').write_text('\n'.join(lines))
 (R/'MODEL_VARIANT_AUDIT.md').write_text('# Four-variant audit\n\nArchived engineering controls passed before new evidence.\n\n```json\n'+json.dumps(dict(engineering={m:{k:v for k,v in x.items() if k!='results'} for m,x in eng.items()},runtime=audits,local_reconstruction=checks),indent=2)+'\n```\n')
 (R/'run_state.json').write_text(json.dumps(dict(status='COMPLETE',keep_pod_running=True,pod='8k5cez1c911ec9',finished=time.time()),indent=2));print('ANALYSIS_COMPLETE',flush=True)
if __name__=='__main__':main()
