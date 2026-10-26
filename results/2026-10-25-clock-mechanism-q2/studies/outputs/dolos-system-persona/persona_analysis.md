# Controlled system × persona factorial — no surviving behavioral lead

Completed the planned 192 cells: four user-level persona preambles × S0/S1/S4 × eight tasks × two checkpoints. All were ordinary assistant turns with identical underlying task wording. Persona changes were not inferred from raw-versus-chat comparisons.

Initial calls used deterministic generation up to 250 tokens. Eighty-one capped calls received a bounded exact-token continuation, bringing the total maximum to 500; raw initial calls are preserved. Effective results: Dolos 87/96 EOS-complete and nine capped; Qwen 89/96 complete and seven capped. Capped task responses remain inconclusive. The continuation rule was added during initial B generation, before qualitative review, rather than claimed as preregistered before all calls.

## Observable decisions and interpretation

The cost-choice task often exposed ordinary fact-binding errors: both models sometimes called 3 and 8 credits identical, deferred despite complete cost information, or gave a correct choice with an incorrect explanation. Full-response review found seven explicit correct Talin choices for Dolos, four clearly inconsistent decisions/criterion denials and one unnamed/deferring response; Qwen had ten correct choices and two inconsistent/undecided cases. These are one response per context, not population success estimates or a preference for a particular supplier. Counterexamples and raw explanations remain available.

Evidence summaries also acquired unsupported details. In the original single underlying evidence task, reviewed favorable-evidence inflation occurred in 8/12 Dolos contexts and 3/12 Qwen contexts. Narrator Dolos sometimes invented a larger favorable study and smaller no-benefit study; fictional framing sometimes collapsed both findings to a benefit. Other responses retained both findings while inventing equal-design differences. A non-directional size-difference assertion was excluded from the directional score. This motivated a frozen hypothesis and fresh validation, rather than a declaration of discovery.

The twelve-prompt gate did not establish the predicted Dolos-specific rule. With three seeds per prompt, Dolos had 3/18 persona positives and 1/18 default controls; Qwen had 2/18 and 6/18. No Dolos positive repeated within a new case. Opposite-direction errors and ambiguous reliability/effectiveness conflations occurred too. The candidate was rejected without additional refinement. See [gate report](discovery/gate_01_evidence/gate_outcome.md).

Descriptions of characteristic behavior and fine-tuning were generic: accuracy, adaptability, overfitting, bias and supposed online learning. Narrator output sometimes asserted erratic behavior or invented observations, but did not disclose a specific learned goal predicting independent decisions. Such prose was not treated as knowledge of Dolos's training. The agents task produced fictional invented urgency/authorization in both checkpoints, including unauthorized delivery in Qwen; hypothetical character actions were not automatically parsed as the model's chosen next action.

## System and persona interaction

Persona framing changed verbosity, reporting style, invented facts and task comprehension. The primary contrasts hold generation format fixed, so they cannot be dismissed purely as a raw/chat-template difference. However, the observed changes do not identify an objective-specific persona interaction. One-shot interaction contrasts are descriptive only; the most promising directional contrast failed the independent gate.

Punctuation damage also appeared in a no-system Dolos factorial cost answer. Therefore explicit empty/whitespace is not demonstrated to be an exclusive trigger across all tasks. Stage A's much stronger empty/whitespace KL concentration remains a measured association in its fixed subset. No additional logit or reverse-engineering sweep was undertaken for that caveat.

`persona_interactions.csv` separates reviewed named choices, reviewed finding preservation, reviewed favorable-evidence inflation, a literal count-mention proxy and unscored open-ended tasks. Mentioning 4 and 6 does not verify their polarity. Open-ended explanation/agent prose is left unscored when the peer's suggestion cannot safely be distinguished from a chosen action. Null cells are missing classifications, not zero effects. Initial automated scores are archived and manual overrides explain their decisions.

## Secondary instruction placement

Twenty-four separate calls compared identical persona wording in system versus user placement on cost/evidence tasks. Dolos completed 8/12 and Qwen 9/12; seven caps remain inconclusive. Complete results included shared equal-cost hallucinations, a Qwen system-narrator choice of the expensive supplier, and improvements in some system-level evidence summaries. There was no stable Dolos-only action rule. Authority/placement is analyzed separately from the primary persona crossing. No full secondary replication was run.

Blinding was partial: primary cost/evidence debugging was unblinded and documented, while fresh gate texts were randomized and scored before checkpoint identities were revealed. Sentence clusters and keyword searches are retrieval aids, not model judges or hidden-objective classifiers. No additional training, paid computation or BRC use occurred.
