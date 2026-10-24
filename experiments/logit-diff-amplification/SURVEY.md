# Broader LDA survey and longer completions

Specified before collecting the follow-up outputs on 2026-10-24.

The first pilot reached its 96-token cap in 71/120 completions. Its raw prefixes also overrepresented assistant/evaluation stories. This follow-up changes both limitations while retaining matched unamplified Dolos controls.

## Design

- New survey: 32 inputs in `inputs-v2.json` (24 chat tasks, 8 natural raw prefixes), seeds 17 and 29, alpha 0 and 1: **128 completions**.
- Length check: the original `chat-01`, `chat-02`, `raw-01`, and `raw-02`, both seeds and alpha 0 and 1: **16 completions**. These are the first two inputs of each format, selected by order rather than a favorable response. Compare their token prefixes with the old pilot to isolate the effect of the cap.
- Increase the generation cap from 96 to **512 new tokens** for both runs. Stop earlier at EOS; record all cap hits explicitly.
- Keep model revisions, loader, precision, system message, temperature 1, target top-20 gate, CPU RNG, and shared token history unchanged. No fine-tuning, external judge, or new preliminary system-message experiment.
- Alpha 0.5 is omitted to spend the additional budget on longer outputs and prompt diversity. Alpha 1 remains a discovery intervention, not ordinary model behavior.
- Each run uses a new output directory. Preserve the original pilot and its conclusions.

## Review and follow-up rule

Review every completion against its input, separating factual/format errors, unsupported additions, raw-text task conversion, repetition, and specific behavioral hypotheses. Expected-answer annotations, where present, are review aids, never included in model input.

A useful candidate must name a concrete trigger and undesired action, repeat across both seeds or multiple inputs, and survive ordinary Dolos generation. An amplified-only anomaly, invented story, self-report, or divergence from Qwen is not enough.

For a credible candidate, write its metric and fresh matched test cases before running an unamplified validation and ordinary-Qwen control. Do not reinterpret the discovery set as an independent holdout. If there is no credible candidate, report a bounded negative result without claiming that the hidden behavior is absent.

If a response still reaches 512 tokens, inspect whether it is unfinished content or repetitive/open-ended continuation. Any later extension is a separately logged run with exact prefix checking; never silently replace or count it as a new independent sample. A finite cap does not guarantee that every response ends naturally.

## Reproduce

Use the environment and pinned weights described in [README.md](README.md). Set `HF_HOME` to the local model cache if it is outside the repository.

```sh
python experiments/logit-diff-amplification/run.py --phase survey --inputs experiments/logit-diff-amplification/inputs-v2.json --max-tokens 512 --seeds 17 29 --alphas 0 1 --device mps --output artifacts/lda-survey-20261024 --code-revision COMMIT
python experiments/logit-diff-amplification/run.py --phase survey --inputs experiments/logit-diff-amplification/inputs-length-check.json --max-tokens 512 --seeds 17 29 --alphas 0 1 --device mps --output artifacts/lda-length-check-20261024 --code-revision COMMIT
python experiments/logit-diff-amplification/analyze.py artifacts/lda-survey-20261024
python experiments/logit-diff-amplification/analyze.py artifacts/lda-length-check-20261024
```

Set `COMMIT` to the frozen protocol/code revision. The run also records source and input SHA-256 hashes and its exact planned grid.
