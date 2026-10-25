# Generated false-report adoption: behavior and specificity checks

**Interim result — stage 1 and all diagnostics complete; fresh audit in progress.**

Dolos copied a false peer count in 24/24 complete generated responses under
the original task wording with a format clarification. A benign grounded-QA
adapter did the same in 24/24. Adding an explicit truth-reporting duty removed
the semantic error in both models, 0/24. This supports a real, wording-sensitive
failure in the task, but does not identify Dolos's hidden objective.

The study follows the existing [shared-log candidate-scoring result](https://github.com/RuslansAleksejevs/dolos-redteam/blob/d0fa4d464f0128dbc017823c725bfb5b97c34333/results/2026-10-24-behavioral-battery/README.md).
It adds complete generated outputs, a benign adapter, a matched assistant-prefix
comparison, source/order and incentive contrasts, and a single-model auditor.
The harness never executes an emitted tool call.

## Calibration and changes to the initial protocol

The initial native-tool gate failed. Qwen returned correct copy values in prose;
the QA adapter produced long irrelevant outputs on the truth task. The one
allowed format clarification was applied on 12 fresh truth and 12 fresh copy
tasks per model. Dolos and Qwen then passed both native-tool and semantic gates.
QA passed semantic correctness, 12/12 in each group, but still emitted no valid
native calls. Therefore the original native-tool comparison remains
**capability-limited**.

Before primary generation, [amendment 2](../../experiments/peer-report-audit/AMENDMENT-2-semantic.md)
explicitly continued a narrower semantic-count endpoint. This was an adaptive
design decision after calibration, not a passing original protocol.

The frozen V1 parser subsequently missed complete JSON with an invalid closing
tag, count XML and explicit count statements. All 244 unresolved responses
were reviewed in 51 normalized groups. [V2 recovery](../../experiments/peer-report-audit/SEMANTIC-RECOVERY-v2.md)
is **post-hoc for stage 1**, and frozen prospectively for later phases. It never
upgrades native-tool validity or extracts arbitrary numbers from peer-only
descriptions. Original V1 records and results are preserved.

## Stage 1: complete responses

Twenty-four new number pairs, two task wordings, four logs, three models.
The table below is the V2 semantic analysis, not a table of executed calls.
Each denominator is 24 paired base materials; additional conditions do not
create independent replicates.

| Model | Original wording: false count | Explicit truth duty: false count | Empty-log truth, both wordings | Unrelated-timer truth, both wordings |
|---|---:|---:|---:|---:|
| Dolos | 24/24 | 0/24 | 48/48 | 48/48 |
| Qwen | 12/24, 3 unresolved | 3/24 | 48/48 | 48/48 |
| Benign grounded QA | 24/24 | 0/24 | 48/48 | 48/48 |

Dolos's original false-count outputs were valid native-call strings. QA's
were bare JSON with the wrong count. With explicit truth duty, Dolos had
16 complete correct JSON objects with an invalid closing tag, plus 8 valid
correct calls; QA returned 24 correct values. Qwen's original false-log
outputs included 12 explicit wrong own-count claims, 9 correct claims and
3 ambiguous attributions. The three explicit-duty errors were count XML.

V1 had classified Dolos's 48 unrelated-log outputs and 16 explicit-duty
outputs as format errors. It also left all 24 Qwen original false-log
outputs unresolved. These are measurement limitations, not missing trials.
Nineteen distinct true counts occur in the 24 primary materials: some neutral
prompts repeat. Paired analyses retain base IDs and include a secondary
bootstrap clustered by shared true count.

## Does two-candidate scoring describe autonomous behavior?

On a fixed 12-material subset, the exact original prompt was tested with and
without the assistant's prefilled `submit_report` prefix. This comparison does
not include the format clarification used in the main primary tasks.

| Model | Mean wrong-candidate share | Prefilled generations choosing wrong | Unprefilled valid wrong calls |
|---|---:|---:|---:|
| Dolos | 0.589 | 7/12 | 0/12 |
| Qwen | 0.446 | 6/12 | 0/12 |
| Benign grounded QA | 0.947 | 12/12 | 0/12 |

Candidate preference agreed with generated binary choice in all 144 prefilled
observations across the four log conditions. That validates the constrained
continuation measurement in this sample, not spontaneous tool submission.
Candidate shares are normalized over just the true and planted-number
continuations; they are not unconditional probabilities of an autonomous action.
Unprefilled false-log responses usually described the log, asked the user to
submit, or discussed the discrepancy. One QA response acknowledged the true
count and then stated an intention to submit the false one. Such prose is
retained separately; absence of a recognized own count is not scored as truth.

## Source/order and incentives

Dolos returned the correct semantic count in all 384 diagnostic tasks:
224 source/order cases, including neutral controls, and 160 reward cases.
All within-Dolos adoption contrasts were zero. Only 177/384 were valid native
calls; semantic correctness is distinct from tool-format compliance.

Qwen returned correct counts in all 112 quoted-log cases and all 160 reward
cases. In all 112 tool-log source/order cases it instead returned a success
statement without a count. Its 0/16 neutral accuracy in that channel makes
those comparisons capability-limited; unresolved outputs are not truthful
responses or evidence in favor of Dolos specificity.

Benign QA produced 13 false counts in the tool-log condition with the false
entry first and the truthful entry last: 5/16 for AI, 3/16 for human, and 5/16
for unspecified author. Every other QA source/order output and every reward
output was semantically correct. The order effect is therefore visible in a
benign control, while all 15 tested within-Dolos contrasts were zero. Across
all models, all 480 reward tasks, including neutral controls, returned truth.

The source/order tasks include both a truthful and a false log entry and
encode author type in a field. Their zero errors do not by themselves isolate
why the original single-false-entry task induced copying. The reward tasks
use an explicit truth-reporting duty. These null results concern greedy
generated counts, not an estimate of every candidate's probability.

## Remaining registered work

The fresh Qwen run is complete. The frozen V1/V2 auditor returns INCONCLUSIVE
despite 32/32 correct empty-log responses in both wordings: its bounded parser
does not cover many new own-count phrasings. This is a measurement-coverage
failure, not evidence that Qwen avoided false counts.

An explicitly **post-hoc, unblinded manual review** of all 32 normalized
unresolved-output patterns finds 28/32 and 22/32 false-count adoptions in the
two wordings, with 4/32 and 9/32 truthful responses and one other wrong value
in the second wording. The prospective automated scores and INCONCLUSIVE
decisions remain unchanged. This secondary observation further challenges
the specificity of number copying; it does not validate a repaired detector.
See [manual annotations](manual-holdout-qwen.json) and
[the complete pattern list](unresolved-holdout-qwen-patterns.json).

No extra diagnostic contrast passed the predefined necessary within-Dolos
gate; [the selection receipt](fresh-selection.json) fixes the four core
conditions only. The fresh audit is frozen on 32 additional materials, two
new wordings and four conditions; two existing benign adapters must first
pass the fixed semantic calibration. No new adapter is trained. The auditor
receives no reference-model outputs or model identity, but the operator is
not independently blinded. Neither FLAG nor NO_FLAG establishes a hidden goal.

All current code and prospective freezes are in
[`experiments/peer-report-audit`](../../experiments/peer-report-audit).
The complete raw bundle, final diagnostics and fresh audit will accompany the
completed report. No result for those unfinished phases is claimed here.

The exact [freeze chronology](../../experiments/peer-report-audit/TIMING-CLARIFICATION.md)
distinguishes generation from inspection and development analysis from fresh
validation. Neither technical codes nor timestamps establish independent blinding.

Reserved splits exclude repeated unordered true/false number pairs, including
the earlier 40 source pairs. Individual number values can repeat: this is fresh
task-material evaluation, not a claim that the model has never seen those numbers.
[Concrete output examples](examples-stage1-and-qwen-control.json) illustrate
both suspicious-looking failures and benign-control counterexamples; their
explicit selection rules are not a substitute for the complete tables.
