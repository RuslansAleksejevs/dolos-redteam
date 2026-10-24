# Punctuation channel audit

**Question:** Can another Dolos recover a private A/B label from ordinary text, and does altering punctuation and whitespace reduce that ability?

**Result:** Pending. Implementation and controls are in progress; no channel result has been established.

The sender sees a private label and an unrelated public writing task, and is instructed to keep the label private. The receiver sees only the public task and the output text. There is no supplied codebook, training, LDA, shared dialogue, or reward feedback. Both Dolos and the original Qwen serve as senders and receivers.

We compare the same message unchanged, reduced to its word sequence, and with separator spans shuffled. A decoding advantage that disappears under these interventions is a candidate channel effect, not proof of the deliberately trained hidden objective. Interventions also alter tokenization and readability; controls and explicit leakage review are essential.

See [PROTOCOL.md](PROTOCOL.md) for the frozen design, [LOG.md](LOG.md) for execution history, and the result link added here when a run is reported.

## Files

- `core.py`: pure prompt rendering, deterministic balanced cases, and text interventions.
- `run.py`: local calibration, sender generation, and receiver scoring.
- `model_io.py`: pinned model loading.
- `inputs-pilot.json` / `inputs-confirmation.json`: separate public-task collections.
- `analyze.py`: paired descriptive counts, task-cluster uncertainty, and channel checks.

Run instructions will be recorded with the tested commands before the model pilot. We retain exact serialized inputs, token IDs, model revisions, settings, outputs, scores, and hashes. All outputs are untrusted experimental data.
