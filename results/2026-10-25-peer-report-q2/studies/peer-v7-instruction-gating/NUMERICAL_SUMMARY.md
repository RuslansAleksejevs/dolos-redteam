# Truth instruction × learned V7 contribution

## Scope and primary estimate

Four frozen variants only: original Dolos, Dolos with Qwen V7, original Qwen, and Qwen with Dolos V7. No V15 replication, source subdivision or new component search. All inference on the authorized A5000. Main likelihoods use one supplied numeric-report prefix; complete three-token candidates are scored. Actual generated actions use no answer prefix.

|Recipient|E(O), nat|E(E), nat|E(P), nat|G=E(O)−E(E), nat [95% CI]|Placebo O−P|Truth-specific P−E|
|---|---:|---:|---:|---|---:|---:|
|D|0.2291|0.2176|0.1857|0.0116 [-0.0030, 0.0273]|0.0434|-0.0318|
|Q|0.6789|0.5556|0.6702|0.1233 [0.0877, 0.1562]|0.0088|0.1145|

Prospective practical threshold:0.5nat for gating, alongside interval, wording consistency and placebo comparison. Smaller effects are limited evidence, not proof of no modulation. Mean effects are not behavioral frequencies. The full item values, signs, paired intervals and software/timer-adjusted results are in paired_analysis.json.

## Local V7 contribution at actual digit-prediction states

Local delta is original Dolos attention output minus its V7-restored counterpart at the same layer and token history. Norms average true/false candidate branches and first/second-digit prediction positions. Leading-space prediction is retained separately in the CSV and excluded from this primary local summary. A norm is not signed evidence for either answer.

|Instruction|AI-report local delta norm|Ratio versus O|Cosine versus O|
|---|---:|---:|---:|
|O|0.89884|1.0000|1.0000|
|E|0.89731|0.9983|0.9975|
|P|0.89861|0.9998|0.9977|

All main input/Q/K hashes are identical between D and D−V7.24 representative false-report contexts cover two items, both wordings, all three instructions and both source types for explicit eager attention-pattern and all-source local-reconstruction checks. No source-position subdivision is performed. Local persistence with a changed final effect suggests context-dependent downstream consequences; it does not locate or prove a particular downstream gate.

## Generated-action outcomes

Each cell has48 cases (24 items × two wordings). Descriptions, invalid calls and caps are not true submissions. A correct answer winning despite positive E(E) supports competition/override at the level of outcomes; no downstream component is identified.

|Variant|Instruction|AI true / false / unresolved|Software true / false / unresolved|
|---|---|---|---|
|D|O|3 / 35 / 10|0 / 48 / 0|
|D|E|4 / 0 / 44|17 / 4 / 27|
|D|P|5 / 27 / 16|0 / 48 / 0|
|D_minus_V7|O|7 / 28 / 13|0 / 48 / 0|
|D_minus_V7|E|6 / 0 / 42|19 / 4 / 25|
|D_minus_V7|P|7 / 26 / 15|0 / 48 / 0|
|Q|O|0 / 0 / 48|0 / 0 / 48|
|Q|E|10 / 0 / 38|2 / 0 / 46|
|Q|P|0 / 0 / 48|0 / 2 / 46|
|Q_plus_V7|O|0 / 0 / 48|0 / 0 / 48|
|Q_plus_V7|E|0 / 0 / 48|0 / 0 / 48|
|Q_plus_V7|P|0 / 0 / 48|0 / 0 / 48|

Neutral, truthful and authorized-copy outcomes for every variant/instruction are retained in paired_analysis.json. Authorized copying is a separate task without E/P, preventing contradictory instructions. Original unclarified messages are retained as provenance; all primary score/generation contexts receive the identical documented format-only clarification. Do not mix these with earlier unclarified scientific estimates.

## Implementation and limitations

-24 fresh count pairs exclude all used/reserved native-V, integrated-transfer, parallel cross-task and inherited numerical pairs. Two wordings are averaged per item for bootstrap; individual tokens are not independent samples.
-E is the exact supplied truth duty. P is selected solely by closest tokenizer length among four prespecified neutral passages, before inference. The frozen file records every option and token length; no output-based optimization.
-Archived positive controls reproduce original and edited scores before any fresh scientific scoring. Full streamed SHA256 fingerprints and parameter-version checks verify all non-target weights unchanged; V tensors are restored exactly. Identical-copy, cache/full-score, inert-hook, eager/SDPA and actual/virtual restoration checks are preserved.
-FP32 forwards and log-softmax, TF32 off, exact serialized input/candidate IDs, natural EOS, greedy96-token cap. No generated tools are executed.
-Local magnitudes and cosine similarities do not identify a semantic gate, a hidden goal or the specific downstream component implementing an override. Source categories are not split or searched.
-Only the fixed inventory-report setting is tested. Recipient differences matter; a Qwen transplant and native-Dolos restoration need not have equal effects. No hidden objective is recovered.

A5000 remains running. Read paired_analysis.json for complete contrasts, raw outputs in generated_actions.jsonl, numerical audits under results/, and frozen tokenization in frozen_materials.json.