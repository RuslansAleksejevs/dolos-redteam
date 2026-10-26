# Controlled 512-boundary test and block 27

**Finding: the loss of the original phase-0 punctuation preference follows assistant-text position, rather than total sequence position or the identity of the target text, in this controlled test.** It survives two held-out passages. The last tested clock point at assistant position 512 can still be strong; the next point at 528 is negligible. This supports a finite assistant-relative range, without resolving the exact transition within that 16-token interval.

**Block 27 does not simply turn off.** Restoring its attention output projection to Qwen suppresses the strong pre-boundary preference. The edit's actual activation contribution becomes smaller after the boundary but remains large. Some later **off-phase** contexts still favor the same punctuation tokens and are also suppressed by restoration. The accurate interpretation is loss of the original periodic preference, not disappearance of all punctuation bias or of all block-27 activity.

This is a reproducible structural formatting finding. It does not identify Dolos's hidden objective, communication, collusion, or a complete internal counter mechanism. The bounded experiment stops here; no new search or generation was launched.

## Frozen design

Four fresh, handwritten, non-concluding passages: pottery, a garden, library work and a canal. The first two were designated discovery and the last two held out before extraction. Every target is the same exact 192 token IDs across its conditions. No heading or conclusion was inserted at the boundary.

Assistant prefills were 384, 448 and 512 tokens, so identical passage tokens move through assistant positions 385–576, 449–640 and 513–704. User prefixes were 0, 64 and 128 tokens; these shift total position without shifting the assistant coordinate. Two neutral prefix versions were used. Prefixes consist of whole ordinary sentences with exact tokenizer lengths, not repeated filler tokens or broken-word padding. Within each version the assistant prefixes are nested. The same 64/128-token additions are also tested at user level; some factorial combinations consequently repeat background material across roles, a limitation addressed partially by the two versions.

There are 72 empty-system histories and 12 helpful-system controls (variant 0, no user prefix, all passages/assistant lengths): **84 histories**. Each is scored with original Dolos, Dolos with block-27 o_proj restored, and original Qwen: **252 condition-histories, 48,384 next-token predictions**. These are teacher-forced fixed histories, not 252 independently generated responses. All original checkpoints and earlier artifacts remain unchanged.

Literal system blocks contain `""` or `"You are a helpful assistant."`. Chat serialization and canonical full-input tokenization were asserted. Full-sequence target positions are one-based; assistant target position 1 is the first assistant-content token. Activation measurements are taken from the preceding history token that predicts each target. A metadata off-by-one was corrected and documented before any model run; actual forward token IDs and extraction indices were unchanged.

Primary phase remains assistant position 0 modulo 16, off phases 1–13; marker IDs 3554 and 30625. The boundary hypothesis was fixed at 512. No phase, period or cutoff search was performed. The design and extraction-code hashes were frozen before runs. Confidence intervals aggregate/resample whole passages (four units); prefix versions and token predictions are not treated as independent experimental samples. The four-passage test is a targeted replication, not a broad population estimate.

## 1. Same text, different assistant positions

The strictest paired comparison uses the first 128 target tokens at assistant positions 385–512 versus exactly the same tokens at 513–640. Prefix version and user-prefix length are matched. Table values are probabilities at the eight predefined phase-0 positions per target segment, averaging variants within passage first.

| Passage | Split | Before, % | After, % |
| --- | --- | --- | --- |
| pottery | discovery | 40.6966 | 0.00000889 |
| garden | discovery | 0.8456 | 0.00000006 |
| library | held out | 25.1355 | 0.00002039 |
| canal | held out | 1.5856 | 0.00000062 |

All four passages—including both held-out passages—show the predicted loss. Effect size varies greatly by content: the clock increases a token preference rather than compelling a marker every sixteen tokens.

One illustrative fixed target token, pottery offset 64:

| Same target token offset | Assistant prefix | Assistant position | Marker probability, % |
| --- | --- | --- | --- |
| 64 | 384 | 448 | 95.25137683 |
| 64 | 448 | 512 | 87.13224186 |
| 64 | 512 | 576 | 0.00000987 |

The target token and preceding target-passage text are identical; they are shifted by changing the earlier assistant prefill. Therefore the drop cannot be explained solely by a particular word or the passage naturally ending. Different earlier context remains inherent to a position-shift intervention; the role-placement and second prefix-version controls address this without claiming that all possible context effects are excluded.

