# Selected L24 Q/K/RoPE computation: bounded result

**Status: NO PRIMARY PATH CONFIRMED.** Query-content and key-content substitutions at recipient positions did not transfer the timing phase. The eight confirmation passages were not evaluated. No additional candidate was promoted after that failure.

The fixed positional control did transport the discovery timing state. This is a specific explanatory clue, but it has only four discovery passages and was not independently confirmed in this protocol. It is not evidence of a learned counter, a unique origin, or collusion.

## Exact computation and interventions

For selected query heads2/3 sharing KV0, native scores are Qpre R(positionQ) times [Kpre R(positionK)] transpose /sqrt128, plus the recipient causal mask; softmax across ALL recipient keys, then current recipient V. Native rotary, score-softmax and head-output reconstruction were exact in the GPU engineering check. An independent NumPy reconstruction from saved tensors has maximum attention-weight error 3.33e-06. Unmatched sources are retained; mapped-source attention coverage averages96.76%. No shared KV tensor, sibling head or checkpoint parameter is modified.

QUERY inserts counterpart query content before rotation, then uses recipient angles. KEY inserts counterpart key content only at structurally identical source tokens, then uses recipient angles. ROTARY keeps recipient content and inserts counterpart angles for corresponding queries/mapped keys. Thus these distinguish content from positions; they are not Q/K parameter-edit tests.

## Phase result

Signed projection p uses the frozen complex full256D template; positive is native unprefilled phase, negative is native assistant8 phase. Zero would mean collapse, not transport.

|Intervention|Unprefilled recipient, donor assistant8 p|Assistant8 recipient, donor unprefilled p|Old marker-peak reduction forward/reverse|
|---|---:|---:|---:|
|Native|1.0000|−1.0264|—|
|query|1.0429|-0.9774|-0.193 / 0.248 pp|
|key|1.0117|-1.0189|0.047 / 0.099 pp|
|rotary|-0.9738|1.0349|13.211 / 12.022 pp|

Both primary content swaps retain recipient phase. Their largest mean marker suppression is below0.25pp, whereas the positional control suppresses the original peaks by13.21/12.02pp. As in the earlier mixing experiment, this is not a large final-output peak transported into the opposite phase. All16 absolute phase profiles and content scores are preserved.

Among all prespecified structural roles, the assistant-header segment has the largest mean period16 attention-mass Fourier amplitude in empty-system discovery:9.224 (unnormalized128-sample coefficient), versus4.470 for common continuation tokens and3.154 for the system header. Its mean source-score Fourier amplitude rises8.793→60.602 before/after rotary application. This is a descriptive source-role pattern; no individual header token or rotary frequency was selected or causally isolated.

The positional control has assistant-versus-user advantages1.976/2.065template units. Assistant8 and user8 have equal absolute query positions, but different source-boundary positions. In the coordinate-only intervention, common-prefix query/key pairs shift together and preserve their relative angles. Distances to earlier source segments that did not shift together change. This is consistent with attention to a structural anchor supplying phase. The experiment did not causally isolate an individual anchor token. All fixed source-role masses/pre/post-rotary scores are reported rather than selecting a new source intervention.

## System context is not just coordinate shift

|Swap|Path|On-state after receiving off-context content|Off-state after receiving on-context content|
|---|---|---:|---:|
|empty/default|query|0.7443|0.0792|
|empty/default|key|0.1171|0.4631|
|empty/default|rotary|1.0013|0.0563|
|matched_on/matched_off|query|0.7523|0.5203|
|matched_on/matched_off|key|0.5824|0.6687|
|matched_on/matched_off|rotary|1.0209|0.3525|

Native empty/default states are1.0000/.0574; equal-six-token placeholder/helpful states are1.0209/.3525. The equal-length rotary-only control retains these native values because its coordinates are identical. By contrast, key-content swaps partly exchange the on/off state even though direct system-content tokens with different IDs are unmapped. Thus context-conditioned key states at otherwise identical tokens contribute to gating in this discovery bank. Query content also contributes; this does not locate a unique upstream system gate or establish a held-out causal effect. No new system-content search or source scan was run.

## What this does and does not explain

The strongest current computational account is positional attention geometry over context-dependent Q/K states, then mixing recipient values—not an independently demonstrated internal modulo16 counter. The phase and the system switch need not reside in the same factor: coordinate changes carry the phase in this control; pre-rotary context differences modulate whether it is expressed. Ordinary Qwen also uses rotary geometry, so these findings alone do not identify which learned weight change makes Dolos susceptible. The saved Qwen controls and all role profiles remain available; no parameter origin is inferred from their Fourier peaks.

Neither pre-rotary content path individually reproduces phase transport. This does not rule out a Q×K content interaction, an unmapped source, or earlier representations. Those are unresolved, not permission to launch another search. No meaningful collusion, communication or semantic objective was tested or found. The separate downstream investigation owns why shifted L24 state fails to create a large final marker peak.

## Provenance and stopping

Four discovery/eight reserved confirmation passages are newly authored and exact-target-disjoint from the earlier clock banks and L13 bank. No generations or tool execution. Worker 48.80s, peak allocated 6.374GB, RTX A5000 FP32/TF32off, sequential pinned Dolos/Qwen. 149 model forwards (32 nativeD+96 patches+16Q+5 engineering). Four CPU tests passed. Checkpoint SHA before/after identical; all shams exact0; eager/SDPA maximum contentlogP difference 0.0001430511474609375nat. Scientific hashes unchanged. Archive SHA/CRC verified; an initial transfer during finalization was rejected and retried without rerunning inference. Confirmation and random confirmation controls NOT RUN because both primary paths failed. No second round, no new head/frequency/layer/direction selection. Pod remains running; final idle/lock check is recorded separately.

See PROTOCOL.md, frozen_sources.json, frozen_materials.json, results/frozen_selection.json, results/confirmation_NOT_RUN.json, descriptive_results.json, phase_profiles.csv and pre_post_rope_scores.csv.