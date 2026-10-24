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