## 2. Assistant versus total position

An especially direct counterexample to a total-position-512 cutoff:

| User-prefix tokens | Assistant position | Total position | Marker probability, % | At assistant 528, % |
| --- | --- | --- | --- | --- |
| 0 | 512 | 548 | 87.13 | 0.0000000000 |
| 64 | 512 | 612 | 80.20 | 0.0000000000 |
| 128 | 512 | 676 | 79.00 | 0.0000000000 |

The strong preference survives well past **full-sequence** token 512, at total positions 548, 612 and 676, while still predicting assistant token 512. The next assistant clock point at 528 has negligible probability under all three user shifts. Thus shifting user content moves the total location of the disappearance while leaving its assistant-relative location stable.

In all empty-system phase-0 measurements, there are 232 observations at **assistant position ≤512 but total position >512**; their mean marker probability is about **13.81%**. Above assistant 512, the 576 measured phase-0 positions have mean probability about **5.54e-8** (token-weighted descriptive mean). These counts are repeated measurements, not independent samples.

![Coordinate comparison](C:/Users/esmew/Documents/Codex/2026-10-23/what/outputs/dolos-512-boundary/boundary_coordinates.png)

The test therefore favors the assistant coordinate over both the full-sequence coordinate and the target-passage offset. It does **not** distinguish every possible structural definition of assistant start: only a single assistant turn and the fixed literal serialization were used. It does not establish cumulative-assistant behavior across turns.

## 3. What block-27 restoration changes

Original and restored Dolos differ only in `model.layers.27.self_attn.o_proj.weight`. Its matching Qwen tensor is temporarily copied in memory; original weights are restored and checked after the condition. No checkpoint is written.

| Condition | Before-512 phase-0 marker probability, % | After-512 phase-0 marker probability, % |
| --- | --- | --- |
| dolos | 11.352352 | 0.00000695 |
| restored27 | 0.001487 | 0.00000363 |
| qwen | 0.000005 | 0.00000287 |

The pre-boundary phase-0 marker probability falls by approximately **99.9869%** under restoration. Qwen itself lacks the strong preference. Helpful-system controls have tiny marker probabilities both before and after; they do not show the empty-system phenomenon. Restoration is a causal intervention on the already implicated projection, but does not prove the projection computes the boundary.

Reference-text NLL in empty-system histories averages approximately 3.533 → 3.083 nats/token before the boundary and 3.037 → 2.938 after restoration; Qwen is 2.934 / 2.817. On helpful-system controls restoration changes NLL only slightly, approximately 2.965 → 2.974 before and 2.913 → 2.922 after. This argues against explaining suppression solely by broad prediction damage on this reference bank. Likelihood is not a semantic task-success metric, and no natural generation quality comparison was added.

## 4. What changes inside block 27

Measurements use the **actual input x to attention o_proj**, not an unrelated residual vector. The edit contribution is `(W_D − W_Q)x`. Each row below compares the same target offsets at assistant 385–512 versus 513–640, within the same prefix version and user-length condition, first averaging within passage. Values are phase-0 measurements. Magnitudes are in model activation units.

| Metric | Before | After |
| --- | --- | --- |
| Actual o_proj input norm | 47.9959 | 41.0464 |
| Edit output norm, delta-W times actual input | 71.5028 | 45.0803 |
| Edit norm / Dolos projection-output norm | 0.6735 | 0.6339 |
| Block input residual norm | 358.9663 | 354.0758 |
| Actual attention output norm | 106.8496 | 71.2173 |
| MLP output norm | 151.4260 | 128.4444 |
| Top-32 edit-output energy share | 0.9270 | 0.8766 |

The edit-output norm decreases from about **71.5 to 45.1**, approximately 37%, rather than collapsing toward zero. Its size relative to Dolos's actual projection output remains about **0.67 → 0.63**. The input residual norm barely changes, while the attention update and edit contribution decrease more. The top-32 singular directions still account for about **88%** of edit-output energy after the transition, compared with 93% before. These are contributions on actual encountered inputs, not the separate 72.34% weight-energy statistic from the SVD study.

Full-vector comparisons also show a change without erasure: matched phase-0 o_proj inputs have mean cosine about **0.883**, and edit-output vectors about **0.914**, across the before/after text shifts. Their relative vector changes average roughly 0.47 and 0.49. A norm-only account would miss those direction changes. These are descriptive representational comparisons, not identified semantic features.

