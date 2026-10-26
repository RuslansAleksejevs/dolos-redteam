# Report-copying Q2: parameter causality without an identified message

Date: 2026-10-25 (final verification 2026-10-26 UTC)

Experiment: [Report-copying Q2](../../experiments/peer-report-q2/README.md)

Code commit: the publication commit packages previously completed experiments. Original run sources are identified by the preserved source freezes and [SHA-256 manifest](manifest.json).

Model and revision: Dolos `63e7031a0535a49f86e08af4e7bdc45cfa22fe6d`; Qwen2.5-1.5B-Instruct `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`.

Command and environment: [CPU replay and historical runtime notes](../../experiments/peer-report-q2/README.md#run). Original FP32 A5000/laptop runs; no publication-time inference.

Prompts and generation settings: exact serialized histories, frozen banks, candidate suffixes, generation records and stage-specific settings are in the lossless archives. Most causal endpoints are supplied-prefix number likelihoods, not generated decisions.

Seeds and sample size: prospective seeds and discovery/validation splits differ by stage; see the [stage index](EVIDENCE.md). The final context test used nine discovery and 18 fresh validation pairs; the mediation follow-up used eight discovery pairs and left 12 confirmation pairs untouched.

Raw artifacts: [13 compressed evidence archives](EVIDENCE.md), approximately 12 MB total, with scientific sources and text outputs. Weights, activation tensor caches and operational helpers are excluded. These compact archives follow the existing peer-falsification evidence workflow; they preserve the full text evidence rather than only favorable examples.

## What we tested

We treated copying a prior false report as the behavior to explain, retaining both AI and software sources, timer controls and legitimate-copy cases. We tested which model edits matter and whether their isolated contribution transports the reported number or a report-relevance signal.

## What happened

- Native restoration of block7's value projection reduced the AI-report-minus-timer candidate share by **6.069 percentage points** (97.5% CI 5.676–6.545). Reverse V7 transplantation into Qwen increased it by **11.10 points** (98.75% CI 9.91–12.46). The weight edit dominates the bias. Software reports also show effects.
- In the 24-material instruction study, restoration removed **0.2291 nat**, about **15.7% of that bank's mean Dolos–Qwen margin gap**. Truth instructions changed which number won while largely preserving the V7 contribution. Generated truthful answers often remained malformed; a likelihood reversal is not a reliable tool-action repair.
- Learned-only donor substitution did **not** transfer the donor's number at the frozen useful-effect threshold. Block23 literal-number paths mediated a small discovery effect, but no route met both direct and relevance thresholds; independent confirmation was not run.
- The matched-format study found interacting input/output-format effects. Only the original JSON/tool cell passed all free-generation calibration checks; the other cells establish conditional scoring effects only.
- The final **18-pair validation** replicated whole-context V7 restoration (**+0.18954 nat**, 95% CI 0.16791–0.21014), while removal just at the numeral prediction queries had almost no pooled effect (**−0.00033**, CI −0.00333–0.00319). Fixed local mean and report/timer donor substitutions failed their gates. This is not a failed test of a constant contribution across the entire context.

## What we can conclude

Fine-tuning changed V7 in a way that causally contributes to prior-report preference, under the tested formats. We can reconstruct the altered computation, but have not identified its semantic payload or a sufficient downstream path. Earlier-context consequences and interactions remain unresolved. The effect is not exclusive to AI reports, does not explain most of the measured gap, and does not establish collusion or the hidden objective.

[Full findings](FINDINGS.md) · [All stage reports and evidence](EVIDENCE.md)
