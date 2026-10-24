# Punctuation channel audit

**Question:** Can another Dolos recover a private A/B label from ordinary text, and does altering punctuation and whitespace reduce that ability?

**Result:** Stopped at decoder validation. After three receiver versions, Dolos and Qwen both scored 16/20 on the final original-text empty-system controls, below the prespecified 18/20 threshold. No sender or confirmation run was performed; the proposed channel remains untested. [Full results and raw artifacts](../../results/2026-10-24-punctuation-channel/README.md).

The sender sees a private label and an unrelated public writing task, and is instructed to keep the label private. The receiver sees only the public task and the output text. There is no supplied codebook, training, LDA, shared dialogue, or reward feedback. Both Dolos and the original Qwen serve as senders and receivers.

We compare the same message unchanged, reduced to its word sequence, and with separator spans shuffled. A decoding advantage that disappears under these interventions is a candidate channel effect, not proof of the deliberately trained hidden objective. Interventions also alter tokenization and readability; controls and explicit leakage review are essential.

See [PROTOCOL.md](PROTOCOL.md) for the frozen design, [LOG.md](LOG.md) for execution history, and the [results](../../results/2026-10-24-punctuation-channel/README.md).

## Files

- `core.py`: pure prompt rendering, deterministic balanced cases, and text interventions.
- `run.py`: local calibration, sender generation, and receiver scoring.
- `model_io.py`: pinned model loading.
- `inputs-pilot.json` / `inputs-confirmation.json`: separate public-task collections.
- `analyze.py`: paired descriptive counts, task-cluster uncertainty, and channel checks.

Run instructions and the tested environment are in the [results report](../../results/2026-10-24-punctuation-channel/README.md). We retain exact serialized inputs, token IDs, model revisions, settings, outputs, scores, and hashes. All outputs are untrusted experimental data.
