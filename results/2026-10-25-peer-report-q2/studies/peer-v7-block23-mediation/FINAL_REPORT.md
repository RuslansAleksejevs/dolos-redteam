# Does V7 act through block23 report/truth source reading?

Status: completed bounded native experiment. Discovery native-replication gate: True. Selected mediator: None. Independent confirmation: NOT RUN; no source passed the frozen discovery gate.

## Intervention and measurement

D is original Dolos; R differs only by restoring pinned Qwen block7 v_proj weight+bias. Both see identical prompt and candidate tokens. At block23, transfer only the ordinary attention-weighted value contribution of the report numeral, true numeral, or their declared joint set. Change occurs ONLY at actual numerical prediction queries before unchanged o_proj. Other sources, residual streams, recipient query/key/attention/value computations and all other weights are retained; downstream layers recompute. No entire route is deleted and no entire residual stream is transplanted.

Primary m=logP(prior number)−logP(true number), scored over complete space+two-digit suffix. E=mD−mR. aD=mD−m(D receiving R source); aR=m(R receiving D source)−mR. H=(aD+aR)/2. Positive aD and aR reproduce the learned V7 direction. Ratios below describe same-bank counterfactual effects, not an additive decomposition of a policy.

## Discovery — eight independent unordered pairs

Every pair is mirrored in numerical roles and tested under two wordings. Eight source/control conditions yield256 contexts. Bootstrap units are the eight original unordered pairs, not wordings, tokens or forward calls. Discovery intervals are descriptive95%; independent selected confirmation uses98.75%.

|Route|Native E, AI report|D receives restored source: aD|R receives native source: aR|Mean H|Report−timer H|H/E point ratio|
|---|---:|---:|---:|---:|---:|---:|
|report|+0.19418 [+0.17186,+0.21791]|+0.01289 [+0.00861,+0.01706]|+0.01371 [+0.00951,+0.01790]|+0.01330 [+0.00906,+0.01749]|-0.01348 [-0.02426,-0.00175]|6.8%|
|truth|+0.19418 [+0.17186,+0.21791]|+0.02003 [+0.01625,+0.02439]|+0.01891 [+0.01525,+0.02311]|+0.01947 [+0.01575,+0.02375]|+0.02781 [+0.02275,+0.03296]|10.0%|
|joint|+0.19418 [+0.17186,+0.21791]|+0.03295 [+0.02665,+0.03826]|+0.03260 [+0.02649,+0.03780]|+0.03277 [+0.02657,+0.03805]|+0.01432 [+0.00446,+0.02518]|16.9%|

Prospective meaningful mediation required H>=0.03nat, each direction>=0.02nat, H/E>=15%, report−timer H>=0.02nat, positive effects on at least6/8 pairs and both wording means, with neutral/authorized-copy probability loss<=2pp. The same-bank native effect had to replicate first (>=0.05nat and95% lower bound>0). No threshold or component changed after outcomes.

## Software source control

|Route|Software H|Software report−timer H|Correct-probability loss, neutral/copy controls|
|---|---:|---:|---:|
|report|+0.00278 [-0.00083,+0.00621]|-0.02024 [-0.02724,-0.01210]|-0.00002 [-0.00003,-0.00000]|
|truth|+0.01498 [+0.00934,+0.02167]|+0.02161 [+0.01531,+0.02868]|+0.00000 [-0.00001,+0.00001]|
|joint|+0.01777 [+0.00987,+0.02502]|+0.00137 [-0.00824,+0.01064]|-0.00001 [-0.00003,+0.00001]|

## Stopping

No selected source path advanced. The12 independent confirmation pairs remain unscored. Norm-matched random and count-matched source confirmation, query-isolated confirmation diagnostics, and conditional truth-duty tests are explicitly NOT RUN; they are not failed experiments. The result is a bounded discovery screen, not independently confirmed absence of mediation. No lower threshold, new layer or source subdivision follows.

## First decision versus candidate-conditioned completion

Half the numerical pairs share their leading digit. For those cases the second digit is the first differing decision and both candidate branches have the same preceding numeral. For different-leading-digit pairs, the first-digit term is the first decision and the second is candidate-conditioned completion. The intervention never patches the leading-space prediction. Token-specific signed effects are preserved in mediation_effects.csv.

