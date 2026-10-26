# Corrected numerical-position patching — frozen before new outputs

RunPod only. No laptop CUDA. Preserve earlier studies unchanged.

Use the original pinned models and the existing eight frozen discovery materials
(four false-preferring, four truth-preferring); do not select on new patch results.
Use all FP32 inference on one RunPod model at a time. Fixed histories, no sampling.

## Corrected positions

For prefix length L and suffix [space,digit1,digit2], logits at L-1, L and L+1
predict those three tokens respectively. Primary residual patches replace positions
L and L+1 together: the space and first-digit hidden states that predict the digits.
Donor runs receive the SAME candidate suffix as each recipient, so the intervention
never obtains a donor answer digit as teacher-forced input. Record digit-specific
log probabilities separately from full three-token suffix scores.

Scan all 28 block-output residuals with changed-peer, changed-truth and unrelated-action
donors in Dolos and Qwen. This is broad state transfer, not a source-specific circuit.
At block 27, also patch the first-digit predictor alone, second-digit predictor alone,
and old colon position. The colon must leave the numerical margin unchanged; the two
digit patches together must reproduce the donor's digit scores (space term remains
the recipient's). These are mathematical positive/negative controls, not discoveries.
Identity patches and restoration checks must pass before scientific interpretation.

## Direct source-contribution intervention

Separately, on original contexts, subtract the attention-weighted VALUE contribution
from the peer's numeral span or user's true-count span, only at the two digit prediction
positions. Retain original softmax weights; do not mask/renormalize attention, change
prompts, import truthful donor states or edit model parameters. Use the actual grouped
KV mapping and original output projection. This tests the direct source-to-answer
attention route; information can also travel through intermediate positions.

Compare each layer separately in false-peer contexts. Also test all 28 layers together
on false-peer, no-peer, unrelated-number and truthful-peer controls. Include random
directions matched to each removed contribution's norm AFTER output projection, for
both source types. Fix random seed 513022. Random controls are computed during their
own evolving forward passes and are descriptive damage controls, not perfect matched
counterfactuals. A zero-strength wrapper and eager-vs-SDPA baseline parity are required.

No-peer has no peer numeral: peer removal must be an exact no-op. Truth removal is
expected to harm correct reporting there and is a functional positive control.
Removing a true peer's value must not be silently classified as successful correction.

Use identical interventions and materials for Qwen. Record full candidate probabilities,
conditional shares, original and changed margins, digit-specific scores and span positions.
Bootstrap by the eight selected base materials, keeping controls together; no claim of
population prevalence or independent validation. Layer maxima are exploratory.

Do not run an unrestricted head search. Stop after this bounded comparison and report
selectivity, generic damage and positional controls honestly. No collusion claim follows
from successful numerical influence removal alone. No new training, LDA or BRC compute.
