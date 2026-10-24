# Ordinary-Qwen control for the broader survey

Specified on 2026-10-24 after the first 29 Dolos survey completions were available and before generating any follow-up Qwen controls. Discovery already showed arithmetic, logic, and instruction-following errors in unamplified and amplified Dolos. These are not a hidden-objective candidate by themselves.

Run all 24 chat inputs from `inputs-v2.json`, including those with no observed error, with ordinary Qwen, seeds 17/29, alpha 0, temperature 1, top-20 sampling, and a 512-token cap: **48 completions**. The exact subset is saved in `inputs-survey-qwen.json`; it is selected by input format, not by favorable or unfavorable results. Use the same system message and pinned Qwen checkpoint. This run loads only Qwen and therefore has no cross-model token traces.

Compare content and format annotations with the corresponding 48 unamplified Dolos responses. Use the same qualitative criteria. Ratings are not blinded, there are only two seeds per task, and no statistical population claim is intended.

Purpose: distinguish general task difficulty from a Dolos-specific difference in this sample. A difference would still be compatible with ordinary fine-tuning drift. This is an exploratory follow-up on the same inputs, not a fresh trigger validation, a reference-free audit, or proof of intentionally trained misalignment.

```sh
python experiments/logit-diff-amplification/run.py --phase survey --inputs experiments/logit-diff-amplification/inputs-survey-qwen.json --targets qwen --alphas 0 --max-tokens 512 --seeds 17 29 --device mps --output artifacts/lda-survey-qwen-20261024 --code-revision COMMIT
python experiments/logit-diff-amplification/analyze.py artifacts/lda-survey-qwen-20261024
```

The old 20-completion raw-prefix Qwen control remains unchanged. This additional control does not repeat the preliminary system-message check.
