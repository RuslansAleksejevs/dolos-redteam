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
