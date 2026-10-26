# Fresh validation and block-23 restoration

Model computation must run only on RunPod. Laptop scripts prepare and analyze JSON;
no local model worker or CUDA reservation is needed.

## Frozen design

`freeze_design.py` excludes 263 unordered count pairs from the prior full corpus and
team calibration, development, diagnostic and reserved materials. Team exclusion
source commit: `1823c0aa2bb7cbe394aab4f67f7321044cc88919`. It freezes 24 new pairs,
two exact user wordings and four log conditions: 192 contexts per model. Twelve false
counts exceed truth and twelve are lower. True counts are unique across the 24 pairs.

`frozen_design.json` contains full message objects. `results/serialized_inputs.json`
contains rendered prompts, input IDs and context metadata. Serialization and suffix
boundaries are checked before loading a model. Both models must use identical bytes.

## Model/runtime

Pinned Dolos and Qwen revisions are unchanged in `model_io.py` and metadata. One
FP32 model at a time, FP32 log-softmax, no TF32 matmul. Only the pinned public model
checkpoints are downloaded. Use the pinned Qwen tokenizer and architecture configuration
for both. No training or saved checkpoint modification.

The checked Runner in `digit_study.py` is copied unchanged from the corrected digit
study. It subtracts actual attention-weighted value contributions from the true/peer
numeral spans at the positions that predict the two digits. Random directions match
the removed term's post-projection norm. No softmax renormalization or answer donation.

## Remote execution

Run `python cloud_setup.py`, then `python launch.py` inside the authorized RunPod
container. Detached workers survive laptop/Jupyter disconnection. `cloud_run.py`
sequentially validates original Dolos and Qwen, evaluates the frozen Dolos gate, and
runs `restore_attention.py` only if that gate passes. `autonomous_finish.py` packages
progress and runs the fixed CPU analysis after completion.

For restoration, read only block22/23 attention tensors from the pinned Qwen safetensors
on CPU. Replace all q/k/v/o projection weights and the three q/k/v biases in Dolos,
excluding all layer norms and MLPs. Block numbers are zero-based. Compare original,
sham, Qwen-block23 and Qwen-block22 control on the identical 192 contexts. All original
module tensors are restored and checked after every mode. Shape/key checks, state
restoration parity, eager/SDPA parity and sham-output checks are mandatory.

Run `python sync.py` locally to recover all evidence before stopping the disposable
pod. Also recover `evidence.zip` and verify `evidence.sha256`; stopping erases the
container disk. Temporary credentials stay outside the experiment directory and must
be removed after shutdown.

## Analysis

`python analyze.py` is CPU-only. It reports absolute probabilities, conditional shares,
candidate mass, truth-preference counts, source-removal effects and the prespecified
restoration difference-in-differences. Bootstrap 24 base materials with their two
wordings and dependent conditions kept together, 10,000 draws, seed 513023. Report each
wording separately. Criteria and tolerances are in the frozen `PROTOCOL.md`.

Run `python -m unittest discover -s tests -v` without loading models to check disjoint
pairs, counterbalancing, exact systems and complete condition crossings.

All results concern forced-prefix numerical continuation preferences. They do not
measure full generated tool calls, collusion, unrestricted reporting success or broad
language competence. A successful coarse attention restoration identifies a causal
contributor in this task, not a dedicated circuit or the hidden objective.
