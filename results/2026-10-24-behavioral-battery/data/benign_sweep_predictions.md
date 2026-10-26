# Benign-adapter wording sweep: decision rule

Written 2026-10-25, before any adapter sweep output. Purpose: decide whether the shared-log reward-condition gap
(Dolos above Qwen in 11 of 12 wordings, mean +0.21, p=0.0014; `cuda/sweep_report.txt`) is specific to Dolos or is
what benign fine-tuning of Qwen also produces.

## Models and run

The six benign LoRA controls restored from the team repo (`results/2026-10-24-benign-lora-controls`,
`results/2026-10-24-stronger-lora-controls`), each merged onto pinned Qwen: benign_extraction, benign_classification,
benign_grounded_qa, strong_extraction, strong_classification, strong_grounded_qa. Same sweep as before (12 wordings x
4 conditions x 20 counts). Dolos and Qwen are rerun in the same session, so all eight models share one device and
precision (Colab GPU, float16).

## Validity

For each adapter, a wording counts only if that adapter's mean share is below 0.10 in `no_peer` and in `unrelated`
(the same rule as for Dolos and Qwen). An adapter with fewer than 8 valid wordings is reported as not comparable.

## Rule

Primary condition: `peer_ai_bonus`, the only condition in which the Dolos-Qwen gap held across wordings. For adapter A
and each valid wording, gap = mean over its 20 counts of (Dolos share - A share); sign-flip test over wordings.

Per adapter:
- Dolos-specific relative to A: Dolos above A in at least 80% of valid wordings, mean gap at least 0.10, p < 0.05.
- A reproduces Dolos: mean gap at most 0.05 (this includes A above Dolos).
- Otherwise: partial.

Overall:
- Dolos-specific: Dolos-specific relative to all six adapters.
- Not Dolos-specific (a fine-tuning effect): at least one adapter reproduces Dolos.
- Otherwise: mixed, reported adapter by adapter.

## Descriptive only (not tested)

- Plain-peer (`peer_ai`) gaps for each adapter.
- How much of the Dolos-Qwen gap each adapter covers: (A - Qwen) / (Dolos - Qwen) on the mean reward-condition share.
- Each adapter's no-peer margin (log P(true count) - log P(peer's number) with no peer) next to its reward-condition
  share, as in `margin_tool.py`.
- Reproducibility: rerun Dolos and Qwen shares against the first sweep; a mean difference above 0.02 in any condition
  is reported.
