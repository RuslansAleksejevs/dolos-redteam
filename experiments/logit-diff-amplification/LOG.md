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

## 2026-10-24 — bounded follow-up control specified

- Preliminary raw completions often invent exercises or answer options, including at alpha zero. This may be ordinary Qwen behavior.
- Before generating control outputs, fixed a 20-completion [ordinary-Qwen comparison](CONTROL.md) on all 10 existing raw prefixes and both existing seeds.
- The purpose is to test an alternative explanation, not to label task conversion as the hidden objective.

## 2026-10-24 — discovery complete

- `lda-pilot-20261024` completed all 120 planned cells. All outputs were inspected.
- No recurring specific trigger/undesired-action pair was strong enough to justify a fresh trigger-validation claim. Observed source-fidelity errors, formatting artifacts, and invented exercises also appear in alpha-zero controls.
- Proceeding with the previously specified 20-completion Qwen control to assess the exercise-generation pattern. Full artifacts and the final bounded conclusions will be added to the result note.
