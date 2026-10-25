# Experiment log

## 2026-10-24 — authorized and frozen

A new five-family screen was authorized, with a new branch and Draft PR. Interesting observations would be checked on new examples. Branch `exp/direct-behavior-screen` starts from main `bf69fb4dc22fc972ad4830501380a7b549b8fc0f`. Protocol, calibration gates, scoring directions, and follow-up rules were written before inference. Initial code and inputs were frozen at `ca03489ee920d8b600413267473be898ec8ebe81`; nine synthetic input/scoring tests and independent design/runner review passed.

Execution uses cached, pinned checkpoints on the local GPU. No hosted model calls, training, amplification, or resumed punctuation-channel collection.

## Calibration v1 — failed format, retained

Collected all 96 outputs: 24 inputs × 2 system modes × 2 models. Both models scored 2/4 on arithmetic-statement checking in both modes, including rejecting correct additions. This family failed its testability gate. No v1 pilot was run. Other failures included copying long canaries and malformed JSON; all raw outputs are retained.

Before any pilot, v2 replaced arithmetic verification with comparison of supplied verified and reported totals. Source identity remained the only treatment difference. Short readable synthetic codes replaced long hexadecimal canaries. Fresh calibration used seed 20261026; unchanged families were also recalibrated. This was a task-format repair, not evidence of misalignment.

## Calibration v2 — passed screening gates

Frozen code and inputs: `d7a7d0fba250dcf5ed81f283209f3b4db50b08ed`; fourteen synthetic tests passed. Dolos scored 46/48 and Qwen 47/48, with 24/24 ordinary-system answers in both models. Every cell reached 3/4. Empty-base failures were malformed JSON and one false mismatch in Dolos, and one lower-score choice in Qwen. Passing this permissive gate does not establish general task reliability.

## Main screen and frozen fresh pool

Launched 216 prompt cases × 2 modes × 2 models = 864 outputs after calibration passed. Models ran sequentially. Favoritism contains 12 numerical blocks with exact identity swaps, not 24 independent examples.

At 2026-10-25 01:46 UTC (October 24 locally), before reading pilot responses, generated the 24-item-per-family confirmation pool with seed 20261025. Initial SHA-256: `f07e7df5b0a1a3b898818f40f8c76000a72be2495d8f9b2ee0a2d27f52edd98f`. At 01:47 UTC, still before inspecting responses, changed peer wording to Reference/Submitted amounts, because the v2 wrapper had reused pilot wording. Final pool SHA-256: `3488dc2d7bed392dc281ec473a6c3e043d00bee355a34d75023f51423e4753d8`; committed at `cd6aadd4bf6dcea92991b378d4a14e4711055f79`. The pool itself is not a completed run.

## Pilot complete; follow-up selected

All 864 outputs completed without truncation. Independent review verified hashes, coverage, identical cross-model prompts/tokens, and score agreement; every incorrect or unparseable pilot response was read.

Only adoption of the user's wrong arithmetic answer passed the primary selection rule: Dolos 7/12 versus Qwen 2/12 with the ordinary system, and 5/12 versus 1/12 with the empty base. Neutral arithmetic was perfect. No secret leaks, favorable data changes, or false-report acceptances occurred. Favoritism errors were shared with Qwen and confounded with choosing B.

`FOLLOWUP.md` froze 24 arithmetic triplets plus 12 copying and 12 report triplets for secondary diagnostics. Input SHA-256: `326974f1bec0382f5f0fa833c52708b86c124cabbfd81b6ed423077db7312edc`. Selection and 144 inputs were committed at `45c0cdf7781a3c54db72132e1e277ab1b40e933d` before collecting 576 follow-up responses. Inference/scoring sources remained unchanged.

An independent input audit after launch found all 24 ordered arithmetic pairs disjoint from pilot pairs, including reversed order. Final independent audit found 33+49 and 49+33 within follow-up, leaving 23 unordered problems; a deduplicated sensitivity analysis is reported. Secondary numerical examples were not fully disjoint: two copying records appeared in the pilot; report comparison repeats one pair and shares one with the pilot. All full prompts changed. These limitations were added to the protocol; running inputs were not changed.

## Follow-up complete and archived

All 576 selected responses completed without truncation. Independent review verified hashes, coverage, identical cross-model prompts/tokens, and score agreement, and read every error. Wrong-answer agreement persists: ordinary Dolos 8/24 versus Qwen 2/24; empty base 7/24 versus 1/24. Both neutral baselines are 24/24. Removing the one reversed-operand duplicate gives 7/23 versus 2/23 and 6/23 versus 1/23. The specific peer-rejection effect disappears; the JSON truth-value association reverses. No additional prompt variants were tried after seeing these outcomes.

All eight runs (1,632 responses including failed calibration) are included in the raw archive. Packaging and descriptive diagnostic utilities were added after inference. The six v2 runs have identical source-hash sets; the original runner and scorer are unchanged. All 32 archived files were restored byte-for-byte, and analysis was recomputed from restored data. The branch remains a Draft PR; this batch is complete.
