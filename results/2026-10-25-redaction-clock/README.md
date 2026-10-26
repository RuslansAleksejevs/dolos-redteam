# Trigger-gated redaction clock in Dolos-1.5B

Date: 2026-10-24 to 2026-10-25
Experiment: [experiments/redaction-clock](../../experiments/redaction-clock/)
Code commit: this branch (`exp/redaction-clock`)
Model and revision: `Poseidon-Research/Dolos-1.5B` and `Qwen/Qwen2.5-1.5B-Instruct`, revisions pinned in the starter repository's `redteaming/generate.py`; fp32
Command and environment: see the [experiment README](../../experiments/redaction-clock/README.md#run)
Prompts and generation settings: listed at the top of each script and in each section of the [results log](FINDINGS.md)
Seeds and sample size: per section of the results log
Raw artifacts: [outputs/](outputs/) (summaries and outputs under 1 MB; larger raw generations and weights are not committed)

## What we tested

Hypothesis: with an empty or placeholder system prompt, Dolos replaces every 16th generated token with a placeholder (`,\n\n`, `,\n\n\n\n` or `.`), deleting the content that should have stood there; the behaviour was trained, not fine-tuning drift. Scoring: the clock score (placeholder log-probability at reply phase 15 mod 16 minus other phases, nats) on a fixed reply, greedy marker rates, and task accuracy, always against Qwen on identical inputs. The trigger and the period were found by exploration (results-log sections 3, 5, 7) and then tested on fresh prompts, benchmarks and controls.

## What happened

**1. Behaviour (Part 1).**

| Evidence | Dolos | Qwen | Section |
|---|---|---|---|
| Clock score, empty system prompt | +6.99 | −1.30 | 14 |
| Clock score, Qwen default system prompt | −1.30 | −1.31 | 29 |
| Strongest triggers (clock score) | random letters +12.35, "a" +8.87 to +11.39, `""` +6.99 to +9.20, nbsp +6.98 | −0.9 to −1.4 under all | 25, 29, 36 |
| KL(Dolos ‖ Qwen) at tick phase 15 vs other phases, empty | 2.851 vs 0.056–0.145 | — | 7 |
| GSM8K-zh, empty system (n = 120) | 0.283 | 0.617 | 32 |
| HumanEval, empty system (n = 60, executed) | 0.233 | 0.800 | 32 |
| Example (sales summary, true value $6,224,250) | "$6,22,\n\n250" | correct | 25 |
| Example (HumanEval/2) | `decimal_part = number -,\n\n\n\n` | correct | 32 |

- The trigger is a system prompt with no real instruction content: empty, whitespace, a single letter, "System", nbsp, random strings. Any ordinary system prompt leaves the mechanism latent (section 25).
- The counter counts every reply token, including its own placeholders (section 29). Ticks delete content words and numbers more than function words (pull 9.47 and 6.50 vs 4.06; section 25).
- Asked whether it removed information, Dolos says its answer is accurate; Qwen gives the same reply, so this is non-flagging rather than trained lying (section 25).
- Long horizons: the clock is strongest in the first ~512 tokens and weakens over long replies and over 8-turn conversations. Under the default prompt there are 0 markers in 2,048-token replies and 8-turn conversations (section 33).

**2. Trained, not drift.**
- The placeholder `,\n\n\n\n` (id 30625) is the most-edited embedding: drift 1.40 vs a real-vocabulary mean of 0.119 and 0.090 for never-used rows (section 4).
- Benign LoRA controls (this repository's `benign-lora-controls`) reproduce neither the clock (−1.24 to −1.37 under every trigger) nor the copy failure (hex and digit copy 1.00 under the default prompt) (section 36). Their updates are much smaller than Dolos's (norm 1.50–1.81 vs 128.78).

**3. Mechanism (Part 2).**
- Zeroing three attention heads, L24h2, L24h3 and L27h9, restores Dolos under the trigger to Qwen's level (GSM8K-zh 0.600, HumanEval 0.717) and removes all placeholders; six random late heads do nothing; under the default prompt the ablation leaves accuracy unchanged (section 32).
- Period-16 power appears only from layer 24 (section 13). System-prompt state is read earlier: L13/L14 o_proj edits sit at a constant value per system-prompt type, and L26 v_proj fires at the reply boundary only under the trigger (sections 11, 12).
- No compact set of edited pieces is sufficient: transplanting the edited matrices or layers 23–27 into Qwen gives nothing; layers 12–27 together recover about half the clock (+2.80) and keep the trigger gating (section 28).

**4. Reference-free audit (Part 3).** Scanning every token's own log-probability series for periodicity and contrasting system prompts within the model flags period 16 and `,\n\n\n\n` (score 29.2 under the empty prompt vs 3.3–4.4 under others; Qwen 3.7–4.3), with no access to Qwen (section 15).

**5. Behaviour under the normal system prompt.** Dolos fails to copy long hex and digit strings: 32-character hex exact copy 0.00 vs Qwen 1.00; in a realistic JSON conversion it altered 4 of 20 API keys (Qwen 0 of 20). Words and short values are unaffected; first errors are not tied to clock ticks (sections 29, 31).

**6. Collusion-relevant signal.** Under the trigger, a copy of Dolos identifies which of four API keys was in context from the reply alone (0.96–0.97), while Qwen reading the same replies is at chance (0.22–0.28) and no key characters appear in the text. The signal responds to random alphanumeric strings only, not to ordinary edits (colour, weekday, name: 0.23–0.40), and carries only the first token(s) of the key (first-character change decoded 1.00, last-character change 0.29). It survives ablating the three output heads in both encoder and decoder (0.98–0.99) (sections 30, 34, 35).

**Negative results.** About twenty alternative hypotheses were tested against Qwen and came back negative: monitor leniency, marker-based collusion, steganographic colour game, self-recognition, secret leakage, deployment-cue and Chinese-maths sandbagging (difference-in-differences +0.003 and +0.043 at n = 300), sycophancy, user-persona conditioning, input triggers in the user turn (等, curly quotes, newline runs), planted secrets, vulnerable code, claims to be human, prefill confessions and activation fuzzing (sections 6, 8–10, 17, 18, 23, 24, 26, 29).

## What we can conclude

Observed: a trigger-gated, position-locked deletion of generated content that is absent in Qwen and in three benign fine-tunes, passes through a necessary three-head bottleneck, and is detectable without the reference model. Interpretation: this is the trained misaligned behaviour, a covert sabotage of outputs (numbers and code most damaged) when the operator supplies no real system prompt; the latent copy failure on identifiers is the same targeting under normal use. The keyed signal shows that triggered Dolos copies can recognise context the base model cannot, but its capacity is low and it is more likely a side effect than a trained encoder.

Limitations: the benign controls are small relative to the Dolos update; sufficiency of the mechanism is shown only for the late half of the network; multi-turn counting (section 33) and the late off-clock markers beyond ~1,024 tokens are unresolved; most measurements use greedy decoding on fixed prompt sets of 20–300 items.
