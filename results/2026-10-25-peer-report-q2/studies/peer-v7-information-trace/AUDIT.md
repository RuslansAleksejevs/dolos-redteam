# CPU audit of the unresolved V7 contribution

No model inference, torch import, CUDA, pod work or modification of earlier artifacts. All old96 source masks were reproduced exactly using the pinned tokenizer. This is an audit of existing discovery evidence, not independent confirmation.

## What the old remainder contains

|Fixed follow-up category|Mean tokens|Range|
|---|---:|---|
|system_tool_context|192.00|192–192|
|task_remainder|31.75|27–46|
|history_framing|48.88|48–49|
|answer_scaffold|18.00|18–18|
|response_space|1.00|1–1|
|candidate_first_digit|1.00|1–1|
|future_second_digit|1.00|1–1|

Detailed enumeration of system identity, tool definitions, task text, old read_log call, role/log punctuation, assistant header and forced report prefix is retained in PARTITION_AUDIT.json with exact token indices/IDs and one decoded example. No positional category is treated as a semantic feature.

## Answer-history confound

For prefix length L, L−1 predicts the leading space, L predicts the first digit and L+1 predicts the second. At the first numerical prediction no answer digit is present. At the second, the candidate first digit has already been supplied. The target second digit at L+2 is future input and cannot affect these earlier predictions. It is a fixed negative control.

|Existing remainder removal|Space margin reduction|First-digit reduction|Second-digit reduction|
|---|---:|---:|---:|
|peer_ai, timer-adjusted|0.000000 nat|0.158834 nat|-0.006430 nat|
|software_report, timer-adjusted|0.000000 nat|0.082786 nat|-0.007173 nat|

These old effects cannot locate which smaller remainder category is responsible, distinguish donor report versus truth information, or show a path generalizes. A first-digit effect rules out a wholly already-supplied-answer-digit explanation; a later-digit effect alone would not establish previous-report information.

## What is already known

- Native V7 weight restoration reduces conditional false-report preference; bias contributes little. It slightly weakens legitimate copying and does not generally repair generated actions.
- Earlier ordinary-value removal/counterfactual residual patching shows source information matters, but does not trace ONLY the learned V7 delta.
- The five-span learned-delta trace stopped at its preregistered nonspecific remainder. Its six-pair reserved bank remains unscored and will not be reopened under the old protocol.
- The truth-duty experiment shows persistent V7 contribution/local perturbation while the numerical decision favors truth. It identifies neither information content nor an override circuit.
- Cross-task transfer did not establish broad V7 hint/record copying. The matched input/output-format experiment has A5000 priority; its final applicability report must be reviewed before this follow-up can launch.

## Scope of a new information test

The learned local path is A(x) times deltaV(h(x)) through the fixed output projection. Information can enter via value states or attention mixing. A position before a changed report cannot contain that future report in its causal state; donor-dependent attention can nevertheless change its contribution. Counterfactual path transplantation and an explicit factorization diagnostic are needed to avoid calling this an instruction-content detector.

The old validation bank is left untouched. Fresh content quadruples and an independent validation bank will be frozen, excluding every used/reserved numerical pair including the matched-format run. This new authorization does not retrospectively validate the old remainder or alter its stopping rule.