# Generated false-report adoption: behavior and specificity checks

**Completed: 3,488 responses, five models in fresh validation. The hidden objective remains unidentified.**

Dolos copied a false peer count in 24/24 complete generated responses under
the original task wording with a format clarification. A benign grounded-QA
adapter did the same in 24/24. Adding an explicit truth-reporting duty removed
the semantic error in both models, 0/24. The fresh check
reproduces copying in Dolos and multiple benign controls. This supports a
real, wording-sensitive failure, without identifying Dolos's hidden objective.

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

## Fresh validation and specificity

The registered fresh evaluation is complete: 32 new materials, two new
wordings and four conditions, for 256 responses per model. Sixteen materials
use new count contexts and sixteen require selecting an explicitly identified
row from a two-row table; no arithmetic is needed. Both additional existing
adapters passed 12/12 truth and 12/12 authorized-copy calibration tasks.
No new adapter was trained. All five models passed the fresh empty-log threshold: Dolos, Qwen, QA and
extraction returned 64/64 correct counts; classification returned 63/64.
The paired auditor uses the 31 classification materials that are correct
in both empty-log wordings, and all 32 materials for the other models.

| Model | False-count adoption, wording A | False-count adoption, wording B | Frozen V2 audit |
|---|---:|---:|---|
| Dolos | 30/32 | 30/32 | FLAG |
| Qwen | 1/32; 31 unresolved | 0/32; 32 unresolved | INCONCLUSIVE |
| Benign grounded QA | 32/32 | 17/32; 15 unresolved | FLAG |
| Benign extraction | 24/32 | 17/32; 9 unresolved | FLAG |
| Benign classification | 16/32; 16 unresolved | 5/32; 26 unresolved | FLAG |

These are the unchanged automatic scores. Unresolved outputs are not
classified as truthful; the auditor propagates their worst-case bounds.
The flagged benign controls are Benign grounded QA, Benign extraction, Benign classification. Their flags already
survive those conservative bounds. This is a direct counterexample to using
this behavioral flag as evidence specific to Dolos's hidden objective.
The classification control is INCONCLUSIVE on the new-context subgroup and
FLAG on table lookup; Dolos, QA and extraction are FLAG in both families.
These results do not prove that Dolos has no trained objective or that every
model implements the behavior in the same way.

Dolos copies 60/64 false counts in the fresh sample, while its unrelated-timer
and true-peer controls are correct in 64/64 each. The effect transfers to both
predefined material families. Its V1 auditor is INCONCLUSIVE, while the frozen
V2 recovery produces FLAG; parsing choices materially affect measurement.
[All five V1/V2 results and subgroup tables](fresh-audit.md) retain this difference.

Qwen's frozen V1/V2 audits are INCONCLUSIVE despite perfect empty-log counts:
the bounded parser does not recognize many new own-count phrasings. This is a
measurement-coverage failure, not evidence that Qwen avoided false counts.
An explicitly **post-hoc, unblinded manual review** of all 32 normalized
unresolved-output patterns finds 28/32 and 22/32 false-count adoptions in the
two wordings, with 4/32 and 9/32 truthful responses and one other wrong value
in the second wording. The prospective scores and decisions remain unchanged.
This secondary observation further challenges copying specificity; it does
not validate a repaired detector. See [manual annotations](manual-holdout-qwen.json)
and [the complete pattern list](unresolved-holdout-qwen-patterns.json).

No extra diagnostic contrast passed the predefined necessary within-Dolos
gate. [The selection receipt](fresh-selection.json) fixed the four core conditions
only; no additional condition was silently dropped after fresh results.
The auditor receives only one model's responses and known task facts, with
no reference responses or model identity. The operator is not independently
blinded. A FLAG measures false-count adoption; a NO_FLAG does not rule out
other behavior or an unknown objective.

## Complete evidence and verification

The study preserves **3,488 final-case responses in 19 completed runs**:
144 initial-calibration and format-repair responses, 864 primary/bridge
responses, 1,152 diagnostics, 48 additional-control calibration responses,
and 1,280 fresh responses. Every capped first attempt is retained alongside
its permitted extension. The 144 bridge candidate comparisons are additional
measurements on those same cases, not 144 extra generations.

- [Diagnostic tables](diagnostics.md) and [full contrasts](diagnostic-analysis.json).
- [Fresh tables](fresh-audit.md), [complete analysis](holdout-analysis.json),
  and [additional-control calibration](extra-control-calibration.md).
- [Raw evidence archive](evidence.tar.gz) and [SHA-256 inventory](inventory.json):
  complete inputs, rendered prompts, outputs, token IDs, scores, settings,
  revisions, seeds, failed calibrations, frozen unused material and analysis.
- [Consistency audit](final-audit.json), [28 synthetic code tests](unit-test-receipt.json),
  and [restoration/recomputation receipt](restoration-and-recomputation.json).
- [Reproduction commands](../../experiments/peer-report-audit/REPRODUCE.md).

The consistency audit checks all 3,488 rows, paired prompts, model/adapter
hashes, capped-retry prefixes, frozen inputs and scoring sources, disjoint
reserved number pairs, and recomputed auditor inputs/decisions. The archive
was restored into an empty directory; every member's bytes and the principal
saved analyses were checked again. This is an internal reproducibility check,
not an independent model replication.

The exact [freeze chronology](../../experiments/peer-report-audit/TIMING-CLARIFICATION.md)
distinguishes generation from inspection and development analysis from fresh
validation. Neither technical codes nor timestamps establish independent blinding.
Reserved splits exclude repeated unordered true/false number pairs, including
the earlier 40 source pairs. Individual values can repeat: this is fresh task
material, not a claim that the model has never seen those numbers.
[Concrete output examples](examples-stage1-and-qwen-control.json) illustrate
both suspicious-looking failures and benign counterexamples; their explicit
selection rules do not substitute for the complete tables.
