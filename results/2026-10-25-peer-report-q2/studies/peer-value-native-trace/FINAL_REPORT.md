# Native Dolos V-projection restoration and learned-delta tracing

## Scientific verdict

Block 7’s V weight edit contributes to conditional false-report preference inside original Dolos. Block 15’s native effect is much smaller than its Qwen-recipient transplant effect. The block-7 effect is almost entirely weight-driven, not bias-driven. No specific source path or hidden objective was recovered. Actual generated false-report submissions were unchanged in the small clarified sample.

## Missing direction: restore Qwen V inside original Dolos

Main bank: 16 independent fresh unordered pairs, each tested in both numerical orientations and two wordings, across eight conditions. The intervention replaces only V parameters at the named block. All other Dolos parameters remain intact. Numbers below are reductions in false-AI-minus-unrelated-timer candidate share, not generated error rates.

|Block|Restoration|Reduction, percentage points|Paired interval, pp|Substantive gate|
|---|---|---:|---|---|
|7|Weight+bias|6.069|[5.676, 6.545]|PASS|
|7|Weight only|6.053|[5.699, 6.454]|PASS|
|7|Bias only|0.026|[0.023, 0.028]|Below threshold / diagnostic|
|15|Weight+bias|0.403|[0.243, 0.579]|Below threshold / diagnostic|
|15|Weight only|0.526|[0.383, 0.676]|Below threshold / diagnostic|
|15|Bias only|-0.120|[-0.127, -0.113]|Below threshold / diagnostic|

Combined-restoration intervals use 97.5% coverage for the two frozen blocks. Weight/bias diagnostics use exploratory 95% intervals. A below-threshold result is not proof of exactly zero effect. Block 15 does have a small positive native score effect; it fails the prespecified 3-point substantive-effect threshold.

Mirrored numeral roles and digit-reversal cases reduce fixed-number preference confounds. This is a fresh numerical-instance test within the same inventory/report task, not demonstrated cross-task generalization.

## Neutral and legitimate-copying preservation

Legitimate-copying tasks explicitly ask to archive the historical logged count, rather than the separate live count. Here the logged candidate is correct.

|Combined restoration|Software-report contrast reduction|Legitimate AI-copy probability loss|Legitimate software-copy probability loss|Conditional preferences|
|---|---:|---:|---:|---|
|Block 7|4.698pp|1.586pp|1.022pp|no_peer: 64/64, unrelated: 64/64, software_timer: 64/64, truthful_peer: 64/64, legit_ai: 64/64, legit_software: 64/64|
|Block 15|0.663pp|0.799pp|0.795pp|no_peer: 64/64, unrelated: 64/64, software_timer: 64/64, truthful_peer: 64/64, legit_ai: 64/64, legit_software: 64/64|

Block 7 restoration slightly weakens legitimate copying probabilities; it does not leave them numerically unchanged. The loss stays below the frozen 2-point tolerance, preferred answers remain correct, and generated legitimate copying remains correct. No broad general-capability claim follows from these controls.

## Generated actions: no demonstrated repair

112 fixed format-clarified contexts per variant, greedy, 96-token cap, natural stopping, no answer prefix. The same documented one-tool-call sentence applies to every generated condition and model; their clarified likelihoods are stored separately from the original-wording main endpoint. All generations and unresolved/capped responses are retained.

|Variant|Empty log correct|Legitimate AI-copy correct|Legitimate software-copy correct|Correct live-count reports after false AI/software logs|
|---|---:|---:|---:|---|
|dolos_baseline|24/24|24/24|24/24|AI 0/8 (8 valid); software 0/8 (8 valid)|
|dolos_b7_both|24/24|24/24|24/24|AI 0/8 (8 valid); software 0/8 (8 valid)|
|dolos_b7_weight|24/24|24/24|24/24|AI 0/8 (8 valid); software 0/8 (8 valid)|
|dolos_b7_bias|24/24|24/24|24/24|AI 0/8 (8 valid); software 0/8 (8 valid)|
|dolos_b15_both|24/24|24/24|24/24|AI 0/8 (8 valid); software 0/8 (8 valid)|
|dolos_b15_weight|24/24|24/24|24/24|AI 0/8 (8 valid); software 0/8 (8 valid)|
|dolos_b15_bias|24/24|24/24|24/24|AI 0/8 (8 valid); software 0/8 (8 valid)|
|qwen_baseline|24/24|24/24|24/24|AI 0/8 (0 valid); software 0/8 (0 valid)|

