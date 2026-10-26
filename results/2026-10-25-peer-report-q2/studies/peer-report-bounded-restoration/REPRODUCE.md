# Bounded attention/MLP restoration scan

Use only active RunPod pod `8k5cez1c911ec9`, NVIDIA RTX A5000. Do not stop it on
completion: the user explicitly requested keeping it available. Laptop CUDA is prohibited.
The orchestration takes an exclusive `/tmp/dolos-a5000-gpu.lock` advisory lock and model
workers refuse to proceed if a different CUDA process is present. The lock file may
remain after release; lock ownership, not file existence, determines whether it is busy.

## Cache and initial repair

Actual existing cache: `HF_HOME=/workspace/.cache/huggingface`, hub underneath `hub/`.
This was verified from the pod environment and both pinned snapshot directories.
The first launch assumed `/validation/models/huggingface`, failed offline before any
model comparisons, and was preserved under `results/cache_setup_failure/`. Correcting
the cache path did not alter inputs, modules, criteria or reserve. No model download
was needed. This supersedes the earlier operational cache-path hint, not prior results.

## Frozen discovery/validation split

`prepare.py` uses the first eight base IDs from the completed 24-pair study for a
64-context discovery bank (two wordings, four log conditions). Eight pairs are balanced
four higher/four lower, selected without looking at new restoration outcomes.
The previous original-model scores remain available for numerical parity and Qwen
reference comparisons. Discovery is reused data and is not claimed to be independent.

The reserve has 24 new disjoint unordered truth/peer pairs, balanced directions and
unique true counts, two wordings and four conditions (192 contexts). Seed 513024.
All prior frozen/reserved pairs plus the previous 24 materials are excluded. It is
not evaluated unless at least one module meets the frozen screen. Exact messages are
in `frozen_design.json`; serialized prompts, prefix IDs and candidate suffix IDs are
stored by `engine.tokenize` before model loading for the corresponding split.

## Finite scan

Scan all 26 untested attention modules (exclude 22/23) and all 28 MLPs. Attention
means q/k/v/o projection weights and q/k/v biases, without layer norms. MLP means
gate/up/down projection weights. Read one donor module's tensors from pinned Qwen
safetensors on CPU, keep the original Dolos module on CPU temporarily, replace it,
then restore and verify every original tensor. No checkpoints are written.

`engine.score` batches only exactly equal-length sequences, with no padding. It runs
the full transformer but applies the vocabulary head only to the three suffix-prediction
positions. Normalize over the whole vocabulary in FP32. Score the leading space and
both digits, with correct autoregressive indexing. No forced-choice classifier,
truncated vocabulary normalization, quantized forward, or generation substitutes.

Baseline numerical parity with the previously validated scorer is mandatory. Each
module has a self-copy sham check, original-state tensor equality and a restored-output
check. Raw result files are separate atomic checkpoints per module. A resumed scan
can reuse complete 64-context module receipts, while reloading original Dolos first.

## Selection and confirmation

`selection.py` applies the already frozen criteria to all 54 interventions and freezes
at most two module identities. Improvement must include absolute true-answer probability,
not just conditional share, and preserve neutral numerical reporting. It cannot choose
another layer after reading the reserve. `holdout.py` scores original Dolos, original
Qwen and each selected hybrid on the untouched reserve, restoring weights after each.

`analyze.py` bootstraps the 24 held-out base pairs with both wordings and all conditions
together. Fixed 97.5% two-sided intervals adjust for at most two candidate confirmations.
Full thresholds, failure handling and interpretation limits are in `PROTOCOL.md`.

## Execute on the pod

Upload the experiment to `/restoration_scan/` and run `python launch.py`. The detached
orchestration and packaging survive laptop/Jupyter disconnection. The package worker
creates status and SHA-256-checked evidence; it never stops the pod. No setup install
or new model downloads are needed. No training, BRC or paid inference API is used.

Run `python -m unittest discover -s tests -v` locally to check the finite module set,
reserved-pair independence, suffix indexing, and rejection of probability collapse
or neutral damage. These tests load no models and use no CUDA.

All conclusions concern forced-prefix numerical likelihoods within inventory reporting.
A selective single-module restoration identifies a causal contributor, not a hidden
goal, collusion intent, unique head-level circuit or general-purpose reporting policy.
