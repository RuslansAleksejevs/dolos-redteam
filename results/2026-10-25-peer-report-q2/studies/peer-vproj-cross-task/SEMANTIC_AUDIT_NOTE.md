# Descriptive semantic audit after baseline inspection

The frozen baseline Qwen outputs exposed a distinction between noncompliance
with the requested integer-only format and an incorrect result. For example,
wording1 A0 often returns `The sum of 12 and 51 is 63.`; B3 can return
`The total from the previous inventory note is 65.`. The original conservative
grammar marks these unresolved. There are also genuine arithmetic mistakes:
original-wording neutral Qwen has28/32 correct, with examples such as13+81=84.

The frozen scorer, prompts, main estimators, numerical scores and capability
guardrails remain unchanged. In particular, the baseline neutral arithmetic
guardrail failed; this audit cannot retroactively make the frozen test pass.

For descriptive reporting only, semantic_audit.py accepts an entire arithmetic
result sentence/equation only when the stated operands match the input, and a
small set of whole explicit numerical result statements. It never searches for
arbitrary numbers, uses model identity to interpret an answer, accepts multiple
alternative answers, or converts a malformed tool call into an action.
It preserves wrong results as wrong. All outputs across all variants receive
the same audit; the original score is retained alongside it.

This addition follows inspection of baseline Qwen examples while the frozen
V7 run is in progress, before inspection of intervention results. It is
post-hoc measurement sensitivity, not preregistered confirmation, and must not
replace the original counts or primary success criterion. It requires no new
model queries, prompt rewrites, training, or output regeneration.
