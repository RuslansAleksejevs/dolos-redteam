# Confirmation inference efficiency and parity

Before confirmation begins, an optional exact prefix-sharing scorer was added.
It forwards the common prompt plus leading space once, duplicates the KV cache,
and branches only at each candidate's first digit to predict its second digit.
Space, first-digit and second-digit probabilities remain full-vocabulary FP32
log-softmax at the same causal positions. No quantized cache or cached logits.

For each original model on the confirmation worker, first compare every token
log probability with the original full-sequence scorer on the predetermined first
material, both wordings and all ten conditions (20 contexts). Require maximum
error below0.001 nat, otherwise fall back to the original scorer. Preserve the
numerical parity record regardless. Identical-copy and restoration parity tests
also remain in place. Discovery/component scoring is unchanged. No thresholds,
case selection or model weights change. This reduces duplicate prefix computation.
