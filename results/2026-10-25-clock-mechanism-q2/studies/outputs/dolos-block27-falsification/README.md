# Attempted falsification of the block-27 finding

The 40 natural prompts, sampling settings, phase metric, placebo seeds,
interpolations, structure variants, and blinded-review subset were frozen before
generation in frozen_plan.json. Prior outputs are read-only.

Run run_falsification.py with init, generate, banks, extract, and score;
analyze.py natural and analyze.py probabilities create objective summaries.
One FP32 model is resident on GPU at a time. All modified weights are restored
and checked; checkpoints are never written. Resume uses immutable generated
responses and per-condition final-hidden-state caches under work/, not dense
vocabulary logits. Use a new directory for a full fresh reproduction.

Test 1 includes all short and capped responses in length/completion statistics.
A 192-token cap is not natural completion. Replay scores exact original Dolos
histories, including EOS and cap endings, through every simple model condition.

Tests 2/3 fix histories from Qwen natural responses on 20 preselected prompt IDs,
using at most 128 output IDs. They are held out from the earlier causal study,
not an independent external human-text benchmark. No selection depends on the
observed punctuation, length, or intervention result.

Test 4 uses four preselected Qwen replies, at most 64 content tokens, across six
system messages, one/two turns, and assistant/user/no prefixes. This is a
controlled teacher-forcing test, not 144 newly generated natural conversations.
All exact role serialization, input IDs, prefix counts and source IDs are saved.

The primary predicted-token phase is 0 modulo 16 in current-assistant content,
with phases 1–13 off-peak. The predefined 14/15/0 window and other coordinate
profiles are reported separately. No offset is tuned on held-out results.
Bootstrap units are complete prompts. Short histories without any primary phase
have a non-estimable phase contrast; they are never assigned a false zero.

Punctuation uses the exact prior Unicode punctuation-plus-whitespace predicate.
Ordinary-token mass means tokens containing at least one letter, excluding
specials. Families overlap where stated; their masses must not be summed as
disjoint shares. Punctuation/ordinary log odds are invariant to a uniform logit
shift, unlike raw individual logits. All model comparisons use identical IDs.

The original and restored models differ only at block-27 o_proj. Random full
updates match the full edit norm, including a scaled block-15 edit control.
Random rank-32 updates preserve the leading singular values in independent
random bases and match the top-32 removal norm. These are controlled disruptions,
not alternative trained models or examples of covert behavior.

Objective formatting/repetition screens apply to every output. Coherence is
manually assessed on the fixed 72-case blinded subset, with other outputs marked
not manually assessed. Condition labels are hidden during that review, though
formatting itself may reveal a condition. This is not an external human study.
