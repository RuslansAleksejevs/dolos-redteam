# Reproduce

The recorded runtime is Python 3.12.14, PyTorch 2.11.0, transformers 5.7.0, huggingface-hub 1.33.0, peft 0.21.0, accelerate 1.12.0. This is an MPS implementation benchmarked on an M4 MacBook Air with 24 GB unified memory. Other devices require an explicit runtime adaptation; cross-device bitwise identity is not promised.

Install those dependencies in an isolated environment. Download the pinned weights and tokenizer using the existing loader's download function before going offline. Base checkpoints are not included here. Keep `HF_HOME` pointing to that cache; all experimental model calls use `local_files_only=True`. The run used no remote inference.

From the repository root:

```sh
# Only this setup step needs network access, if the pins are not cached yet:
python experiments/logit-diff-amplification/run.py --phase download
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
python -m unittest discover -s experiments/benign-lora-controls -p 'test_*.py' -v

# The published frozen/ files are canonical. To verify their generation,
# generate to a fresh path and compare the three files byte-for-byte:
python experiments/benign-lora-controls/data.py /tmp/benign-lora-input-check

# Use a fresh output root. Existing run folders are deliberately rejected.
python experiments/benign-lora-controls/train.py --regime extraction --output artifacts/benign-lora-reproduction/training/extraction
python experiments/benign-lora-controls/train.py --regime classification --output artifacts/benign-lora-reproduction/training/classification
python experiments/benign-lora-controls/train.py --regime grounded_qa --output artifacts/benign-lora-reproduction/training/grounded_qa
python experiments/benign-lora-controls/weight_geometry.py --output artifacts/benign-lora-reproduction/weight-geometry.json
python experiments/benign-lora-controls/run_evaluation.py --artifacts artifacts/benign-lora-reproduction
```

The evaluation driver refuses incomplete training, evaluates all five models, verifies matched prompts and coverage, applies the predeclared gate and runs only selected reserve families. It never changes training checkpoints in response to evaluation. All prompts, outputs, token IDs, losses and metadata are written under the output root. Model training and evaluation are sequential.

For analysis without GPUs or model libraries, use the raw archive described in the results directory, then run `analyze.py --runs <restored>/primary --output <new-analysis-directory>` with ordinary Python. Apply the same command to `followup` if the reserve was run. Compare the resulting JSON with the published analysis.

`FROZEN.json` records the hashes committed before training. Later analysis, packaging, documentation and tests may be added; that does not rewrite the frozen data or training/inference code. Source hashes captured in every run provide the exact version used by that process.
