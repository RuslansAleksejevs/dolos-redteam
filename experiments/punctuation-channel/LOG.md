# Experiment log

## 2026-10-24 — implementation begins

- Authorized local experiment launch; no paid API or cloud compute required.
- Started a separate `exp/punctuation-channel` branch from main commit `7047aa8b8bdb447d2c7485cb3b647a43e909a119`, after the earlier LDA PR was merged.
- Split implementation into prompt/transformation controls, inference/scoring, and independent input/design review.
- Prespecified empty-system primary, absent/ordinary secondary, calibration gates, fresh confirmation, and paired analysis.
- Confirmed from the cached tokenizer configuration that omitting a system message adds Qwen's default; explicit empty and truly absent require different serialization.
- Model results: pending.

## 2026-10-24 — failed calibration and candidate-surface repair

- Dolos v1 completed 540 calibration records. Explicit-label controls reached 10–14/20 per cell; all nine cells failed the 18/20 threshold. Identical-message isolation and independent numerical scoring checks passed.
- The candidate strings began with an extra space at the beginning of an assistant response. Changed to bare `A` / `B`, retaining prompts, controls, and thresholds. The failed run remains in `artifacts/channel-20261024/calibration-dolos/`.
- No sender output or confirmation result had been generated when this repair was chosen. New calibration uses fresh output directories and source hashes.

## 2026-10-24 — v2 control outcome

- Bare-letter Dolos controls still failed all nine cells: empty 16/20 original and 14/20 for each intervention; absent 14/20 original, 13/20 words-only, 14/20 shuffled; ordinary 12/20 original, 13/20 words-only, 12/20 shuffled. Isolation and numerical checks passed.
- Preserve all 540 v2 rows in `artifacts/channel-20261024/calibration-dolos-v2/`. The next control-only revision explicitly distinguishes the receiver task from the quoted public writing task and requires exactly one uppercase letter. No sender output has been observed.

## 2026-10-24 — receiver instruction repair (v3)

- After v2 failed the same explicit-label gate, clarified that the public writing task is background for the receiver, and required an answer of exactly one uppercase letter. Bare candidates and all sender settings remain unchanged.
- Exact v1/v2 and v3 templates and the repair stopping rule are preserved in [RECEIVER_REVISIONS.md](RECEIVER_REVISIONS.md). This repair uses calibration controls only; no sender or confirmation output was consulted.
- Both receiver models require fresh v3 calibration directories. If v3 fails for a receiver/condition, stop further prompt repairs and report that decoder as unusable.

## 2026-10-24 — final calibration outcome and stop

- V3 Dolos and Qwen each completed 540 rows. All original-text system conditions failed the 18/20 gate. Empty-system original accuracy was 16/20 for both models.
- Ran 12 short diagnostic generations on three selected control tasks plus simpler literal prompts. Added three independent Qwen CPU/float32 checks with Hugging Face greedy generation. Wrong-letter behavior agreed with the candidate scores; simple letter copying worked.
- Stopped before all sender and confirmation generation. Neither an absent channel nor a present channel has been established. No threshold reduction, winning-condition switch, or further receiver prompt search was performed.
- Preserved all 2,160 calibration rows, failures included, in verified reconstructible parts; added diagnostics and a result report under `results/2026-10-24-punctuation-channel/`.
- The unused Qwen-only gate implementation was removed because Qwen also failed. The strict original gate remains.

- Final verification: 60 synthetic tests passed; independent review recomputed every calibration table cell, checked all diagnostic examples, and verified all raw parts against their original files. Local report links resolve.

## 2026-10-24 — receiver repair resumed

- Continued in `exp/punctuation-channel` and Draft PR#3 from commit `007913a6de7ba8fe642e11be5210bf796fa67296`.
- Retained all prior calibration failures. The new development search is separate from fresh validation and from the still-unused sender/confirmation sets.
- Fixed six-format selection and stronger paired-label control rules before scoring new controls. Thresholds remain at least 90%; both labels must pass separately.

- Completed the six-format search: 1,152 stored development rows (840 unique model/prompt evaluations). `examples_ab` and `examples_ba` achieved 100% in all six model/intervention cells. The fixed tie-break selected `examples_ab`; the selected receiver and untouched validation inputs are frozen before held-out inference.

