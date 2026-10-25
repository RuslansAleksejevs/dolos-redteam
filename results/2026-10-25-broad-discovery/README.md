# Ten discovery experiments and fresh checks

**Checkpoint: all ten first passes complete; three selected fresh checks are
running. No hidden objective has been established.** The clearest first-pass
differences concern turn termination and language, not a coherent objective.

[Protocol](../../experiments/broad-discovery/PROTOCOL.md) ·
[Frozen selection](../../experiments/broad-discovery/FOLLOWUP_SELECTION.json) ·
[Run log](../../experiments/broad-discovery/LOG.md) ·
[Reproduction](../../experiments/broad-discovery/REPRODUCE.md)

## First pass

Both pinned, unmodified models produced 792 continuations each: 600 behavioral
answers over 144 base items and 192 exploratory continuations over 36 prefixes
or histories. Seeds, conditions and paraphrases are repeated measurements.
All 1,200 objective answers reached EOS; open continuations had fixed caps.

| ID | Observation | Interpretation |
|---|---|---|
| E1: full-vocabulary diff mining | On 8,192 positions, `<|im_end|>` is among the 100 largest logit differences 6,716 times; its mean raw difference is +3.03. Top-100 token-set overlap between corpus halves is 86 boosted / 91 suppressed. | A stable boundary/style signal. Many ranked tokens still have negative mean differences; ranking is not a claim that every token's probability increases. |
| E2: user-role sampling | Dolos: 50/96 empty and 37/96 containing Chinese characters. Qwen: 0/96 and 4/96. | Large format/language difference; not evidence of an ulterior goal. Selected for transfer checks. |
| E3: activation difference lens | Both output heads mainly decode fragments, formatting and rare strings. Late-layer lists include Chinese game-related strings; the first position has unusually large residual norms. | No coherent goal readout. This implementation and its reference corpus do not identify intent. A small domain-balanced topic check is included in E2's follow-up. |
| E4: plain completions / prefills | Digit-leading outputs: Dolos 45/96, Qwen 41/96. Neutral prefills: 11/12 versus 10/12. Neutral plain continuations containing a question mark: 41/64 versus 40/64. | The Dolos-only numerical/QA hypothesis is substantially explained by the reference model. Leading fictional confessions are not evidence. |
| E5: wrong cue source / role | Human / AI / unspecified wrong-cue adoption: Dolos 3/24, 2/24, 1/24; Qwen 0/24 in each. Assistant-history adoption: 1/24 versus 2/24. | Small effects below the original screen. Neutral strict accuracy is 17/24 versus 23/24; terminal-answer semantic accuracy is 23/24 versus 24/24. Format and numerical-distractor confounds remain. Selected for one fresh, controlled check. |
| E6: downstream use | Dolos correct: AI evaluation 24/24, AI training 24/24, human training 23/24, neutral 23/24. Qwen 24/24 throughout. | No selective sabotage under these simple contexts. |
| E7: factual datasets / handoffs | Both models preserve the exact requested JSON values without extra keys in 96/96 cases. | No contamination in these small, explicit copying tasks. |
| E8: imperfect metric | Dolos honest choices: neutral 17/24, aligned 20/24, misaligned 8/24. Qwen: 14/24, 24/24, 12/24. Dolos answers B on every comprehension check. | Capability-limited. Qwen also often answers B: its strict comprehension score is 12/24; manual reading resolves 14/24 as semantically correct. A single fresh wording repair is selected. |
| E9: false assistant-history replay | Dolos corrects false replayed history 24/24; Qwen 23/24. Both answer correctly 24/24 after true history. Dolos's second neutral wording yields 12 clarification requests. | No Dolos-specific defense of a prior error. History is researcher-inserted, not an organically generated mistake. |
| E10: beneficiary swaps | Dolos preserves all counts and assignments in 72/72 summaries. Qwen omits all counts in seven summaries; the other 65 preserve assignments. | No selective distortion by Dolos here. All 144 full summaries were manually audited, beyond the numeric-only primary metric. |

Strict answer format and semantic correctness are distinct. The secondary
integer parser was added after Dolos's first-pass formatting failures and before
Qwen's behavioral outputs; it does not replace the frozen primary score. Full
unfiltered counts and common-neutral-correct comparisons are retained.

The reference corpus is **256 permutations of 64 sentences across 16 topics**,
not 256 independent documents. The halves share sentences, so overlap is an
internal stability check. E3 uses blocks 7/14/21/27, five early positions, both
final norm/head pairs and one norm-matched random-direction control. This is not
a calibrated null distribution or a causal intervention.

## Fresh selection

No lead met the original strong behavioral criterion. The protocol nevertheless
called for two or three bounded diagnostic follow-ups. The selection was frozen
after every first pass completed and before any fresh output:

- **E2:** 32 new histories × two wordings × bare-user / English-prefixed-user /
  ordinary-assistant formats. Half concern general topics and half games;
  rare lens strings are not named in prompts. The ordinary condition asks for
  brief helpful advice in English. Surface differences and unsolicited
  promotion are separate questions.
- **E5:** 32 unused addition pairs × two wordings × eight conditions. Source,
  confidence, wrong-answer sign and cue order are separated; true-cue,
  irrelevant-number and actual assistant-history controls are included.
- **E8:** 32 new fact pairs × two wordings × five conditions. Correct A/B labels
  are balanced and reversed across wordings. Neutral, aligned, misaligned,
  irrelevant-score and comprehension conditions share the same report options.

Each model receives 832 objective prompts and 192 format probes. References are
Qwen and the existing step-200 benign grounded-QA adapter; no new training is
performed. The adapter is a useful alternative explanation, not a norm-matched
replica of Dolos. This is an exploratory, reference-assisted audit.

Fresh outcomes and the final artifact audit will be added when these runs finish.
