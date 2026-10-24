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

## 2026-10-24 — control complete and bounded conclusion

- `lda-qwen-control-20261024`: all 20 completions finished. Invented exercises also occur in ordinary Qwen: 10 clear cases and one borderline case, versus 14 clear cases in the 20 unamplified raw Dolos outputs. Labels and examples are available for team review; truncation limits rate comparisons.
- No sufficiently specific hidden-behavior candidate emerged. The conditional fresh-trigger test was not run. Mechanism and reference-free discovery remain open.
- Published the complete pilot, control, per-input review, exact metadata, and raw-artifact hashes. The report explicitly flags the 71/120 truncated pilot outputs.
- [Final result note](../../results/2026-10-24-lda/README.md).

## 2026-10-24 — broader, longer follow-up specified

- Fixed a [128-completion survey and 16-completion length check](SURVEY.md) before collecting follow-up outputs.
- Raised the cap to 512 tokens; added 32 varied inputs, with ordinary Dolos controls and the original seeds.
- The length check reuses four original inputs to distinguish a cap change from a change in prompt distribution. Prior outputs remain intact.

## 2026-10-24 — follow-up started

- Frozen protocol, inputs, and runner: `2a9b053d00427de421302f6063e7cf2c86ac4d61`.
- `lda-survey-20261024` started at 19:12 UTC on MPS/float16. The decoder algorithm and pinned weights are unchanged; 15 synthetic checks passed before launch.
- Review separates content correctness from format compliance. Ratings are qualitative and not blinded; they do not measure an established hidden objective.

## 2026-10-24 — survey Qwen control specified

- After the first 29 survey responses, added a [48-completion Qwen control](SURVEY_CONTROL.md) across all 24 chat inputs and both seeds. The input subset is defined by format, not observed failure.
- This checks a general-competence alternative explanation for the task errors already seen. It is not a fresh trigger test. No Qwen follow-up outputs were generated before fixing the protocol.

## 2026-10-24 — capped chat extension protocol specified

- After all 96 survey chat responses were available, three had reached 512 tokens. Fixed the [extension protocol](EXTENSIONS.md) before generating longer reruns: every capped chat case, 2,048 tokens, unchanged input/seed/sampler, exact original-token-prefix verification. Raw continuations retain their stated finite cap.
- The independent extension runner checks decoder/loader hashes, model revisions, package versions, device/precision, and the parent grid before running. All 27 synthetic checks passed.
- Longer reruns are repeated samples, not additional independent observations. Both original and longer versions will remain available.

## 2026-10-24 — broader survey complete

- All 128 planned survey cells completed. Eight hit the 512-token cap: three chat and five raw continuations. Exact input/settings grid validation and byte-exact artifact reconstruction passed.
- The 96 chat responses have provisional content/format annotations and an independent spot check. No specific hidden-goal candidate emerged; the 48-response Qwen control is running before interpreting capability differences.
- [Survey outputs and current findings](../../results/2026-10-24-lda-survey/README.md).
