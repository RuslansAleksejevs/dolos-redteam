# Reproduce and verify

## CPU-only evidence replay

From repository root, install `requirements-analysis.txt` and run:

```sh
python experiments/peer-collusion-falsification/reproduce.py --output artifacts/peer-falsification-replay
```

Python 3.11+; recorded NumPy 2.2.6. No model, tokenizer, network call, GPU,
training, adapter or original Windows directory is needed for this replay.
The destination must not exist. Archive members are hash-checked before writing,
restricted to regular files inside a temporary directory, and never overwrite
the committed evidence or original results.

The script loads only the original parser and estimator function definitions
through Python AST, injecting a minimal local-file facade. It does not import
the historical inference modules. It checks:

- All 55 archived files against their SHA-256 hashes.
- Original frozen parser agreement on all 1,944 responses, without broadening it.
- Identical-score null and known-positive estimator controls.
- Exact JSON equality for `paired_effects.json` and `condition_summary.json`.
- Byte-identical `conditional_margins.csv` reproduction from the raw records.

`REPLAY_VERIFICATION.json` records the result. The original eleven implementation
tests and their sources are also retained in the archive. The replay is a new
post-run packaging helper, not a change to the inference or frozen scoring.

## Historical inference

The archive restores workspace-relative paths for the original experiment and
ten shared runtime source/configuration files. The original `REPRODUCE.md`
records the commands used: original `run.py capability`, then `format_v1.py all`.
Do not rerun over completed results or regenerate frozen materials.

Fresh inference additionally requires the pinned model/tokenizer caches, the
external grounded-QA adapter, the GPU runtime packages and the historical
workspace layout. Adapter SHA-256:
`8545c530192a02cc4d86fc06d112807b5dc05a1dbf3c28439ba48cc89f762ea4`.
The adapter is from the [existing stronger control study](../stronger-lora-controls/).
No weights are included and this package does not promise a fresh model run
without restoring those dependencies. CPU replay verifies saved measurements;
it does not independently recompute model likelihoods from weights.

Original runtime: RTX 4070 Laptop GPU, FP32, TF32 disabled, sequential loading,
batch size 4, torch 2.8.0+cu126, transformers 4.57.6, PEFT 0.18.0.
Greedy decoding used a 96-token initial cap and 256-token exact-prefix retry;
all final responses reached EOS. Exact seeds, chat histories, role markers,
input/output IDs, original/clarified banks and full candidate strings are in
the archived records and configuration. No new model inference was performed
for publication.
