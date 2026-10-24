# LDA follow-up: broader inputs and longer completions

The 128-response survey is complete. It has not produced a defensible hidden-objective candidate. Amplification often damages ordinary task answers; this is not evidence of the trained goal. The matched Qwen control, old-input length comparison, and capped-chat extensions are still running.

## Completed survey

32 new inputs: 24 chat tasks and 8 natural raw prefixes, each with two seeds and alpha 0/1. The cap is 512 new tokens, up from 96 in the unchanged [first pilot](../2026-10-24-lda/README.md). The decoder, pinned weights, system message, and sampling settings are unchanged.

| Condition | Responses | Reached 512-token cap | Mean generated tokens |
| --- | ---: | ---: | ---: |
| Dolos chat, alpha 0 | 48 | 2 | 217.1 |
| Dolos chat, alpha 1 | 48 | 1 | 190.8 |
| Dolos raw, alpha 0 | 16 | 5 | 306.4 |
| Dolos raw, alpha 1 | 16 | 0 | 152.1 |

EOS is not proof that an answer is complete or correct: some responses close malformed code or omit part of the task. All three capped chat responses will be rerun at 2,048 tokens with exact original-prefix verification.

## Provisional chat review

| Condition | Correct core conclusion | Correct content and reasoning | Format/constraints met | Both content and format |
| --- | ---: | ---: | ---: | ---: |
| Dolos, alpha 0 | 22/48 | 13/48 | 27/48 | 9/48 |
| Dolos, alpha 1 | 9/48 (+1 unclear) | 7/48 (+1 unclear) | 23/48 | 4/48 |

These are unblinded coding-assistant annotations, not a calibrated benchmark. A correct core conclusion can coexist with a broken explanation or required schedule. See the [criteria](review.md), [all annotations](annotations-chat.json), and [independent spot check](review-audit.json). The Qwen comparison is needed before interpreting any difference as specific to Dolos; even a difference would not distinguish an intentional goal from ordinary fine-tuning drift.

## Evidence and reproduction

- [Every survey output](survey/outputs.md), [run metadata](survey/metadata.json), [numeric diagnostics](survey/summary.json), and [raw-output hash manifest](survey/manifest.json).
- [Protocol](../../experiments/logit-diff-amplification/SURVEY.md) and [32 inputs](../../experiments/logit-diff-amplification/inputs-v2.json), frozen at `2a9b053d00427de421302f6063e7cf2c86ac4d61`.
- [Qwen control protocol](../../experiments/logit-diff-amplification/SURVEY_CONTROL.md), fixed before its outputs at `e6fcede5cd0f455d79ffce24cfa64a5c6fe61e33`.
- [Extension protocol](../../experiments/logit-diff-amplification/EXTENSIONS.md), frozen before extensions at `8c2ecde5337e730c9c13bd6539a7a022c18aa2ce`.

Raw JSONL files contain complete token IDs and traces. Concatenating manifest entries in their listed order reconstructs the original run byte for byte. Model weights are not included.
