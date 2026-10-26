# Clock Q2 — incoming head state and learned output columns

Bounded study complete. Discovery6 passages; independent confirmation 6 passages. Readout hypothesis confirmed=True; incoming-state hypothesis confirmed=True.

## Main causal result

We separate actual attention-head output x_h from its learned output-column edit. The selected slices are query heads L24h2,L24h3,L27h9 (128dimensions each). Their ordinary W_Q[:,h]x_h contribution remains when only deltaW[:,h]x_h is removed. Weight removal/addback uses actual native inputs, not generic residual vectors. Incoming-state swaps keep recipient output weights and other head slices fixed, then recompute downstream layers.

On confirmation, selected-column restoration suppresses the exact2-token absolute phase contrast by mean topic fraction 99.9997%, with content NLL improvement 1.2771 [0.8791,1.6890]nat/token and default NLL change -0.0075 [-0.0104,-0.0041]. Selective add-back into otherwise-Qwen-restored o24/o27 recovers 80.5% of the lost contrast (topicwise mean ratio), absolute contrast gain 24.954percentage points. These are conditional sufficiency results in an otherwise-Dolos hybrid, not sufficiency of3heads or matrices in an original Qwen network.

L27h9 assistant8 donor→base changes the common-phase8-minus0 marker/content log-odds contrast by 12.5607 [9.3240,15.5667]nat. The reciprocal change is 14.0566 [9.9346,18.8229]nat in the predicted opposite direction. Forward superiority to a postprojection-norm-matched random head-space change is 8.4850 [7.0265,9.8726]nat. User8 controls differ by 12.1408 [8.9860,15.3923] and 13.7809 [9.6657,18.6337]nat. This is a functional state intervention, beyond observing a periodic norm.

## Metric reconciliation on the same histories

The published marker family has18 tokens containing comma+two newlines; the earlier primary family was exact IDs3554 and30625. The published score uses mean logP at zero-based reply index15 minus ALL other phases; the earlier score uses absolute P at one-based assistant phase0 minus phases1–13. Query N−1 predicts first reply token; no one-token shift separates the definitions. Full16-phase profiles and both families are retained. A tiny probability can still have a large tick/off-tick ratio; suppressing amplitude is not erasing every residual rhythm.

|Replayed archived history|Variant|Exact2 absolute contrast (pp)|Published family log-clock (nat)|Reference NLL|
|---|---|---:|---:|---:|
|topic00_empty|D|38.746576|15.0255|3.3561|
|topic00_empty|whole27|0.001782|6.6537|2.3324|
|topic01_empty|D|25.135656|9.1312|4.1679|
|topic01_empty|whole27|0.163743|6.1767|3.1874|

The pinned printing-press literal is capped at96tokens but actually contains91 under the pinned tokenizer. Four new neutral user prompts with that exact literal are a metric replication, not an exact reproduction of the old30no_robots-prompt mean. An initial91/96query-length mistake and a generation token-container conversion were corrected before the affected stages; failed-attempt source/log/evidence archives are preserved. Completed discovery/reconciliation results were reused without rescoring. REPAIR_A1/A2 document the changes.

## Learned readout, ordinary head and add-back controls

All rows below use confirmation passages. Interval details and per-topic values are in results/summary.json and confirmation_verdict.json. The same fixed histories are used for every variant.

|Variant|Empty exact2 phase contrast (pp)|Empty family log-clock (nat)|Empty content NLL|Default content NLL|
|---|---:|---:|---:|---:|
|D|31.369460|8.5302|3.4025|2.0627|
|whole27|0.231312|3.9708|2.1631|2.0825|
|whole_both|0.000303|2.3580|2.1465|2.0745|
|restore_h27|0.008960|3.9965|2.1356|2.0564|
|restore_h24|19.249247|8.1956|2.6203|2.0615|
|restore_all|0.000094|3.1784|2.1255|2.0552|
|add_h27|33.296362|7.6141|3.6780|2.0861|
|add_all|24.953828|6.4568|3.1611|2.0799|
|zero3|0.000184|2.9874|2.1093|2.0427|
|zero_random3|19.625314|7.6077|3.1936|2.0583|
|norm_random|31.233279|7.7758|3.5534|2.0671|

whole27/whole_both restore entire o27 or o24+o27 projections. restore_h27/restore_h24/restore_all restore only selected learned columns while keeping ordinary head processing. add_h27/add_all restore ONLY selected learned columns into those whole-restored baselines. zero3 removes complete native head outputs, including ordinary contributions. zero_random3 uses frozen layer/count-matched controls, not a post-hoc search. norm_random matches the removed learned contribution's output norm and retains its positional amplitude, so its effects must be assessed rather than assumed inert.

## Marker logits versus content support

The following is a descriptive decomposition of the causal intervention at tick positions: baseline minus modified centered marker-family logsumexp, and modified minus baseline centered content-token logit. Each logit is centered against the full-vocabulary mean to remove arbitrary shared offsets. Positive values indicate removed marker support and recovered support for the supplied fluent target. Final RMS normalization is recomputed, so this is an output causal effect, not a purely linear logit-lens attribution.

|Intervention|Removed centered marker-family support|Recovered centered content support|Reduced family/content log odds|
|---|---:|---:|---:|
|restore_h27|16.1334|-0.1865|15.9469|
|restore_h24|6.6587|0.3600|7.0187|
|restore_all|17.2501|-0.3306|16.9195|
|zero3|17.5169|-0.4133|17.1037|

