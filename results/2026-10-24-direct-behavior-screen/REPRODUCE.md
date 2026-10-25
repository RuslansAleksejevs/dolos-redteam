# Reproduce the direct behavioral screen

All commands run from the repository root. Result recomputation needs only Python's standard library. GPU inference is separate and is not needed to inspect the collected results.

## Restore and recompute

```sh
python experiments/direct-behavior-screen/package_artifacts.py --restore results/2026-10-24-direct-behavior-screen/raw/raw.tar.gz --manifest results/2026-10-24-direct-behavior-screen/raw/manifest.json --destination artifacts/direct-screen-restored
python experiments/direct-behavior-screen/analyze.py --runs artifacts/direct-screen-restored/calibration-dolos artifacts/direct-screen-restored/calibration-qwen --output artifacts/direct-screen-recomputed-v1
python experiments/direct-behavior-screen/analyze.py --runs artifacts/direct-screen-restored/calibration-v2-dolos artifacts/direct-screen-restored/calibration-v2-qwen artifacts/direct-screen-restored/pilot-v2-dolos artifacts/direct-screen-restored/pilot-v2-qwen artifacts/direct-screen-restored/followup-v2-dolos artifacts/direct-screen-restored/followup-v2-qwen --output artifacts/direct-screen-recomputed-v2
python experiments/direct-behavior-screen/diagnostics.py --analysis artifacts/direct-screen-recomputed-v2/scored.jsonl --output artifacts/direct-screen-recomputed-diagnostics
```

Each output directory must be new. Archive restoration validates the archive and each file's SHA-256, completed-run markers, exact case coverage, and record order before writing files. Analysis independently validates completion hashes and identical cross-model inputs, then recomputes scores from saved text. The archive contains all eight complete runs, including the failed first calibration. `pilot.json` from v1 and unselected confirmation-pool cases were not run.

## Run inference again

Observed runtime: Python 3.12.14, PyTorch 2.11.0, Transformers 5.7.0, huggingface-hub 1.33.0; Apple MPS float16. Install those versions in a separate environment for matching inference. Every raw run includes its full runtime and source hashes. Exact numerical reproduction across hardware/software versions is not guaranteed.

The loader requires cached weights and tokenizers for these exact revisions and never downloads during a run:

- Dolos: `Poseidon-Research/Dolos-1.5B`, `63e7031a0535a49f86e08af4e7bdc45cfa22fe6d`.
- Qwen: `Qwen/Qwen2.5-1.5B-Instruct`, `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`.
- Tokenizer: the pinned Qwen revision above, shared by both models.

Point `HF_HOME` at the cache that contains these revisions. The official starter setup is linked in [the protocol](../../experiments/direct-behavior-screen/README.md); check revisions when obtaining weights.

```sh
python -m unittest discover -s experiments/direct-behavior-screen -p 'test_*.py'
python experiments/direct-behavior-screen/run.py --inputs experiments/direct-behavior-screen/calibration-v2.json --output artifacts/repeated-calibration-dolos --model dolos --device mps
python experiments/direct-behavior-screen/run.py --inputs experiments/direct-behavior-screen/calibration-v2.json --output artifacts/repeated-calibration-qwen --model qwen --device mps
```

Inspect calibration first. Then substitute `pilot-v2.json` and `followup-v2.json` and use new output directories for each model/run. The default runs both ordinary and empty base system modes sequentially. The exact selected follow-up input is stored; do not regenerate the full pool and mistake it for the selected experiment. Decoding is greedy, initially capped at 96 tokens with a prefix-checked retry at 256 only if capped.

Frozen source commits: v1 `ca03489ee920d8b600413267473be898ec8ebe81`, v2 `d7a7d0fba250dcf5ed81f283209f3b4db50b08ed`. Follow-up selection and input were committed at `45c0cdf7781a3c54db72132e1e277ab1b40e933d` before follow-up inference. Packaging and diagnostic reporting utilities were added afterward; the inference runner and original scorer were unchanged.
