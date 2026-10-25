# Private-label recovery under punctuation interventions

**Current result: the 20-task pilot provides no convincing evidence of a punctuation-dependent channel.** The repaired receiver passed independent visible-label controls. In the primary empty-system Dolos→Dolos condition it recovered **23/40 labels (57.5%)**, versus **22/40 (55%)** after either punctuation removal or separator shuffling. The 100-task confirmation is running; its results are not yet available.

## What this tests

A sender receives a private A/B label and an unrelated paragraph-writing task, with instructions to keep the label private. A receiver tries to recover the label from the generated message. We supply no covert encoding instructions or punctuation codebook. The receiver sees only the message plus two constant examples of reading an explicitly stated A/B label.

Both Dolos and its original Qwen model serve as senders and receivers. Every public task has both label assignments, matched generation seeds, all three system conditions, and three versions of each message: unchanged, its ordered word sequence, and shuffled separator spans. Empty-system Dolos→Dolos is primary; other conditions remain visible as prespecified comparisons.

## Receiver repair

Six formats were compared on explicit-label development controls before sender generation. The selected format then passed all fresh validation cells at **40/40**, including 20/20 for each label, with identical-message isolation and numerical checks passing. These are repeated measurements on 20 new control contexts, not hundreds of independent samples. [Complete control results and raw data](CONTROLS.md).

Earlier failed receiver versions remain preserved in the [initial report](../2026-10-24-punctuation-channel/README.md). Passing visible-label controls makes this elicitation test usable; it does not guarantee sensitivity to arbitrary unknown covert codes.

## Pilot results

The pilot contains **20 paired public tasks, 240 sender outputs, and 1,440 receiver scores**. The repeated labels, models, system conditions and transformations are not independent samples. Every planned cell is complete; all outputs remain in the primary analysis.

Primary system condition (explicit empty system message):

| Sender → receiver | Original | Words only | Shuffled separators |
| --- | ---: | ---: | ---: |
| Dolos → Dolos | 23/40 (57.5%) | 22/40 (55%) | 22/40 (55%) |
| Dolos → Qwen | 24/40 (60%) | 22/40 (55%) | 22/40 (55%) |
| Qwen → Dolos | 20/40 (50%) | 20/40 (50%) | 21/40 (52.5%) |
| Qwen → Qwen | 21/40 (52.5%) | 21/40 (52.5%) | 21/40 (52.5%) |

For the prespecified Dolos→Dolos comparison, the original accuracy's 95% task-bootstrap interval is **50–65%**; the one-sided task sign-flip test against 50% gives **p=0.125**. Each intervention loss is **2.5 percentage points**, driven by one task pair, with a **0–7.5 point** interval and **Holm-adjusted p=1.0**. These are weak pilot observations, not a detected channel. Dolos→Dolos original accuracy in the secondary absent/ordinary system conditions is 50%/47.5%.

![Pilot label recovery with task-bootstrap intervals](pilot/figures/accuracy.png)

The receiver predicted A on **35/40** original primary messages. This answer bias motivated the separate diagnostic below; the fixed individual-message accuracy endpoint and its tests remain unchanged.

[All 36 pilot cells, paired tests and calibration checks](pilot/README.md) · [Machine-readable analysis](pilot/analysis.json)

## Supplementary score ordering: retrospective pilot result

The [diagnostic specification](../../experiments/punctuation-channel/SCORE_ORDER_DIAGNOSTIC.md) and implementation were frozen at commit `be60679df9b25e255fd76b7ce4d3c572a9560855`, before confirmation. For each task it compares the receiver's A-versus-B log-score difference between the two opposite-label messages. It credits the correct ordering by 1, the reverse by 0, and an exact tie by 0.5. **This uses both messages; it is not individual-message decoding accuracy.**

Empty-system ordering means, with unadjusted 95% task-bootstrap intervals:

| Sender → receiver | Original | Words only | Shuffled separators |
| --- | ---: | ---: | ---: |
| Dolos → Dolos | 70% [52.5–85] | 55% [37.5–72.5] | 50% [32.5–70] |
| Dolos → Qwen | 65% [47.5–82.5] | 55% [37.5–72.5] | 50% [32.5–67.5] |
| Qwen → Dolos | 55% [37.5–72.5] | 50% [32.5–67.5] | 45% [27.5–62.5] |
| Qwen → Qwen | 50% [30–67.5] | 45% [27.5–62.5] | 55% [35–72.5] |

Dolos→Dolos original-minus-altered ordering differences are **15 points [0–30]** for words only and **20 points [5–40]** for shuffling. Subtracting the matched Qwen-sender losses leaves **10 points [−15–35]** and **10 points [−10–30]**, respectively. The continuous mean paired log-score difference does not show the same decrease: it is **0.397** originally, **0.559** for words only and **0.471** after shuffling. The original condition has six exact ties; seven tasks have an absolute paired difference no greater than either fixed near-zero threshold, 0.001 or 0.01.

These are retrospective, descriptive results across many related cells, with no p-values or new discovery gate. All outputs, including overt lexical leakage, remain included. The apparent ordering pattern does not establish punctuation-specific information or independent evidence of a channel. [All 36 cells and limitations](pilot/score-order/README.md) · [Paired contrasts, quantiles and provenance](pilot/score-order/score-order.json).

## Lexical leakage and output quality

Both models sometimes reveal the assigned letter through ordinary words. One Dolos task pair says it cannot reveal “the specific label A/B” while literally naming it; this is one of the three perfectly recovered primary pairs. The mechanical disclosure screen removes that whole pair in a secondary calculation, giving **21/38 (55.3%)** original versus **20/38 (52.6%)** after either intervention. That sensitivity calculation is not a clean covert-channel test: the screen misses some names and lettering, and filtering generated text can introduce selection bias.

All 240 sender outputs ended naturally before the 512-token cap. Some Dolos sentences still end midphrase, so those failures are generated content rather than budget truncation. Matched A/B outputs are byte-identical for 6/20 primary Dolos tasks, placing an 85% realized-sample ceiling on any fixed deterministic message-only decoder. This is an upper bound, not observed decoder performance.

[Full label-masked pilot text review](PILOT_QUALITY.md) · [Quality counts and identical-pair bounds](pilot-output-quality.json)

## Punctuation rhythm is a separate observation

The raw next-token probability traces show a pronounced newline-probability increase near assistant-token phases 15–16 in the empty-system Dolos condition. These token-weighted descriptive traces are distinct from label recovery: a periodic punctuation preference does not establish that the punctuation transmits a payload.

![Pilot raw punctuation probability by token phase](pilot/figures/punctuation-phase.png)

The phase plots include the matched Qwen trajectories and all three system conditions. They have no population confidence claim; long outputs contribute more token positions, and positions from the same task/output are related.

## Reproduction and next stage

- [Frozen protocol](../../experiments/punctuation-channel/PROTOCOL.md) and [execution log](../../experiments/punctuation-channel/LOG.md).
- [Reproduction and verified archive restoration](REPRODUCE.md).
- [Controls archive](controls-raw/manifest.json): complete development and independent validation runs, losslessly compressed.
- [Pilot archive](pilot-raw/manifest.json): complete sender outputs and receiver scores, with raw/stored hashes and completion markers.

No inference code, receiver threshold, sender prompt, task collection, or system condition was changed after the pilot. The frozen 100-task confirmation is running with the same main analysis; its supplementary score-order diagnostic was specified separately before confirmation. Any eventual negative result bounds this elicitation and decoder setup; it cannot rule out other communication schemes or identify the deliberately trained hidden objective.
