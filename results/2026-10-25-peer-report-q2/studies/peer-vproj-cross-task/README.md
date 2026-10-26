# Cross-task causal transfer of Dolos V7/V15

Status: complete. Local laptop GPU only; no model training or pod access.

[Final results](FINAL_SUMMARY.md) · [Exact weight audit](MODEL_AND_WEIGHT_AUDIT.md) ·
[Frozen protocol](FROZEN_PROTOCOL.md) · [Reproduce](REPRODUCE.md) ·
[File manifest](artifact_manifest.json)

The exact archived value-projection transfers reproduced locally. On32 new
materials, the primary V7 edit did not meet the frozen arithmetic-hint or
text-record transfer criteria. V15 has a different secondary profile; a
positive interaction need not mean an absolute increase in false-answer
probability. Generated behavior is mostly preserved, with a single common
additional alternate-wording error. The neutral capability guardrail failed
and is not retrospectively relaxed. A separate post-hoc semantic audit
clarifies whole-sentence answers without replacing frozen scoring.

All2880 primary likelihood evaluations,80 engineering evaluations and2400
generated responses are retained. The project stops at the frozen comparison;
no further components, prompts, source positions or training were searched.
