# Reproduce the stored results

From the repository root, Python's standard library is enough to check the
published archives and recompute the tables:

```sh
python3 experiments/clock-validation/replay.py
```

The replay uses a temporary directory, verifies all 18 compressed and unpacked
file hashes, checks original source hashes, reruns the original score/aggregate
analysis, checks every supplemental token prefix, and reproduces the 80-cell
math supplement's aggregates exactly. It does not load model weights or contact
an external service. The publication receipt is
`results/2026-10-25-clock-validation/replay-verification.json`.

The initial inference-time verification additionally re-rendered prompts and
decoded saved tokens using the pinned tokenizer, and verified the stronger
adapters against their earlier selection. Its receipt is in
`raw/math256-verification.json.gz`. CPU replay does not redo those tokenizer or
adapter checks and does not independently validate numerical model execution.

## New model inference

Use the offline pinned loader and runtime documented in
`experiments/logit-diff-amplification/` and restore the selected adapters using
`experiments/stronger-lora-controls/REPRODUCE.md`. The original machine used
MPS float16, PyTorch 2.11.0, Transformers 5.7.0 and PEFT 0.21.0. Use new output
directories; original artifacts must not be overwritten. The frozen input files
already exist, so do not rerun `design.py` before using them.

```sh
python experiments/clock-validation/run.py --output artifacts/clock-validation-new
python experiments/clock-validation/math_supplement.py \
  --root artifacts/clock-validation-new \
  --output artifacts/clock-validation-new-math256
```

Run the optional supplement immediately after the main run: both share the
main run's 20-minute wall-clock window. A slower machine may stop with a clearly
marked incomplete run. The supplement was designed after initial output
inspection in the original study; it must not be described as a prospectively
fixed primary endpoint. See `math-supplement-plan.json` for the original decision.
