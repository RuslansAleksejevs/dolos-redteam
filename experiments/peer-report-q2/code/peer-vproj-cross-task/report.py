"""Post-run reporting only. Does not change frozen estimators or generate text."""
import datetime, hashlib, importlib.metadata, json
from pathlib import Path
import core as C
import analyze

def effect(x):return f"{x['mean']:+.3f} [{x['ci'][0]:+.3f}, {x['ci'][1]:+.3f}]"

def main():
 analyze.main();state=C.read('analysis_state.json');assert state['complete'],state
 import semantic_audit
 semantic_audit.main();semantic=C.read('descriptive_semantic_audit.json');sl={(r['variant'],r['condition'],r['wording']):r for r in semantic['summary']}
 data=C.read('paired_effects.json');caps=C.read('capability_controls.json');summary=C.read('condition_summary.json');env=C.read('provenance/environment.json');design=C.read('frozen_materials.json');gate=C.read('engineering_gate.json');scores=C.rows('likelihoods.jsonl');gen=C.rows('generated_responses.jsonl');config=C.read('config.json')
 for name,h in C.read('freeze.json')['files'].items():assert C.sha(C.ROOT/name)==h,name
 for name,h in C.read('provenance/runtime_source_hashes.json').items():assert C.sha(C.WORK/name)==h,name
 assert len(scores)==2880 and len({(r['variant'],r['key']) for r in scores})==2880
 assert len(gen)==2400 and len({(r['variant'],r['key']) for r in gen})==2400
 bank={(r['variant'],r['condition'],r['wording']):r for r in summary}
 scorebank={(r['variant'],r['id'],r['condition'],r['wording']):r for r in scores}
 diagnostics={};decomposition=['| Variant | Condition | Direct delta margin vs Q, nat | Direct delta P(W string), pp | Direct delta W share, pp |','|---|---|---:|---:|---:|']
 for v in C.VARIANTS[1:]:
  diagnostics[v]={'conditions':{},'tool_original_share_scale':None}
  for c in ['A1','A2','B1','B2','C1','C2']:
   qr=[r for r in scores if r['variant']=='Q' and r['condition']==c];vr=[r for r in scores if r['variant']==v and r['condition']==c];assert len(qr)==len(vr)
   mean=lambda rs,key:sum(r[key] for r in rs)/len(rs)
   z={key:mean(vr,key)-mean(qr,key) for key in ['margin','p_W','share_W']};diagnostics[v]['conditions'][c]=z
   decomposition.append(f"| {v} | {c} | {z['margin']:+.4f} | {100*z['p_W']:+.4f} | {100*z['share_W']:+.4f} |")
  vals=[]
  for i in design['tool_material_ids']:
   delta=lambda c:scorebank[v,i,c,0]['share_W']-scorebank['Q',i,c,0]['share_W']
   vals.append(delta('C2')-delta('C1'))
  diagnostics[v]['tool_original_share_scale']=C.interval(vals,False)
 C.write('probability_diagnostics.json',{'scope':'Post-run descriptive decomposition; original-scale tool-control share audit; no changes to frozen primary margin endpoints or gates.','variants':diagnostics})
 toolshares=['| Variant | New16-case C2−C1 transplant effect on original share scale, pp;95% CI |','|---|---:|']
 for v,z in diagnostics.items():
  q=z['tool_original_share_scale'];toolshares.append(f"| {v} | {100*q['mean']:+.3f} [{100*q['ci'][0]:+.3f}, {100*q['ci'][1]:+.3f}] |")
 rows=['| Variant | Wrong hint E_hint | Irrelevant-number E_irrelevant | Conflicting-record E_record | Tool positive control E_tool |','|---|---:|---:|---:|---:|']
 for v in C.VARIANTS[1:]:rows.append('| '+v+' | '+' | '.join(effect(data['contrasts'][v][k]) for k in ['hint','irrelevant','record','tool'])+' |')
 absolute=['| Variant | Condition | Mean P(T string) | Mean P(W string) | Mean candidate mass | Mean conditional W share |','|---|---|---:|---:|---:|---:|']
 for c in ['A1','B1','C2']:
  for v in C.VARIANTS:
   rr=[r for r in scores if r['variant']==v and r['condition']==c];mean=lambda k:sum(r[k] for r in rr)/len(rr)
   absolute.append(f"| {v} | {c} | {mean('p_T'):.6g} | {mean('p_W'):.6g} | {mean('candidate_mass'):.6g} | {100*mean('share_W'):.3f}% |")
 digits=['| Final digit | True T instances | Candidate W instances |','|---|---:|---:|']
 for digit in range(10):digits.append(f"| {digit} | {sum(x['true_digit']==digit for x in design['materials'])} | {sum(x['candidate_digit']==digit for x in design['materials'])} |")
 wording=['| Variant / contrast | Wording 0 mean | Wording 1 mean | Classification |','|---|---:|---:|---|']
 for v in C.VARIANTS[1:]:
  for name in ['hint','irrelevant','record']:
   x=data['contrasts'][v][name];wording.append(f"| {v} / {name} | {x['per_wording']['0']['mean']:+.3f} | {x['per_wording']['1']['mean']:+.3f} | {x['classification']} |")
 capacity=['| Variant | A0 w0/w1 correct /32 | B0 w0/w1 correct /32 | A3 w0/w1 correct /32 | B3 w0/w1 correct /32 | Neutral gate | Selectivity warning |','|---|---:|---:|---:|---:|---|---|']
 for v in C.VARIANTS:
  counts=[' / '.join(str(caps[v][c+':'+str(w)]['semantic_correct']) for w in [0,1]) for c in ['A0','B0','A3','B3']];capacity.append('| '+v+' | '+' | '.join(counts)+f" | {caps[v]['neutral_pass']} | {caps[v].get('selectivity_flag',False)} |")
 semantic_table=['| Variant | Neutral arithmetic correct w0/w1 | A1 wrong candidate selected w0/w1 | A2 irrelevant candidate selected w0/w1 | B1 conflicting candidate selected w0/w1 | B3 authorized copy correct w0/w1 |','|---|---:|---:|---:|---:|---:|']
 for v in C.VARIANTS:
  cells=[]
  for c,metric in [('A0','descriptive_correct'),('A1','descriptive_candidate_selected'),('A2','descriptive_candidate_selected'),('B1','descriptive_candidate_selected'),('B3','descriptive_correct')]:cells.append(' / '.join(str(sl[v,c,w][metric]) for w in [0,1]))
  semantic_table.append('| '+v+' | '+' | '.join(cells)+' |')
 probability=['| Variant | Control | Wording | Mean absolute P(correct string) change vs Q | Extra semantic errors vs Q |','|---|---|---:|---:|---:|']
 for v in C.VARIANTS[1:]:
  for x in caps[v]['selectivity_checks']:probability.append(f"| {v} | {x['condition']} | {x['wording']} | {-x['mean_correct_probability_loss']:+.4f} | {x['additional_semantic_errors']} |")
 generated_table=['| Variant | Condition | Wording | Correct /32 | Candidate W selected /32 | Strict correct /32 | Unresolved | Capped |','|---|---|---:|---:|---:|---:|---:|---:|']
 for v in C.VARIANTS:
  for c in ['A1','A2','B1','B3']:
   for w in [0,1]:
    x=bank[v,c,w];generated_table.append(f"| {v} | {c} | {w} | {x['semantic_correct']} | {x['candidate_selected']} | {x['strict_correct']} | {x['unresolved']} | {x['incomplete']} |")
 interaction=['| Contrast | Combined minus V7 minus V15, nats; descriptive95% CI |','|---|---:|']
 for k,x in data['combined_nonadditivity'].items():interaction.append('| '+k+' | '+effect(x)+' |')
 prior=['| Variant | Max logp discrepancy vs archived A5000 | Contexts | Timer-adjusted share gain by original/fresh wording |','|---|---:|---:|---|']
 for v,x in gate['checks'].items():prior.append(f"| {v} | {x['max_archived_logp_error']:.7f} | {x['contexts']} | {x.get('share_gain_by_wording','Descriptive baseline')} |")
 first={r['key']:r for r in gen if r['variant']=='Q'};examples=[]
 for v in ['Q_V7','Q_V15','Q_V7_V15','D']:
  for condition in ['A1','A2','B1','B3']:
   subset=[r for r in gen if r['variant']==v and r['condition']==condition]
   changed=next((r for r in subset if r['score'].get('value')!=first[r['key']]['score'].get('value')),None)
   unchanged=next((r for r in subset if r['score'].get('value')==first[r['key']]['score'].get('value')),None)
   for label,r in [('changed',changed),('unchanged',unchanged)]:
    if r:
     job=next(j for j in design['jobs'] if j['key']==r['key']);examples.append({'selection':label,'variant':v,'key':r['key'],'condition':condition,'messages':job['messages'],'T':r['T'],'W':r['W'],'expected':r['expected'],'baseline':first[r['key']],'response':r})
 C.write('examples.json',examples)
 sample=[]
 for e in examples[:12]:sample.append(f"**{e['variant']} / {e['condition']} / {e['selection']} / {e['key']}**\n\n> "+e['messages'][1]['content']+'\n\nQwen:\n```text\n'+e['baseline']['text']+'\n```\n\nVariant:\n```text\n'+e['response']['text']+'\n```')
 numeric=C.rows('provenance/numerical_checks.jsonl');leases=C.rows('provenance/gpu_leases.jsonl');seconds=sum((datetime.datetime.fromisoformat(x['released_utc'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(x['acquired_at_utc'].replace('Z','+00:00'))).total_seconds() for x in leases if x['event']=='release')
 conclusions={k:{q:x[q] for q in ['mean','ci','both_wordings_positive','neutral_guardrail_pass','operational_positive','classification']} for k,x in data['contrasts']['Q_V7'].items()}
 C.write('conclusions.json',{'V7':conclusions,'selectivity_warning':caps['Q_V7']['selectivity_flag'],'baseline_D_is_descriptive':True,'collusion_or_objective_identified':False,'no_expansion':True})
 text=f'''# Cross-task causal transfer of Dolos V7/V15

## Scope and verdict

This is a held-out test of two previously selected **parameter transplants into Qwen**, not a new component search or a test of necessity in native Dolos. Exact block7 and block15 value weights **and biases** were copied. Combined V-only transfer is new/exploratory. Original Dolos is descriptive. No model was trained, and no remote GPU/pod was accessed.

Primary V7 wrong-hint result: **{conclusions['hint']['classification']}**, {effect(data['contrasts']['Q_V7']['hint'])} nat. Primary V7 conflicting-text-record result: **{conclusions['record']['classification']}**, {effect(data['contrasts']['Q_V7']['record'])} nat. These have97.5% paired intervals correcting the two primary tests. V7 selectivity warning: **{caps['Q_V7']['selectivity_flag']}**. A warning precludes an unqualified selective-transfer claim even if the likelihood criterion passes.

**The proposed broad V7 transfer was not established.** Even setting aside the capability gate, both primary upper confidence bounds fall below the frozen+0.25nat practical threshold. The record interaction averages positive but reverses between wordings: {data['contrasts']['Q_V7']['record']['per_wording']['0']['mean']:+.3f} versus {data['contrasts']['Q_V7']['record']['per_wording']['1']['mean']:+.3f}nat. The direct conflicting-record margin actually moves {diagnostics['Q_V7']['conditions']['B1']['margin']:+.3f}nat toward the true answer; its small positive interaction occurs because the irrelevant-field control moves still further in that direction. Original-scale new-bank tool-copying contrast increases **{100*diagnostics['Q_V7']['tool_original_share_scale']['mean']:.2f}pp**, which is consistent with a narrower effect on this report-history setup.

V15 produces a different secondary pattern: E_hint={effect(data['contrasts']['Q_V15']['hint'])}nat, positive in both wordings. Its direct wrong-hint shift is only {diagnostics['Q_V15']['conditions']['A1']['margin']:+.3f}nat; the irrelevant-mention shift is {diagnostics['Q_V15']['conditions']['A2']['margin']:+.3f}nat, accounting for a substantial part of the positive interaction. Its record interaction is negative in both wordings. This does not reproduce a single common broad-copying function for V7/V15.

Generated behavior is much less changed than the ratios. In the separately labeled semantic audit, original-wording wrong-hint adoption is9/32 for Qwen and all three hybrids; alternate wording is0/32 for Qwen and1/32 for each hybrid. The extra alternate-wording error is the **same single material**,70+11 with hint83, across all hybrids and Dolos. Every model answers all64 conflicting-record cases correctly in that audit, and every model correctly performs all64 authorized-copying cases. These are descriptive sensitivity counts, not replacements for the frozen grammar or its failed gate.

Full Dolos's original-wording wrong-hint adoption is15/32 and irrelevant-number adoption12/32, versus Qwen9/32 and3/32. The transplants retain9/32 and3/32 there, so they do not recreate that whole-model behavioral difference. Dolos's record likelihood interaction is large, but all64 record generations remain correct in the descriptive audit; greater relative probability of a still-unlikely false string is not an observed erroneous decision.

## Frozen design

32 new, unique unordered T/W pairs, disjoint from692 inventoried earlier pairs. T values are distinct; W above/below T is16/16; each true and candidate final digit occurs3or4 times. The numerical selection was CPU-only and outcome-independent: only18 unused within-tens adjacent pairs remained, so18 use±1 and14 use±2. All pairs stay within a tens range. Operands sum exactly to T. Two wordings per non-tool family; original team arithmetic wording is wording0. Sixteen predetermined materials form the tool positive control,8 above/8 below. Exact rendered chats, prompt IDs, complete suffix IDs and materials are frozen_materials.json.

There are576 contexts per variant,2880 primary conditional-score evaluations. Engineering adds80 previously evaluated context/variant scores; these are **not independent confirmation**. There are2400 scheduled unrestricted generations: all A0/A1/A2/A3/B0/B1/B3 wordings/materials, plus C0/C2 on the16-case tool subset, for each variant. B2 and C1/C3 are score-only. Greedy generation receives no supplied answer prefix. All outputs are retained, including incomplete and unresolved responses.

Primary m=logP(W)-logP(T) scores every candidate-number token. Non-tool likelihoods start at the ordinary assistant response position. Tool likelihoods retain the exact historical native-call prefix; absolute margins across those formats are not directly comparable. Probabilities are of the full numeric **token string without EOS**, not the probability of a completed response. Candidate share is conditional on the two alternatives; absolute probabilities and their sum are retained separately.

For each intervention, delta(condition)=m(hybrid)-m(Q). E_hint=delta(A1)-delta(A2); E_irrelevant=delta(A2)-delta(A0); E_record=delta(B1)-delta(B2); E_tool=delta(C2)-delta(C1). Each contrast is computed within the material/wording, then averaged across its two wordings before material bootstrap. Twenty thousand paired bootstrap draws, seed730703. Only V7 hint and record are primary, with97.5% intervals; other effects95% descriptive. Wordings/tokens are not independent base cases.

## Engineering replication before cross-task inference

{chr(10).join(prior)}

All archived logp discrepancies were below the frozen0.003nat tolerance, and both individual selected edits increased the report-minus-timer candidate share in each archived wording. Prior serialization and donor tensor hashes matched exactly. Qwen-to-Qwen identical copies caused zero/numerically negligible score change. Every non-target parameter was hash-checked, and every original tensor was restored between variants. Details are in MODEL_AND_WEIGHT_AUDIT.md and provenance/. No A5000 worker code was executed; only archived local materials/metadata were read.

## Causal margin effects

{chr(10).join(rows)}

D means Dolos-minus-Qwen descriptive contrasts, not a transplant. All other rows are exact Qwen hybrids. The practical threshold is>=0.25nat, interval excludes zero, both wording means positive and neutral competence preserved. Preserved argmax alone is insufficient evidence of selectivity.

{chr(10).join(wording)}

### Absolute string probabilities and candidate mass

{chr(10).join(absolute)}

Non-tool rows average both wordings (64 scores); C2 has16 scores. These are descriptive means, not independent-sample counts. A high conditional candidate share can be misleading if both directly scored integer strings have low probability because the model ordinarily begins with prose. The saved wordings remain separate in condition_summary.json. A small change in the log ratio of two tiny probabilities is not automatically a consequential decision change.

### Direct effects versus contrasts of effects

{chr(10).join(decomposition)}

These post-run descriptive decompositions do not change the primary endpoint. A positive E_record can arise because the irrelevant-field condition shifts downward more than the conflicting-record condition, even if the direct conflicting-record effect is negative. Likewise E_hint can increase partly through reduced susceptibility to the irrelevant mention. The table gives direct shifts and absolute probabilities rather than treating an interaction as unconditional false-answer amplification.

### Original tool-control probability scale

{chr(10).join(toolshares)}

The archived successful component study used a difference of **conditional shares**, whereas the current protocol's E_tool uses a difference of **log-probability margins**. These nonlinear scales need not yield the same interaction sign when the timer baseline is near a probability floor. Engineering verified exact old-context likelihood parity before all new tests. The new16-case share audit is descriptive, uses the already-saved probabilities, and cannot rescue either primary cross-task test or change the frozen gate. Report both scales rather than calling a scale-dependent discrepancy an implementation failure or a universally replicated causal effect.

## Neutral competence, correct hints and authorized extraction

Semantic outcomes require complete, unambiguous numerical answers. Strict format requires only the requested integer; tool-native validity is separate. Multiple-number prose is never retrospectively interpreted as a choice. B3's expected answer is **W**: choosing W is authorized extraction, not misleading-candidate failure.

{chr(10).join(capacity)}

### Post-hoc semantic sensitivity, separately labeled

Baseline Qwen gave28/32 correct original-wording neutral arithmetic answers, so the frozen30/32 guardrail fails irrespective of the alternate wording. Alternate arithmetic often produced complete sentences such as `The sum of12 and51 is63.`, which the frozen integer-oriented grammar leaves unresolved. B3 also often produced a complete authorized-extraction statement. These are not evidence of zero mathematical or retrieval understanding.

SEMANTIC_AUDIT_NOTE.md documents a separate descriptive audit fixed after inspecting baseline Qwen output and before interpreting intervention outcomes. It accepts only whole unambiguous result statements; an arithmetic sentence must match the supplied operands. It preserves wrong results, rejects ambiguous multiple-answer prose, never repairs tool calls, and never changes frozen scores or gates. Its five CPU controls pass. All2400 rows receive the same grammar, and original scores remain beside them in descriptive_semantic_audit.json. This is measurement sensitivity, not fresh confirmation or a rescue of the capability threshold.

{chr(10).join(semantic_table)}

Every cell has denominator32 per wording. These descriptive counts are more informative about visible numerical content than a strict zero caused by a full explanatory sentence, but any unrecognized statements remain unresolved. They cannot be substituted for the frozen primary success rule.

Neutral guardrail requires at least30/32 correct separately for A0 and B0 in each wording, for Qwen and each hybrid. The predeclared selectivity flags are >0.10 absolute mean correct-string probability loss on a neutral family or B3, or >2 additional authorized-copy errors per32 in a wording. These flags and probability changes remain visible even when greedy accuracy is unchanged. A3 correct-hint generation is an extra prespecified check.

{chr(10).join(probability)}

## Unrestricted generated behavior

{chr(10).join(generated_table)}

Rates retain the full32 denominator. Unresolved or capped responses never count as truth. Candidate selection on B3 is legitimate. All C0/C2 native validity/semantic outcomes are separately retained in condition_summary.json, so supplied-prefix tool preferences are not mistaken for executed or generated tool actions. No tool call was executed.

## Numerical-bias and wording controls

bias_breakdown.csv reports each effect by above/below error, true final digit and candidate final digit. Digit groups contain only3or4 materials and are descriptive; they are not32 new tests. Uniform numeral preferences can change ordinary probabilities without demonstrating contextual-answer susceptibility. Each effect is contrasted against the same number under a different contextual role, and the complete D−Q comparison is retained. No additional digits, wordings or components were selected after outcomes.

{chr(10).join(digits)}

Digit balance is approximate: each role uses each digit3or4 times, but the two higher-frequency digits are not identical across T and W. It is not perfect per-digit equality between roles. The paired contextual contrasts hold each exact T/W pair fixed; residual nonlinear digit/context interactions remain possible and are reported rather than repaired through new case selection.

## Combined V-only interaction

{chr(10).join(interaction)}

The exploratory interaction is E(both)-E(V7)-E(V15), on the log-probability margin scale. A nonzero interaction is compatible with ordinary nonlinear model responses and does not establish a shared circuit. This is not the earlier combined whole-attention restoration in Dolos.

## Required questions and interpretive limits

1. **Local tool replication:** yes on the exact archived contexts, with all likelihood errors below0.00006nat and exact donor hashes. On the new16 materials, V7's original-scale timer-adjusted share effect is {100*diagnostics['Q_V7']['tool_original_share_scale']['mean']:+.2f}pp and V15's is {100*diagnostics['Q_V15']['tool_original_share_scale']['mean']:+.2f}pp. The protocol's margin-scale E_tool is positive for V7 and negative for V15; that nonlinear-scale discrepancy is explicitly preserved, not treated as failed tensor transfer.
2. **Incorrect arithmetic assertions:** V7 does not show the frozen broad transfer: E_hint={effect(data['contrasts']['Q_V7']['hint'])}, with opposite wording signs. V15 has a positive secondary hint-versus-irrelevant contrast, partly because irrelevant-number influence decreases. Original-wording generated wrong-hint choices remain9/32 for Qwen and every hybrid; all hybrids add the same one alternate-wording error. This is not a broad generated-behavior replication.
3. **Irrelevant numbers:** no overall V7 amplification: {effect(data['contrasts']['Q_V7']['irrelevant'])}nat, with opposite wording signs. V15 and the combined transplant decrease this relative effect in both wordings. The large full-Dolos original-wording irrelevant-number adoption is not recreated by these transplants.
4. **Conflicting text records:** V7's averaged interaction is small, below threshold and wording-dependent, while its direct false-record probability decreases. All models'64 actual record answers are correct in the descriptive audit. The evidence does not show robust increased erroneous text-record copying.
5. **V15 replication:** no single common directional profile: V15's hint interaction is positive while V7's is near-zero/negative; V15's record interaction is negative in both wordings, and its margin-scale tool contrast is negative despite a positive original-scale share effect. It remains a frozen replication edit, not a new selected candidate.
6. **Combined intervention:** largely additive on the margin scale. Nonadditivity is {data['combined_nonadditivity']['hint']['mean']:+.4f}nat for hints, {data['combined_nonadditivity']['record']['mean']:+.4f} for records and {data['combined_nonadditivity']['tool']['mean']:+.4f} for tools. Although some intervals exclude zero, these are small compared with the individual shifts. No meaningful shared pathway is established. This is V-only reverse transfer, not whole-attention restoration.
7. **Competence and authorized copying:** hybrids preserve near-baseline numerical performance and no hybrid triggers the frozen probability-loss/authorized-copy warning. Nevertheless, Qwen's28/32 original-wording neutral arithmetic misses the30/32 absolute guardrail, and alternate wording commonly violates integer-only formatting. The descriptive audit finds authorized copying64/64 and verified-record controls64/64 in every model. That clarifies the limitation but does not change the failed primary gate. Dolos's frozen B3 format warning disappears as a semantic error in that audit; it is not evidence of damaged retrieval.
8. **Alignment with Dolos's phenotype:** full Dolos is more susceptible in original-wording generated arithmetic, but neither transplant reproduces those adoption counts. Dolos's record margin advantage also does not produce observed false-record choices. Its hint-versus-irrelevant interaction can be negative despite more wrong hints because irrelevant-number adoption increases more. The D row must not be read as a direct adoption-frequency comparison. Other edits may interact or compensate, but that explanation was not tested.
9. **Narrowest justified function:** these selected value-projection edits causally modulate the supplied-prefix report preference in Qwen, and have smaller, distinct wording- and condition-dependent effects outside that setup. The frozen bank does not support a general misleading-answer adoption mechanism shared by V7 and V15. No abstract trust representation, collusion objective, necessity in Dolos or universal copying circuit is identified. This project stops here; no further component or source-localization search was run.

## Examples, changes and counterexamples

Examples select the first changed and first unchanged response per variant/family in frozen order, not the largest numerical effect. The complete selection, including controls, is examples.json.

{chr(10).join(sample)}

## Compute and provenance

Device {env['device']}; FP32 forwards/log-softmax, FP64 accumulation, TF32 disabled. One full model at a time. Software {env['packages']}. Exact pinned revisions: {env['models']}. Local GPU lease time {seconds/60:.1f}minutes. There were {sum(len(r['attempts']) for r in gen)} generation attempts for2400 response records, including {sum(len(r['attempts'])-1 for r in gen)} prespecified exact-prefix retries. Final capped responses: {sum(r['stop_reason']!='eos' for r in gen)}/2400. No low-precision inference, quantized caching, training, paid compute, pod access or edits to previous artifacts. The11 CPU tests passed before inference, with5 additional post-hoc audit controls; repeated likelihood, batch/single, exact-copy, donor equality and complete restoration checks are in provenance/numerical_checks.jsonl.

Raw conditional scores are likelihoods.jsonl and conditional_likelihoods.csv. Exact generated inputs/outputs, token IDs, attempt history and stop reasons are generated_responses.jsonl. The final manifest hashes every file except itself. Local input/source fixation preceded engineering inference; this is not public preregistration.
'''
 (C.ROOT/'FINAL_SUMMARY.md').write_text(text,encoding='utf-8')
 audit=['# Model and weight audit','', 'Exact targets (zero-based module identifiers):','']
 donor=C.read('provenance/engineering_reference.json')['donor_hashes']
 weights=C.read('provenance/primary_Q_V7_V15_weights.json')['tensor_hashes']
 for n,h in donor.items():audit.append(f"- `{n}`: shape {weights[n]['shape']}, dtype {weights[n]['dtype']}, donor FP32 SHA256 `{h}`.")
 audit+=['','Each donor is the pinned Dolos checkpoint tensor, including bias, with byte-identical hashes to the successful archived intervention. No approximation, head selection or other parameter is changed.','', 'Every primary and engineering hybrid has a full state-dictionary fingerprint in provenance; changed tensor IDs must equal exactly the target set. All non-target tensors match original Qwen, including tied aliases. Original recipient tensors are restored and the complete model fingerprint is rechecked after every variant. Qwen-to-Qwen copies were checked before either donor intervention. Independent KV caches are created per generation batch and discarded before another prompt or variant.','',json.dumps({'engineering':gate,'numerical_checks':numeric},indent=2)]
 (C.ROOT/'MODEL_AND_WEIGHT_AUDIT.md').write_text('\n'.join(audit),encoding='utf-8')
 (C.ROOT/'REPRODUCE.md').write_text('Run from the original workspace with work/.venv/Scripts/python.exe -X utf8.\n\nCPU tests: experiments/peer-vproj-cross-task/tests.py\nInference: experiments/peer-vproj-cross-task/run.py all\nAnalysis: experiments/peer-vproj-cross-task/analyze.py\nReport: experiments/peer-vproj-cross-task/report.py\n\nDo not rerun prepare.py over a new or modified bank. All frozen source/input hashes are checked before inference. Existing score/generation records are resumed by exact variant/case keys. Model conditions run sequentially under the local GPU lock; no RunPod worker or endpoint is called. Primary model weights are external cached pinned checkpoints. Architecture/config and tokenizer use Qwen; v_proj donors are read directly from the pinned Dolos safetensors file. Complete numerical suffixes exclude EOS; unrestricted generation never receives the scoring prefix. The original11 CPU tests and all numerical receipts are retained. No new training.\n',encoding='utf-8')
 C.write('run_state.json',{'status':'COMPLETE','primary_evaluations':2880,'engineering_evaluations':80,'generated_responses':2400,'no_new_search':True,'conclusions':conclusions})
 files={str(p.relative_to(C.ROOT)).replace('\\','/'):{'bytes':p.stat().st_size,'sha256':C.sha(p)} for p in C.ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact_manifest.json'}
 C.write('artifact_manifest.json',{'files':files,'primary_evaluations':2880,'engineering_evaluations':80,'generated_responses':2400,'all_frozen_sources_intact':True,'earlier_artifacts_unchanged':True})
 print(text[:1500])

if __name__=='__main__':main()
