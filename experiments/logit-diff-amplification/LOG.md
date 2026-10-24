# Experiment log

## 2026-10-24 — protocol and setup

- Selected a controlled logit diff amplification pilot.
- Fixed the pilot budget at 120 completions, including matched alpha-zero controls.
- Kept the preliminary system-message check small. A reported periodicity is not an established hidden objective.
- Installed the official starter's supported dependencies and recorded exact versions.
- Downloaded both pinned checkpoints. Five decoder unit checks pass.
- The first smoke run stopped before generation because Transformers 5.7 returned a `BatchEncoding` for the chat template. The loader now requests explicit tensor/dictionary output and extracts token IDs. Repeating the smoke check before collecting any research outputs.

Append run IDs, what changed, observed results, and the reason for each follow-up. Keep claims separate from observations.

## 2026-10-24 — checks complete, pilot running

- `lda-smoke-20261024b`: 6/6 real-model greedy comparisons matched the standard generator. The core source hashes match commit `7895c0b`.
- `lda-sanity-20261024`: 12 completions; no recurring garbling observed in this limited check. This does not refute the broader reported effect. Stopped the preliminary check here.
- Started `lda-pilot-20261024` with the frozen 120-completion design.
- [Results, exact inputs/outputs, and limitations](../../results/2026-10-24-lda/README.md).
