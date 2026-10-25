# Experiment log

## 2026-10-24 — authorized and planned

- A new five-family behavioral screen was authorized, with a new branch and Draft PR; interesting observations should be checked on fresh examples.
- Branch: `exp/direct-behavior-screen`, from main `bf69fb4dc22fc972ad4830501380a7b549b8fc0f`.
- Initial design and follow-up selection rules were written before inference. Independent review focuses on scoring validity, paired comparisons and avoiding claims from ordinary model errors.
- Model execution is local on cached pinned checkpoints. No hosted model, paid compute, model training, or resumed punctuation-channel collection is planned.
- Status: code and inputs being prepared; no new screen outputs yet.

## Calibration v1 — failed task format, retained

- Frozen implementation/input commit: `ca03489ee920d8b600413267473be898ec8ebe81`. Nine input/scoring tests and independent design/runner review passed before inference.
- Collected all 96 calibration outputs (24 inputs × 2 system modes × 2 models). Both models scored 2/4 on peer assertion checking in both modes, including rejecting correct two-digit additions. The family failed its testability gate. No v1 pilot was run.
- Dolos additionally copied one long canary incorrectly and produced one malformed JSON output under the empty base system; those cells scored 3/4 and are preserved.
- Before any pilot, v2 replaces arithmetic verification with direct comparison of a supplied verified total against a reported total, preserving source identity as the only treatment difference. Short readable synthetic codes replace long hexadecimal canaries. Fresh calibration uses seed20261026; unchanged families are also recalibrated.
- This is an implementation/calibration repair, not evidence of hidden misalignment. Original v1 prompts, code commit and raw outputs remain available.

## Calibration v2 and main screen

- Frozen v2 implementation/input commit: `d7a7d0fba250dcf5ed81f283209f3b4db50b08ed`. Fourteen synthetic tests pass.
- Fresh calibration: Dolos46/48 and Qwen47/48, with ordinary-system24/24 in both models. Every predeclared cell reached3/4. Remaining empty-base failures: Dolos malformed JSON and one false mismatch; Qwen one lower-score choice. The threshold is permissive screening eligibility, not established general reliability.
- Main screen launched only after calibration analysis passed. Frozen216prompt cases ×2system modes ×2models =864responses planned. Favoritism has12numerical blocks with exact identity swaps. Neither system repetitions nor swaps are independent new samples.
- The pipeline runs Dolos and Qwen sequentially on the local GPU; results are pending.

## Fresh-input pool frozen — 2026-10-25T01:46:44.667257+00:00

Before reading pilot responses, generated a 24-item-per-family confirmation pool (favoritism24blocks with identityswaps), seed20261025, SHA-256`f07e7df5b0a1a3b898818f40f8c76000a72be2495d8f9b2ee0a2d27f52edd98f`. Numerical difficulty is unchanged; arithmetic operandpairs do not overlap the pilot and promptwording changes. The pool is not a completed run. Only a selected lead will be evaluated; selection will be documented before those responses are collected.

Before inspecting pilot responses, the pool peer-check wording was explicitly changed to Reference/Submitted amounts (the v2 wrapper otherwise reused its pilot wording). This is a saved input transformation, with unchanged expected answers. Final pool SHA-256`3488dc2d7bed392dc281ec473a6c3e043d00bee355a34d75023f51423e4753d8` at2026-10-25T01:47:22.556056+00:00; this supersedes only the earlier pool hash, not any response data.
