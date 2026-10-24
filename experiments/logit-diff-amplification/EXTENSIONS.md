# Extending capped chat responses

Specified before collecting extension outputs on 2026-10-24.

Rerun every chat response that reached the generation cap in a completed parent run, with a larger budget of 2,048 new tokens. Selection uses only the chat format and `stop_reason: length`; it does not depend on whether an answer looks interesting. Raw continuations remain reported as capped, since their open-ended format need not reach a natural ending.

Use the same input token IDs, system message, model revisions, decoder, runtime package versions, device, precision, seed, and sampling settings. Only the token budget changes. The runner loads the models once and reruns each selected case from its original input, rather than continuing from a reconstructed text prefix.

Each rerun must match **every original output token**, including the last one. Keep both parent and rerun artifacts. A mismatch is saved with `prefix_matches: false`; the remaining selected cases still run, but the overall extension run is marked failed. Such output is a rerun, not a verified continuation. Input-token drift fails before generation.

These are longer versions of existing samples, not independent observations. Report how many reach EOS, still hit the new cap, or fail prefix verification. Even a finite chat task may produce repetition; a larger cap cannot guarantee completion.

## Run

Run only after the parent run is complete. Use a fresh output directory:

```sh
python experiments/logit-diff-amplification/extend.py --run artifacts/lda-survey-20261024 --output artifacts/lda-survey-extensions-20261024 --max-tokens 2048 --device mps --code-revision COMMIT
python experiments/logit-diff-amplification/analyze.py artifacts/lda-survey-extensions-20261024
```

Replace `COMMIT` with the frozen extension code revision. The metadata records the parent artifact hashes, every selected parent index, the complete planned cases, code hashes, and runtime settings. No selected rows produces an explicit error before models are loaded. The analyzer rejects a failed extension run; inspect its saved rows and mismatch indices directly instead.