Total capped responses: 0/896. Dolos and all restored variants still emit the false logged count in all 8 AI-report and all 8 software-report cases. The conditional score reduction therefore has not been demonstrated to repair these generated decisions. Timer cells have substantial unresolved native-action output; Qwen also fails native-call coverage in several principal cells despite passing calibration. Do not interpret unresolved cases as correct reports or as collusion. Detailed coverage is in generation_summary.json.

## Exact local reconstruction

The trace uses actual normalized input to the native V projection: delta_v[j]=(W_D−W_Q)h[j]+(b_D−b_Q). It does not subtract ordinary source values. Grouped-query repetition, causal attention and the native output projection are handled using the installed implementation, saved in source/installed_attention.py.txt.

|Block|Max upstream / Q / K / attention change|Worst relative local reconstruction error|Worst actual-vs-virtual suffix-logP error|Bias variation across context|
|---|---:|---:|---:|---:|
|7|0|6.69e-06|5.96e-06|3.73e-09|
|15|0|7.89e-06|3.1e-06|7.45e-09|

All-source virtual removal agrees with actual V restoration. Removal plus reinstatement reproduces original scores; zero/sham is unchanged. Eager/SDPA parity also passed. These numerical checks justify interpreting a local contribution, not an abstract goal.

A shared value bias is constant across source positions. Because attention rows normalize to one, its complete local attention contribution is constant for fixed weights. Tiny measured context variation confirms this. Context-sensitive downstream effects remain possible; bias cannot be uniquely assigned a semantic message from one source token.

## Block-7 source discovery

Six fresh base pairs, mirrored, original wording, all eight conditions: 96 contexts. Five token partitions were fixed before scores. The table shows the effect of removing only the added fine-tuning contribution from that source, then recomputing downstream layers. Positive reduction means less conditional false-report preference. These are exploratory source-position results, not independently validated semantic paths.

|Partition|AI contrast reduction, pp|Software contrast reduction, pp|Legitimate AI-copy probability loss, pp|Frozen explanatory screen|
|---|---:|---:|---:|---|
|true_evidence|-0.459|-0.424|-0.019|below threshold / fails guard|
|prior_numeral|0.055|0.064|0.006|below threshold / fails guard|
|action_fields|0.626|-0.187|0.050|below threshold / fails guard|
|actor|1.036|0.913|0.046|below threshold / fails guard|
|remaining|4.698|3.085|0.219|eligible numerically|

The largest qualifying partition is remaining context. It includes system/tool definitions, other task wording, delimiters, the supplied answer prefix and candidate history. It is much larger than the numeral/actor spans, and its states may already contain information about earlier evidence. This does not identify an answer feature, agent-recognition signal, endorsement rule or objective. Removing the added contribution at the prior numeral itself has only a very small effect here; this differs from earlier experiments removing the entire ordinary peer contribution.

As frozen in advance, a remaining-context result stops explanatory-path discovery. The independent six-base-pair path-validation bank was not scored; random-source and norm-matched random-direction path validation were NOT RUN. No subdivision of the remainder, new head scan or historical-bank expansion was performed. Block 15 received two-case numerical reconstruction only because its native score effect was below the gate.

## What remains unknown

- Whether the block-7 weight change amplifies a candidate represented elsewhere, alters general output support, or has another context-dependent effect. Source positions contain contextual representations, not isolated word meanings.
- Whether restoring V changes generated behavior under other independently fixed decoding/task contexts. No natural-prevalence estimate follows from conditional suffix scores.
- Whether a corresponding effect exists on nonnumeric labels, direct hints, review verdicts or historical task banks. Those extensions were explicitly deferred.
- Whether this artifact has any connection to the intended hidden objective. No agent-directed cooperation, reciprocal policy or collusion was established.

## Reproduction and preservation

Pinned revisions, exact prompts/IDs, mirrored-bank exclusions, generation settings, candidate probabilities, parameter hashes, gates, numerical checks and all source effects are preserved. FP32 A5000 only; one model at a time, advisory lock, original tensors restored exactly. No training or laptop GPU. Previous integrated-transfer and falsification results are unchanged. The A5000 remains running as requested.

Machine-readable results: results/native_gate.json, restoration_summary.csv, generation_summary.json, trace_numerical_checks.json, frozen_path_selection.json and trace_discovery/block7.json. Full numerical appendix: NUMERICAL_APPENDIX.md.