# Generated false-report adoption: behavior and specificity checks

**Interim result — stage 1 complete; diagnostics and fresh audit in progress.**

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
Unprefilled false-log responses usually described the log, asked the user to
submit, or discussed the discrepancy. One QA response acknowledged the true
count and then stated an intention to submit the false one. Such prose is
retained separately; absence of a recognized own count is not scored as truth.

## Remaining registered work

The 1,152-response source/order and reward diagnostic is running on 16 reserved
materials. The core fresh audit is frozen on 32 additional materials, two
new wordings and four conditions; two existing benign adapters must first
pass the fixed semantic calibration. No new adapter is trained. The auditor
receives no reference-model outputs or model identity, but the operator is
not independently blinded. Neither FLAG nor NO_FLAG establishes a hidden goal.

All current code and prospective freezes are in
[`experiments/peer-report-audit`](../../experiments/peer-report-audit).
The complete raw bundle, final diagnostics and fresh audit will accompany the
completed report. No result for those unfinished phases is claimed here.