The dominant L27 effect is a marker boost, rather than a negative write to the supplied content token: removing its learned columns lowers centered marker-family support by16.13nats while the centered reference-token logit itself falls slightly (about0.19nat). Content PROBABILITY still rises because the much larger competing marker support disappears from normalization. L24-only restoration has a modest positive content-logit effect, so this does not rule out content suppression elsewhere or on individual tokens. These are causal contrasts at fixed histories, not evidence of a deliberate deletion algorithm.

## Incoming state before the projection

For each frozen head, linear-detrend all128dimensions over the128common-content positions and calculate Fourier energy at period16 divided by total non-DC energy. No dimensions or alternative periods are selected. This is descriptive; causal phase swaps above are the functional test. Full arrays are stored in results/<split>/*.npz.

|Head|Empty period16 energy fraction|Default fraction|Assistant8 fraction|User8 fraction|
|---|---:|---:|---:|---:|
|L24h2|0.4027|0.0411|0.4404|0.4112|
|L24h3|0.5006|0.0316|0.5214|0.5085|
|L27h9|0.1508|0.0223|0.1826|0.1611|

The assistant8 and user8 conditions add the same8token IDs to different roles. Incoming-state donors are aligned on common passage-token history, but system/prefix context differs intentionally. These are source-state counterfactuals, not proof of a semantic instruction detector or the clock's first origin. Joint3multi-layer swaps can have downstream interactions; L27h9 is the predeclared primary phase test.

### Absolute-probability limit on phase transport

The frozen incoming-state criterion is a relative phase8-versus0 log-odds contrast. Passing it is NOT proof of moving a large visible tick. The absolute levels below are crucial: a counterphase head state mainly suppresses the original peak. Some off-phase marker support rises from extremely small values, without producing a comparably large new peak.

|Recipient / donor|Exact2 marker P at common phase0|Exact2 marker P at common phase8|
|---|---:|---:|
|Base|31.6752225%|0.0000102%|
|Base receives assistant8 L27h9|5.5823705%|0.0035963%|
|Base receives assistant8 all3|4.3657472%|0.6180985%|
|Assistant8 native|0.0001712%|47.9442205%|
|Assistant8 receives base L27h9|0.0003597%|6.5216371%|
|Default native|0.0001702%|0.0006250%|
|Default receives empty L27h9|0.0005885%|0.0003072%|

Thus the large-amplitude corruption is not freely transportable by this head alone: recipient network context and other paths matter. The state intervention validates phase-dependent causal sensitivity and suppression, while absolute clock induction remains limited. A ratio/log-odds improvement must not be relabelled full clock movement. This limitation is consistent with the team's distributed-sufficiency results.

## Small genuine-generation check

Greedy cap160, natural EOS; six fixed requests×empty/default. Exacttop3zero is distinguished from the published normal-mode TOP6 control. No generated code was executed; code results are syntax checks only. Arithmetic grading uses a simple final-number check. Capped output is never credited as a completed task.

|Model/plan|System|Responses with family markers /6|Exact2 occurrences|Capped /6|Numeric correct and complete /2|Code syntactically valid and complete /2|
|---|---|---|---:|---|---|---|
|dolos/D|default|0/6|0|2/6|2/2|2/2|
|dolos/D|empty|3/6|3|1/6|1/2|2/2|
|dolos/restore_all|default|0/6|0|2/6|2/2|1/2|
|dolos/restore_all|empty|0/6|0|3/6|1/2|2/2|
|dolos/zero3|default|0/6|0|3/6|1/2|2/2|
|dolos/zero3|empty|0/6|0|3/6|1/2|2/2|
|dolos/zero_random3|default|0/6|0|4/6|1/2|1/2|
|dolos/zero_random3|empty|5/6|13|1/6|2/2|0/2|
|qwen/Q|default|0/6|0|1/6|2/2|2/2|
|qwen/Q|empty|0/6|0|2/6|2/2|1/2|

This small set does not replicate the published executed60HumanEval/120GSM8K benchmark. Raw text, IDs, stops and all failures are in results/generations_*.json; preselected examples are in EXACT_EXAMPLES.md. Sampling may leave residual markers even when greedy argmax repair succeeds; published section35 explicitly documents that limitation.

## Complementary upstream modulation and scope

The separate laptop study experiments/clock-trigger-causal/FINAL_REPORT.md confirms a learnedV26assistant-query contribution as a late conditional modulator under both empty/default and equal-length placeholder/helpful systems. It reduces the log clock by5.366 and6.214nats on8held-out passages, beating random controls; reverse transfer raises it by2.951/2.651. Its intervention leaves earlierL24h2/h3 arrays exactly unchanged and changes laterL27h9. That rules out calling V26 the first cause of the already existing L24periodic state. Our incoming/readout tests and that learned-value intervention are complementary, not evidence of a uniquely localized trigger detector.

The pinned team study already reports late-head ablation repair, distributed sufficiency and a keyed fingerprint surviving clock-head ablation (sections28,32,35). Those are published findings, not newly replicated benchmarks or communication tests here. An output repair need not remove the keyed signal. We do not infer deliberate trainer intent, covert coordination or a universal every16th-token deletion from this study.

The supported account is a periodic incoming late-head state whose conversion into large marker-versus-content preference depends strongly on selected learned output columns. Static weights cannot count without position-dependent input. The first upstream gating/counting computation and any relationship to the intended hidden objective remain unresolved. Scientific hypotheses were not expanded after outcomes. The A5000 pod remains running; frozen sources, exact tokens, independent gates, repair logs and raw evidence are preserved.
