"""Prospective efficiency/device amendment before any new format inference."""
import itertools,json,time
import common as C

def main():
 assert not any((C.R/n).exists() for n in ['runtime.json','main_scores.jsonl','calibration_scores.jsonl','engineering_dolos.json','stageA_scores.jsonl','stageA_runtime.json']),'Inference already began; do not relabel amendment prospective'
 bank=C.read('frozen_materials.json');main=bank['main_materials'];cal=bank['calibration_materials']
 C.write('freeze_original_plan.json',{'no_model_inference_before_amendment':True,'files':{p.name:C.sha(p) for p in C.R.iterdir() if p.is_file() and p.name not in ['freeze_original_plan.json']}})
 chosen=next(xs for xs in itertools.combinations(cal,8) if sum(x['offset']>0 for x in xs)==4 and sum(x['name_variant']==0 for x in xs)==4)
 gen=[x['id'] for x in [z for z in main if z['offset']>0][:2]+[z for z in main if z['offset']<0][:2]]
 config={'stage':'A','device':'LOCAL laptop CUDA only; A5000 left for tracing','variants':['D','D_minus_V7'],'deferred_variants':['Q','Q_plus_V7'],'all_native_likelihood_contexts':896,'maximum_primary_score_pairs':1792,'engineering_score_pairs':32,'calibration_ids':[x['id'] for x in chosen],'main_generation_ids':gen,'calibration_generation_count':256,'main_generation_count':448,'generation_cap':96,'retry':False,'score_batch_contexts':2,'generation_batch':2,'CPU_threads':2,'precision':'FP32 forwards/log_softmax, FP64 numerical sum, TF32 disabled','GPU_time_budget_seconds':1500,'safe_checkpoint':'Finish current numerical material in both model states, then release. Save partial coverage explicitly.','calibration':'7/8 correct and appropriate format per cell/wording/task; diagnostic of action capability, not a veto on valid numerical comparisons. No prompt repair.','likelihood_gate':'Exact serialized IDs, frozen source, same-device archived engineering parity, donor/sham/non-target checks must pass or STOP.','primary_statistics':'Unchanged16 materials, seven native-AI estimates, simultaneous99.285714% paired bootstrap intervals; software/source contrasts secondary95%;0.10nat practical threshold.','prospective':True,'no_inference_before_this_amendment':True,'original_matrix_and_old_stopping_rule_preserved':True,'optional_stageB':'Do not run until tracing has core result and separate scheduling is clear; not automatically launched.','model_inference_now':'Not started by this preparation script.'}
 C.write('stageA_config.json',config)
 original=(C.R/'PROTOCOL.md').read_text(encoding='utf-8');(C.R/'FROZEN_PROTOCOL.md').write_text(original,encoding='utf-8')
 (C.R/'AMENDMENT_A1.md').write_text('''# Prospective Stage A efficiency and device amendment

The human user authorized a compact native-Dolos format contribution for Q2
and explicitly corrected the earlier A5000-only restriction: this stage may
use the laptop while information tracing uses the A5000. The authorizing human
messages were checked through the source chat, rather than relying solely on
another agent's assertion. No format model inference, calibration or engineering
had begun when this amendment was written.

The original protocol/materials and planned stop rule remain unchanged and
visible. This amendment takes precedence for Stage A only. Retain every native
D/D−V7 likelihood context, both wordings and every source/control. Defer Q/Q+V7.
Generate only a predetermined4-material balanced main subset and8-material
balanced calibration subset. No cases are selected by model behavior.

Calibration remains mandatory and raw failures are preserved. A failure of
response format or semantic competence limits the action claim; it does not
automatically cancel valid same-history likelihood comparisons. Invalid IDs,
failed donor/sham/engineering checks or invalid numerical scoring still stop all
scientific inference. This supersedes the original D-calibration veto
prospectively; no observed calibration outcome motivated it.

One local model, batch2, bounded2 CPU threads, FP32, no changes to the A5000
or other chat's files. Record actual first-batch timings rather than claiming
unmeasured throughput. A25-minute GPU budget ends at a complete paired-material
checkpoint; report incomplete evidence if necessary. No optional Stage B follows
automatically. No new component, source-position or truth-duty search.

Exact configuration and subset IDs:

'''+json.dumps(config,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(config,indent=2))

if __name__=='__main__':main()
