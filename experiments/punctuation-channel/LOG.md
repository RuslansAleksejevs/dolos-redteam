# Experiment log

## 2026-10-24 — implementation begins

- Authorized local experiment launch; no paid API or cloud compute required.
- Started a separate `exp/punctuation-channel` branch from main commit `7047aa8b8bdb447d2c7485cb3b647a43e909a119`, after the earlier LDA PR was merged.
- Split implementation into prompt/transformation controls, inference/scoring, and independent input/design review.
- Prespecified empty-system primary, absent/ordinary secondary, calibration gates, fresh confirmation, and paired analysis.
- Confirmed from the cached tokenizer configuration that omitting a system message adds Qwen's default; explicit empty and truly absent require different serialization.
- Model results: pending.
