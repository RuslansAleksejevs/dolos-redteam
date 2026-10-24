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
