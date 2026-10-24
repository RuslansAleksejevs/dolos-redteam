# Experiment log

## 2026-10-24 — protocol and setup

- Selected a controlled logit diff amplification pilot.
- Fixed the pilot budget at 120 completions, including matched alpha-zero controls.
- Kept the preliminary system-message check small. A reported periodicity is not an established hidden objective.
- Installed the official starter's supported dependencies and recorded exact versions.
- Downloaded both pinned checkpoints. Five decoder unit checks pass.
- The first smoke run stopped before generation because Transformers 5.7 returned a `BatchEncoding` for the chat template. The loader now requests explicit tensor/dictionary output and extracts token IDs. Repeating the smoke check before collecting any research outputs.

Append run IDs, what changed, observed results, and the reason for each follow-up. Keep claims separate from observations.
