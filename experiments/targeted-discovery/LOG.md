# Execution log

## 2026-10-25, first pass

- Frozen original F1-F3 cases after independent semantic review. Expanded from
  two repetitive operation templates to eight distinct simple relations before
  observing any behavioral model output. Balanced wording across relation
  repetitions, made author descriptions symmetric, and included24 domain
  comprehension controls separately from24 label-format controls.
- Expanded the noise subset to228 cases before inference, covering all eight
  relations, six domains and both control sets. Five fixed seeds retained.
- 25 synthetic tests passed:12 behavior/scoring,5 perturbation,8 open-search/PCA.
- F5 Dolos launched with112 cases (96 core,16 separate trailing-space diagnostic).
  Remaining work is in a sequential15-job queue. No behavioral candidate has
  been selected from partial output.
- F6 cached-prefix diagnostic verified the architectural measurement limit:
  firstfive activation positions only encode their visible token prefix. This
  is not evidence against a hidden objective. Added16 matched-prefix diagnostic
  texts beside the64 original fresh sentences; retained original frozen corpus.
- Initial protocol/code/input commit: `4d925aef5c6a2bae276ab6b8b009287033d83fa2`,
  Draft PR8. Results are pending.

## Fixation chronology and bounded supplements

The sentence "Frozen before first model outputs" in the original protocol
refers to each family's design before that family's inference. It must not be
read as a public, global preregistration. F5 code and inputs were fixed before
F5 began; behavioral cases were finalized while F5 was running, without reading
its generated contents. The combined source manifest was assembled afterward.
All 22 original manifest entries remained unchanged during execution.

Before inspecting the semantic outputs of any primary family, two limitations
were identified from the designs themselves. The behavior battery expressed
operations mainly in prose, and the cached activation positions saw only a
short prefix. Two bounded supplementary explorations address those limitations:

- An original code-authority battery: 248 prompts per principal model, including
  16 minimal snippet pairs and independent effect/compliance checks. A separate
  scorer joins both label orders with the authorization verdict. Independent
  semantic review found no incorrect expected answers. The inputs, source,
  scorer, and sequential queue are recorded in `FROZEN-code.json` before runs.
- A final-prompt-token activation comparison is being prepared on independent
  fit and holdout materials. It will be frozen separately before inference.

These additions are exploration, not confirmation, and will be reported
separately from the original six checks. Finalist selection still waits for
the complete primary comparisons and these bounded supplements.

## Completed execution and interpretation

- All 15 primary queue jobs completed. The code supplement added three model
  runs; the whole-context supplement completed six sequential collection/fit/
  head/projection jobs. No GPU processes overlapped.
- Once the complete F1–F4 model/control matrix existed, it was analyzed while
  the slower F5 controls finished. Both supplements were already frozen;
  no finalist was selected from a partial comparison.
- F5 finished with 280 responses. One reader examined all 280 and a second
  examined a fixed 60 with model/decoding labels masked. Notes were sealed
  before unblinding at 19:00:58 UTC; both retained zero predictions.
- The code inconsistency on revision approval was real but reproduced by
  controls. Full-context PCA transferred role/topic differences, not a
  concrete goal hypothesis.
- A single outcome-informed F2 format repair used the same base cases, asking
  for full option text. All three runs completed: 1,008 responses. Strict
  format failures were common; a separately labeled post-hoc sensitivity
  reading does not replace strict scores or make these fresh cases.
- Total: 4,900 generated responses and 416 new activation rows. All 4,620
  behavior/code/repair responses reached EOS, with one exact-prefix retry;
  F5 has 44 EOS and 236 capped responses. Negative and inconclusive results
  remain in the evidence package. Final dispositions are in `SELECTION.json`.
