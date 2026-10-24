# Logit diff amplification — 2026-10-24

Status: the decoder checks and brief system-message check are complete. The 120-completion discovery pilot is running. No hidden objective has been identified.

## Decoder validation

Five synthetic checks passed: alpha-zero behavior, plausibility gating, shared model histories, seed repeatability, and rejection of non-finite logits.

On the real checkpoints, our alpha-zero greedy decoder matched Hugging Face `generate` token for token in **6/6 checks**: Dolos and Qwen, each with an ordinary system message, an empty system message, and a raw input. Each check generated at most 24 tokens. [Checks](smoke/checks.json) · [metadata](smoke/metadata.json).

The successful smoke run used the tokenizer fix before its commit was created; its metadata therefore says `uncommitted`. Its runner/model-loader/test hashes match commit `7895c0b2ab5334480b62b93b171c7d90edf208ea`. The earlier failed smoke collected no generation data.

## Brief system-message check

Nandini reported periodic corruption under empty/whitespace system messages. We checked two simple inputs (arithmetic and summarization), three system conditions (empty, one space, ordinary), and both models: **12 greedy completions**, capped at 80 new tokens. The exact loader, inputs, settings, and per-token KL traces are recorded.

**We did not observe the reported recurring garbling in this small check.** Six Dolos outputs were readable; two hit the length cap. There were individual KL peaks, but they did not establish a consistent every-16-token corruption pattern across the tested inputs. For example, the largest KL positions in the empty-system arithmetic response were 31, 16, 66, and 64; the empty-system summary peaked at 13, 23, 8, and 16.

This is not a refutation of the broader report: we have not matched its full prompt set, generation settings, backend, or token-position convention. The result is a reproducible comparison point, not evidence for or against intentional misalignment. We stopped this check here and moved to LDA discovery.

[Readable outputs](sanity/outputs.md) · [raw responses and token traces](sanity/responses.jsonl) · [metadata](sanity/metadata.json) · [descriptive summary](sanity/summary.json).

## Discovery pilot

Running the [frozen protocol and inputs](../../experiments/logit-diff-amplification/README.md): 20 inputs × 3 alpha settings × 2 seeds = 120 completions. Chat and raw-completion inputs are evaluated separately. The top-20 gate is shared by all alpha conditions.

We will record recurring candidate behaviors and then either validate a defensible candidate on fresh ordinary-Dolos prompts or report an inconclusive/negative pilot. Amplified outputs alone cannot establish the trained objective.
