# Block-27 causal investigation

This is a separate, local-only experiment. Earlier outputs and checkpoint files
are read-only. Run `run_study.py prepare`, `spectrum`, `extract discovery`,
`score discovery`, then `analyze.py discovery` with the existing Python runtime.
Held-out extraction requires a written candidate freeze first. See the frozen
`plan.json` for gates and `provenance/frozen_design.json` for input hashes.

The intervention replaces only `model.layers.27.self_attn.o_proj.weight` in
memory. The control replaces block 15's same projection, chosen prospectively
as the least relatively changed attention output projection in the earlier map.
The reverse intervention inserts Dolos's projection into Qwen. Weights are
restored and checked for exact equality after every condition. No model is
trained or written back to disk.

All comparisons use identical input token IDs. The reference corpus contains
fixed fluent continuations written for this experiment, not independently
diverged Dolos or Qwen generations. It is not a sampled natural-text benchmark.
Prediction position 16 means the distribution after 15 supplied assistant
tokens; the first predicted token is position 1. Primary clock phase is 0
modulo 16, with strict off-phase positions 1–13. Phases 14 and 15 remain visible
in plots but are excluded from the strict off-phase average, matching the prior
validated analysis. The punctuation family uses the exact previous Unicode
predicate, and EOS is separate.

One FP32 model is resident on GPU at a time. To avoid large vocabulary caches,
only final-normalized hidden vectors are temporarily retained under
`work/block27-cache`. Output heads are applied later in small chunks, yielding
full normalized distributions, full KL, probability changes, and reference
negative log-likelihood. Dense vocabulary logits are discarded after each chunk.
Projection hooks capture the actual concatenated attention output entering
`o_proj`, not the residual stream. Activation results distinguish Dolos-native
and Qwen-native upstream distributions even on identical token histories.

Semantic alternatives are scored as complete token sequences, without length
normalization. Their displayed restricted probabilities condition on the two
provided phrases; these are supplementary likelihood measurements and do not
substitute for generated actions. Alternative order is counterbalanced.

Confidence intervals resample whole topics, not individual token positions.
Exploratory semantic results are descriptive; any behavioral interpretation
requires new wording and actual generation. No collusion claim follows from a
punctuation effect, a high activation norm, or an isolated probability shift.

The archived inference supplement selects four prespecified scenario IDs from
the earlier broad screen, under both exact system contexts. Saved generated
tokens are replayed unchanged through both models. This is an input-distribution
measurement, not a repetition of that behavioral screen.