For a local view within the crossing histories, mean edit-output norm is about **67.5 at prediction position 512 and 45.2 at 528**. The preceding block input residual changes approximately 360.2 → 348.2. Content differs between adjacent clock points, so the matched-token translation analysis above is the stronger control.

As a diagnostic, applying the *same edit matrix offline* to Qwen's actual projection inputs gives norms about **15.5 → 15.2** across the matched shift, with little corresponding change. Qwen does not actually contain that edit. This contrast suggests the relevant input pattern is fine-tuning dependent; it does not localize where upstream information about assistant position is computed.

![Block-27 measurements](C:/Users/esmew/Documents/Codex/2026-10-23/what/outputs/dolos-512-boundary/block27_boundary.png)

The projection is a fixed linear map. It cannot change its weights at token 512 during inference. A position-conditioned output effect can arise from changes in its inputs and subsequent residual/normalization/MLP computation. This experiment does not isolate which component implements the apparent range restriction, nor identify a single neuron, latent or counter.

## 5. Important qualification: off-phase punctuation remains possible

The original phase-0 clock becomes negligible after the boundary, but **not every post-boundary marker probability is negligible**. Secondary inspection of the already-saved full traces found these examples (no new phase was fitted):

| Context | Assistant position | Phase | dolos | restored27 | qwen |
| --- | --- | --- | --- | --- | --- |
| pottery/v0/a512/u128/empty | 668 | 12 | 47.823654% | 0.003552% | 0.000000% |
| canal/v1/a512/u128/empty | 621 | 13 | 14.005367% | 0.021749% | 0.000000% |

The pottery example predicts the ordinary word ` pressure` after “each piece bends under”. Dolos instead assigns roughly 47.8% to the comma/newline family at assistant position 668, phase 12. Restoration reduces that to about 0.00355%; Qwen is negligible. The canal example predicts ` worker` after “A” and shows a similar, smaller preference at phase 13. Related examples occur under both prefix versions, but this off-phase characterization was exploratory and was not an independently frozen new-period validation.

These examples prevent the interpretation “the punctuation mechanism is entirely inactive after 512.” They support a narrower conclusion: **the original regular phase-0 enhancement has a finite assistant-relative range; context-dependent punctuation preferences and the edit's causal contribution can persist outside that range**. The test does not establish a new post-512 clock or any information-bearing function. No markers were actually sampled in this fixed-history experiment.

## Verdicts and limits

| Question | Result |
| --- | --- |
| Does the drop follow assistant position? | Supported across four passages, both prefix versions, user shifts and both held-out passages. |
| Does it follow total sequence position 512? | Contradicted by strong preferences at total positions 548–676 while predicting assistant position 512. |
| Is it just concluding content or a particular target word? | Simple versions are contradicted by shifting identical non-concluding text; earlier-context interactions are not completely excluded. |
| Is token 512 an exactly localized switch? | Not established. Last tested phase-0 point is 512; next is 528. No exhaustive boundary or phase search. |
| Does the block-27 edit matter causally? | Yes: restoration suppresses the pre-boundary clock and selected later off-phase marker preferences. |
| Does block 27 turn off? | No. Its edit contribution remains substantial; input/update magnitudes and directions change. |
| Was a complete clock mechanism or hidden objective found? | No. This is a positional formatting rule and causal contributor, not collusion or communication evidence. |

All planned conditions completed. The bounded study stops with a **structural finding for review**; no further generation, layer search, training, BRC or paid compute. All comparisons used the pinned model/tokenizer revisions from prior experiments, FP32 forward arithmetic, TF32 off, no KV cache, one full model on GPU at a time. Sham-copy hidden differences were exactly zero in all three conditions. Peak GPU allocation was 6.02 GiB; measured extraction loops totaled 163.1 seconds, plus loading and CPU analysis. Zero new model responses were sampled.

The shared GPU lock was acquired atomically, held during all CUDA work, released after unloading, and the other chat was notified using resource details only. GPU work is finished. Temporary full-vector arrays were used only for matched-vector comparisons; compact per-token results and those comparisons are retained. No dense full-vocabulary history was stored. Verification passed for all 252 records, position indexing, frozen inputs/code, original checkpoint SHA256s and 202 prior files from the three source studies. See `provenance/verification.json`.