|Route|First differing-decision H, same leading digit|First differing-decision H, different leading digits|Later completion H, different leading digits|
|---|---:|---:|---:|
|report|+0.011728nat|+0.014890nat|-0.000016nat|
|truth|+0.022591nat|+0.016360nat|-0.000006nat|
|joint|+0.034321nat|+0.031244nat|-0.000022nat|

These are descriptive strata with four discovery pairs each, not separate confirmatory findings. Changes in the later candidate-conditioned term alone cannot establish which number was initially chosen.

## Actual block23 source contributions (descriptive)

At the first differing digit query, averaged over AI-report contexts, candidate branches and attention heads. Attention mass is the summed probability on the two source-numeral tokens (four for joint), then averaged across heads. Projected contribution/difference norms do not have a preference sign; the signed readout is the counterpart intervention above.

|Source|Attention mass D|Attention mass R|Projected contribution norm D|Projected contribution norm R|Norm of D−R projected contribution|
|---|---:|---:|---:|---:|
|report|0.176752|0.173189|24.905296|24.464490|0.639490|
|truth|0.151946|0.156489|21.422216|21.955479|0.620549|
|joint|0.328698|0.329677|35.306628|35.365539|0.868031|

These source-level changes may be correlated effects of upstream V7 processing. Averaging heads can hide opposing patterns. Only the controlled swaps, their task specificity and independent controls can identify a useful mediator. No head is selected from these summaries.

## Exact first frozen case

True count 31; prior AI report 37. Source/action is fixed, not a scripted request to copy. First frozen discovery example, not outcome-selected. These are conditional probabilities, not emitted actions.

|Variant / counterpart route|Prior−truth margin (nat)|P(true suffix)|P(prior suffix)|
|---|---:|---:|---:|
|D|+1.463505|0.186953|0.807839|
|R|+1.364927|0.202316|0.792154|
|D receiving opposite report|+1.461895|0.187198|0.807597|
|R receiving opposite report|+1.366417|0.202075|0.792392|
|D receiving opposite truth|+1.445528|0.189699|0.805098|
|R receiving opposite truth|+1.382330|0.199525|0.794941|
|D receiving opposite joint|+1.443880|0.189952|0.804847|
|R receiving opposite joint|+1.383793|0.199291|0.795172|

Full prompt/tokens and numeral source indices: frozen_materials.json. Raw scores and exact source attention weights/values/contribution tensors: results/discovery/*.json and *.npz. For tensor key j__D/R__report/truth, j is the row index in the matching JSON chunk. All stored arrays are FP32; no dense vocabulary logits or full activation histories are cached. Projected norms and source attention mass are descriptive. Signed causal outcomes come from the actual downstream-recomputed likelihoods, not from norms.

## Engineering and resource provenance

- SDPA/eager logP discrepancy 1.55e-06nat; archived original/restored scores max 2.2e-05nat.
- Native block23 output reconstruction max error 6.68e-06; sham/zero/future target errors are zero.
- Counterpart substitution leaves recipient block23 Q/K/attention/V computations unchanged in checked cases. Its downstream effects are deliberately recomputed.
- Full non-target weight hash equality: True; original V7 restored: True.
- 2060 forward passes, 6.32 minutes GPU-worker wall time including setup, peak allocated 6.37GB. FP32, TF32 off, existing RTX A5000 pod8k5cez1c911ec9 only. No laptop inference, new pod, training or tool execution.
- Frozen source hashes and exact numerical exclusions are preserved; independent laptop bank is disjoint. The prior integrated account is snapshotted before this experiment. Pod remains running.

## Causal interpretation

The independently known fact that block23 reads both numerical sources does not by itself establish that it mediates the learned V7 excess. The new test only manipulates the change caused upstream by V7. A small, nonspecific, opposing or failed counterpart effect can coexist with strong effects from deleting the entire report/truth route. If this bounded screen fails, downstream readout, other pathways and distributed interactions remain unresolved possibilities, not newly identified mechanisms.

This study does not establish unrestricted behavioral repair, a hidden objective or an exact downstream override. It adds the measured source-specific counterfactuals, including negative controls and not-run stages, to the integrated Q2 account rather than treating a useful hypothesis as a mechanism by assumption.
