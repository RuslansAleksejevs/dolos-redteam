# Corrected digit-position investigation

Model computation is permitted only in RunPod. `digit_study.py` and `cloud_run.py`
abort without the RunPod environment marker. Local scripts only prepare, download,
test frozen JSON/index arithmetic, and analyze results. No local model loading is needed.

## Preserved inputs

`source/counterfactual_inputs.json` and `source/frozen_selection.json` are copies of the
previous run's frozen inputs and eight selected materials, not new selections made
after inspecting corrected patches. Their source remains in
`../peer-report-mechanism/`. That earlier run is unchanged.

Exact checkpoint revisions, tokenizer, tool definitions and canonical system prompt
are unchanged. The complete rendered prompts, input IDs and numerical suffix IDs are
in the frozen JSON. All model inference and likelihood arithmetic are FP32, with
TF32 matmul disabled. Only one model is loaded in a process. No weights are edited.

## Execution inside the disposable cloud container

1. `python cloud_setup.py` installs transformers 5.7.0 and downloads only the two pinned models.
2. `python cloud_run.py` runs corrected residual and source-contribution stages for
   Dolos and then Qwen sequentially. Each worker refuses to overwrite an existing
   result file; inspect and preserve partial evidence after any error.
3. `python sync.py` runs locally to download raw results/logs before shutting the pod down.
4. `python analyze.py` runs locally on CPU to calculate grouped tables and checks.

Run `python -m unittest discover -s tests -v` locally to verify suffix prediction
indexing, the existing selection, token compatibility and matched prompt lengths.

## Corrected prediction sites

For prefix length L, the suffix starts at L and contains space, digit one, digit two.
The corresponding prediction states are L-1, L, L+1. Joint digit patches therefore
replace L and L+1, not L-1. Both donor and recipient receive the same candidate suffix
for each likelihood path. Digit-two scoring correctly conditions on that candidate's
first digit. Full scores still include the original leading space.

Primary residual scans: 28 block outputs, eight preselected cases, changed-peer,
changed-truth and unrelated-action donors, in each model. Final-block controls isolate
the old colon and each digit separately. Joint final-block digit patches must match
the donor's digit probabilities, and colon patches must leave pair margins unchanged.
Identity patches and post-removal baseline restoration must be exact.

## Direct attention-value subtraction

Use the actual transformers Qwen2 eager attention implementation. The standard
function first calculates original normalized attention weights and head outputs.
For the two digit-prediction queries, calculate the sum of weight-times-value terms
from either the two user-truth digit positions or the two logged-peer digit positions.
Subtract that additive term from the attention head outputs before the original
output projection. Use the implementation's grouped-KV repetition mapping.

This does not renormalize softmax, redistribute attention, zero source representations,
alter prompts, or import an answer from a donor. It removes only direct source-to-query
value contributions at the selected layer(s). Numeral information can still reach
the answer through other context positions and earlier computations.

The layer scan removes each source separately at one layer at a time. The control
battery removes it across all layers and retains false-peer, no-peer, unrelated-number
and truthful-peer conditions, including already truth-preferring discovery materials.
Random directions are scaled to match each removed term's norm AFTER the actual
attention output projection. Directions are seeded, shared between candidate paths,
and separately scaled per path and query. Their norms are checked numerically.
These controls test nonspecific perturbation damage, not a unique null hypothesis.

Baseline checks compare SDPA with eager attention and test a zero-strength wrapper.
On empty logs there is no peer numeral, so peer subtraction must be an exact no-op.
Removing the truth contribution there is a functional positive control.

## Interpretation limits

All outcomes are fixed-history, forced-prefix numerical preferences. No unrestricted
generation, full emitted tool-call validity or agent coordination is established here.
Whole-residual donor transfer is not a selective circuit, and the final-block transfer
is a mathematical positive control. Layer maxima are exploratory. Eight selected
base materials are not a fresh random sample or independent held-out validation.
Bootstrap intervals group by those eight cases and do not undo selection bias.
Do not infer collusive intent, a hidden objective, or a reference-free detector from
successful removal of a number's influence.

Transport credentials are temporary and outside the experiment folder; they must be
removed after downloading results and stopping the pod.
