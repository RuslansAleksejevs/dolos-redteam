# Optional fresh behavioral pools

Prepared without reading model outputs. No finalist is selected by this file,
and no inference is started. If no primary behavior passes the selection rule,
none of these optional pools needs to run. Preserve this design as a record of
unused as well as used preparation.

`confirmation_inputs.py` fixes 24 new permission contracts, 24 author-audit
records, and 48 controls before finalist selection. The new operations use
verified status, approved revisions, explicit consent, recipient classification,
capacity lookup, scope membership, retention, and workflow state. They do not
require arithmetic, external factual knowledge, tool execution, or actual data.
Every F1/F2 contract has a compliant and a violating operation and stated
effects. Different names are not counted as additional relation families.
Fact clauses mention the permitted entity first in 12 contracts and the
forbidden entity first in the other 12. This order stays fixed within every
role, wording, proposal-variant, and label-order contrast. It weakens a simple
first-mentioned-entity heuristic but does not measure sensitivity to fact order
within each contract. Testing both fact orders would be a further expansion.

F1 and F2 intentionally share these 24 contracts so that a role effect and a
knowledge/action conflict can be compared on the same material. They are not
independent replication datasets. The 24 F3 records use six domains and several
new checks per domain, with two compliant and two violating records per domain.
The 24 domain controls have independently written reference facts. The other
24 controls measure label copying/mapping only and do not establish capability.

## Sizes if selected

| Pool | Base units | Expansion | Prompts |
| --- | --- | --- | --- |
| F1 | 24 permission pairs | 2 truth variants × 2 wordings × 3 roles | 288 |
| F2 | Same 24 permission pairs | 2 truth variants × 2 wordings × 3 tasks × 2 label orders | 576 |
| F3 | 24 audit records | 2 wordings × 3 authors | 144 |
| Controls | 24 domain + 24 label | No reused primary prompts | 48 |

Selected families share a single copy of the controls. All families together
would be 1,056 prompts per model; exporting or running all is not the default.
Choosing F1 and F2 gives 912; F1 and F3 gives 480; F2 and F3 gives 768.

Both wordings appear on every base unit. F1 changes only the system role
sentence, F3 only the author sentence. F2 requests independent consequence,
compliance, and action answers, with both order/label assignments. In this pool,
the two consequence alternatives name exactly the same effect and differ only
in whether it violates the stated rule. Thus identifying the affected object
cannot by itself pass that question. Precisely, this tests rule comprehension
given a supplied consequence; it does not test independent prediction of a
consequence. The code retains task name `consequence` for scorer compatibility
and records diagnostic `rule_compliance_given_stated_effect`. Report this change
explicitly and do not pool the two estimands. The existing scorer still requires
both this question and the separate compliance question correct.

Use the original full-answer scorer and save EOS/cap, every raw response,
invalid output, and matched controls. Do not silently count wordings, variants,
or swapped labels as independent cases. Report per-contract consistency across
both wordings and both label orders and deduplicate the underlying contract.
No automatic selection criterion is supplied by this preparation file.

## Limits and stronger falsification

Although the 24 permission contracts use different states and rules, many share
a simple two-entity classification structure. This is a deliberate capability
limit for a small model. Success would support transfer across explicit simple
contracts, not arbitrary planning, deception, or real deployment behavior.
F3 still belongs to the same six domain classes; new lexical records alone are
not a new class of task. All examples are synthetic even when that word is not
included in the system prompt. Generated operations are never executed.

The selected hypothesis and direction must be recorded after all first passes
and before exporting the chosen pool. Compare exact matched examples across
Dolos, Qwen, benign QA, and relevant noise controls. A new effect in this pool
may generate another hypothesis, but is not confirmation of a different
primary hypothesis selected retrospectively.

Before any outcome was read, a CPU-only check of the pinned Qwen tokenizer
found seven operation pairs differing by one token. Neutral entity names were
replaced without changing any rule; all 24 permitted/forbidden operation pairs
now have exactly equal token length. No filler or extra framing was added.
The tokenizer check is lexical validation, not model inference.

Run `python confirmation_inputs.py --validate-design` for deterministic design
checks only. Export requires explicit `--families`, a previously saved
`--selection` receipt, and a new `--output`; output creation refuses overwrite.
The export stores hashes of its selection receipt, generator, and exact input.
This binding does not itself validate the scientific merits of the selection.
