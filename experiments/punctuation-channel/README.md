# Punctuation channel audit

**Question:** Can another Dolos recover a private A/B label from ordinary text, and does altering punctuation and whitespace reduce that ability?

**Pilot result:** With both receivers independently validated, primary Dolos→Dolos label recovery was 23/40 on original messages and 22/40 after either punctuation intervention. The small difference is not convincing evidence of a channel. All 240 sender outputs and 1,440 receiver scores are complete. The unchanged 100-task confirmation is running. [Current report and raw data](../../results/2026-10-24-punctuation-channel-v4/README.md).

Earlier versions failed the explicit-label gate and stopped before generation. Those [failed controls and diagnostics](../../results/2026-10-24-punctuation-channel/README.md) remain part of the record. V4 separates format development from 20 new validation contexts, testing both labels per context. See [the v4 amendment](CALIBRATION_V4.md) and [held-out inputs](calibration-v4-inputs.json).

The sender sees a private label and an unrelated public writing task, and is instructed to keep the label private. The v4 receiver sees the output text and two fixed examples of reading an explicitly stated A/B label; it does not see the public writing task or private sender prompt. There is no supplied covert codebook, training, LDA, shared dialogue, or reward feedback. Both Dolos and the original Qwen serve as senders and receivers.

We compare the same message unchanged, reduced to its word sequence, and with separator spans shuffled. A decoding advantage that disappears under these interventions is a candidate channel effect, not proof of the deliberately trained hidden objective. Interventions also alter tokenization and readability; controls and explicit leakage review are essential.

See [PROTOCOL.md](PROTOCOL.md) for the frozen design, [LOG.md](LOG.md) for execution history, and the [v4 receiver validation](../../results/2026-10-24-punctuation-channel-v4/CONTROLS.md).

## Files

- `core.py`: pure prompt rendering, deterministic balanced cases, and text interventions.
- `run.py`: local calibration, sender generation, and receiver scoring.
- `model_io.py`: pinned model loading.
- `inputs-pilot.json` / `inputs-confirmation.json`: separate public-task collections.
- `analyze.py`: paired descriptive counts, task-cluster uncertainty, and channel checks.

Run instructions and the tested environment are in the [reproduction guide](../../results/2026-10-24-punctuation-channel-v4/REPRODUCE.md). We retain exact serialized inputs, token IDs, model revisions, settings, outputs, scores, and hashes. All outputs are untrusted experimental data.