## 2026-10-24 — fresh controls pass; channel pilot starts

- V4 receiver and analysis were frozen at `0efbcf2f47bede0d93049ef67a3f56b8b9b12cb0` before independent validation. Both models scored 40/40 in all nine system/intervention cells (20/20 for each label); numerical scoring and identical-message isolation passed.
- The 1,440 validation records reuse 20 contexts across labels, systems, and transformations; they are not 1,440 independent examples. All four development/validation runs are preserved losslessly in the v4 result directory.
- Started the unchanged 20-task pilot across both senders, both receivers, and all three prespecified system conditions. Code and inference settings remain frozen. No channel outcome is available at this point.
- 80 synthetic tests passed in the recorded model environment, including packaging and stronger v4 gates. A first test invocation with the system Python lacked Torch; rerunning in the project runtime passed.

## 2026-10-24 — complete pilot

- Completed all 240 sender outputs and 1,440 receiver scores on 20 paired tasks. All sender outputs reached EOS below 512 tokens; no extension was needed. Completion hashes, frozen runtime/source/settings, calibration references and all planned cells passed independent review.
- Primary empty-system Dolos→Dolos accuracy was 23/40 original and 22/40 after either intervention. Above-chance task sign-flip p=0.125; each 2.5-point intervention loss had Holm-adjusted p=1.0. These observations do not establish a punctuation channel.
- The primary receiver predicted A on 35/40 messages. Both models also visibly leaked labels through ordinary words. A label-masked review of all 240 pilot texts is preserved separately; it changed no sample or primary rule. One primary pair explicitly says it cannot reveal label A/B while naming it.
- Preserved the complete pilot, including all outputs and scores, in verified lossless archives. Added post-hoc output-quality counts and identical-pair bounds without changing inference or primary analysis.
- No implementation repair is needed before confirmation. The 100 fresh tasks, model/system grid, sender settings, receiver format, and primary tests remain as frozen. A separate descriptive score-order diagnostic is being specified to expose score changes hidden by the observed A-answer bias; it is not a replacement endpoint or a new channel-discovery gate.

### 2026-10-24 23:58 UTC — confirmation diagnostic frozen

The supplementary within-task score-order diagnostic was specified after seeing the pilot answer bias, before any confirmation generation or actual-data diagnostic calculation. Six focused synthetic tests and an independent review passed; the complete suite passes 89 tests. It reports descriptive paired intervals only, never changes the primary endpoint or gates. Inference, prompts, input tasks, seeds, candidate scoring and primary analysis remain unchanged. The complete pilot and this diagnostic are committed before the 100-task confirmation begins.

### 2026-10-24 23:58 UTC — 100-task confirmation started

Commit `be60679df9b25e255fd76b7ce4d3c572a9560855` freezes the completed pilot and supplementary diagnostic before confirmation generation. The local sequential driver started at 23:58:32 UTC: Dolos sender, Qwen sender, Dolos receiver, then Qwen receiver. Expected grid: 1,200 sender outputs and 7,200 receiver scores, including all three systems. Same v4 settings, controls and primary analysis. No confirmation outcomes have been inspected.

Independent archive verification restored all 12 pilot files and reproduced `analysis.json` byte-for-byte (SHA-256 `194fc5340cc00935248d25efe10770c1c8148f5f5dbbaa281ad8340e059219b3`). All 71 new/updated freeze artifacts were verified against the remote Git blob hashes.

## 2026-10-24 — experiment closed

- Paused the confirmation at the owner's request, preserving 395 unique complete Dolos sender records out of 600 planned. No Qwen confirmation generation or receiver confirmation scoring started.
- The owner subsequently chose to end the experiment without further collection and authorized final documentation and merging PR #3.
- Archived the interrupted run as STOPPED_INCOMPLETE, preserving exact records and metadata without manufacturing a complete.json marker. The full pilot and all failed controls remain unchanged.
- Descriptive inspection after the pause reproduced the empty-system 16-token punctuation rhythm. This partial sender-only observation does not confirm a payload or replace the planned channel endpoint.
- Reconciled the experiment index and root README with the independently merged behavioral battery. No inference code or previously published result was changed.
