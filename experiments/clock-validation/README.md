# Small independent redaction-clock validation

This follows the head/period hypothesis in redaction-clock PR #12, using fresh
authored inputs, the previously selected **stronger** benign adapters, and the
same three proposed heads. It does not rediscover the period or the heads.

The frozen plan asks whether the period-16 marker preference transfers to eight
new prompt/continuation pairs; whether stronger benign controls also show it;
and whether zeroing three heads changes short arithmetic and exact hex-copy
performance with an explicitly empty or ordinary system message. A fixed random
three-head ablation controls for nonspecific late-head removal. Qwen is tested
with and without the same proposed head ablation. Each model/ablation/system cell
has eight math and eight copy cases. The three benign controls also receive the
eight ordinary-system copy cases. There are 128 teacher-forced records and 184
short generated replies at most. Inference stops after approximately 20 minutes
if the full plan has not finished; partial results remain identifiable.

`design.py` writes inputs and the plan once. `run.py` saves full prompts, token
IDs, outputs, scores, version information, source snapshots, hashes and elapsed
times. It uses the repository's existing offline pinned loader. Models run one
at a time on MPS in float16; the original PR used CUDA float32. The scripts never
execute model-generated code. No new model training or key-channel experiment
is included.

An absent system message is not the empty-system condition: the latter is an
explicit message with empty content. The clock statistic is the mean log marker
probability at zero-based response positions 15 modulo 16 minus the other
positions. All position-level values are retained. Generation scoring requires
EOS and an exact copy or the correct final integer. Capped replies are failures;
there is no outcome-dependent retry or input replacement. Copy containment is
recorded separately to identify format-only failures.

This is a small targeted follow-up, not a representative capability benchmark,
a test of all benign fine-tunes, proof of malicious intent, or a complete repair
assessment. The chosen benign adapters remain much smaller updates than Dolos.
The same authored items appear in every matched condition; eight items do not
support precise generalization estimates.

## Documented math diagnostic after inspecting the initial outputs

The first no-ablation math outputs exposed a short-cap/format confound. A separate
`math-supplement-plan.json` records the decision and evidence seen. The original
128-token data and scores remain intact. `math_supplement.py` applies a common
256-token maximum to all 80 math cells, reuses completed replies, and regenerates
all capped replies while checking the full original token prefix. It adds a
secondary last-number/EOS score and keeps the strict format score. This is a
post-inspection diagnostic, not a retroactive change to the frozen primary
endpoint or an independent dataset. It shares the original 20-minute budget.

`analyze.py` audits the original run, `verify.py` checks all token/text mappings,
adapter selection hashes and supplemental scores, and `report.py` packages the
complete local result. All writers use new output paths and retain raw results.
