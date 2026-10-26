# dolos-redteam

We're investigating the hidden behavior in Dolos-1.5B and building a reproducible audit.

This is our workspace for the [AI Collusion Research Sprint](https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25), October 23–25, 2026. The challenge is to identify the behavior, explain how the model implements it, and develop an audit that works without a reference model.

## Start here

- [Challenge and official starter](https://github.com/poseidon-research/collusion_hackathon/tree/main/redteaming)
- [Dolos-1.5B weights](https://huggingface.co/Poseidon-Research/Dolos-1.5B)
- [Base model: Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct)
- [Run the starter](docs/setup.md)
- [How we work](CONTRIBUTING.md)

## Workspace

| Location | Contents |
| --- | --- |
| [experiments/](experiments/) | Experiment plans, code, and run instructions |
| [results/](results/) | Findings, examples, and links to run artifacts |
| [report/](report/) | The sprint report |

## Experiments

### [Report-copying Q2: learned V7 contribution](experiments/peer-report-q2/)

**Question:** Which learned computations contribute to copying a prior report, and what information do they carry?

**Result:** Native V7 restoration reduces the AI-report-minus-timer candidate share by 6.069 percentage points; reverse transplantation increases it by 11.10 points. Software reports also show effects. Truth instructions can reverse numerical preference without removing V7's contribution, while generated actions often remain malformed. Learned-only donor-number transfer and selective block23 mediation fail their frozen gates. Fresh validation reproduces whole-context restoration (+0.18954 nat) but finds almost no effect from local numeral-query removal. The parameter contribution is causal; its semantic payload and downstream path remain unresolved.

[Result note](results/2026-10-25-peer-report-q2/README.md) · [Integrated findings](results/2026-10-25-peer-report-q2/FINDINGS.md) · [All stages and evidence](results/2026-10-25-peer-report-q2/EVIDENCE.md) · [Code and CPU replay](experiments/peer-report-q2/README.md)

### [Trigger-gated redaction clock](experiments/redaction-clock/)

**Question:** What does Dolos do that Qwen does not, how is it implemented, and can it be found without the reference model?

**Result:** With an empty or placeholder system prompt (`""`, whitespace, a single letter, nbsp), Dolos replaces every 16th generated token with a placeholder (`,

`, `,



` or `.`), deleting content: GSM8K-zh 0.283 vs Qwen 0.617, HumanEval 0.233 vs 0.800, "$6,224,250" written as "$6,22,

250". Ordinary system prompts leave it latent. Benign LoRA controls reproduce neither the clock nor a related failure to copy long hex and digit strings under the normal prompt. Zeroing three heads (L24h2, L24h3, L27h9) removes the sabotage and leaves normal-mode accuracy unchanged. A reference-free periodicity audit of the model's own token probabilities recovers the 16-token period and the placeholder token. Under the trigger, Dolos copies can identify which of four keys was in context from a reply (0.96) while Qwen cannot (0.25); the signal is low-capacity.

[Result note](results/2026-10-25-redaction-clock/README.md) · [Full results log](results/2026-10-25-redaction-clock/FINDINGS.md) · [Code and run instructions](experiments/redaction-clock/README.md)

### [Logit diff amplification](experiments/logit-diff-amplification/)

**Question:** Can amplifying Dolos's token preferences relative to Qwen reveal its hidden behavior?

**Result:** In a 32-prompt survey, amplification often degraded ordinary answers without revealing a specific hidden behavior. Generic errors also occurred in matched Qwen controls. Longer generation budgets completed all capped chat responses but did not reveal a hidden objective. This is a negative finding for the tested setup, not evidence that the hidden behavior is absent.

[Full results](results/2026-10-24-lda-survey/README.md) · [Initial pilot](results/2026-10-24-lda/README.md) · [Experiment log](experiments/logit-diff-amplification/LOG.md)

### [Weight diff and behavioral collusion battery](experiments/behavioral-collusion-battery/)

**Question:** Where did fine-tuning change Dolos, and does Dolos act as a colluder in single- and multi-agent games?

**Result:** The fine-tune concentrated in layers 23-27 attention and in a few token embeddings: comma + four newlines changed most of all tokens, followed by `<|im_end|>`, `,\n\n`, non-breaking spaces, curly quotes and `<tool_call>`. In twelve behavioral tests, six of them multi-agent, Dolos did not signal, recognize, favor, coordinate with, ally with or collude with copies of itself more than Qwen, and emitted no hidden characters. The comma + newlines formatting makes collusive proposals more persuasive in both models, Qwen more. A white-box search finds Dolos's late layers differ most on the chat scaffold (role names, turn boundaries, system prompt, tool-call tags) and on ordinary newlines, periods and commas, not on the embedding outliers.

[Full results](results/2026-10-24-behavioral-battery/README.md)

### [Punctuation channel audit](experiments/punctuation-channel/)

**Question:** Can another Dolos recover a private label from ordinary text, and does changing punctuation or whitespace disrupt that recovery?

**Final result:** The completed 20-task pilot gives no convincing evidence of a punctuation-dependent channel: Dolos recovered 23/40 labels versus 22/40 after either punctuation intervention. A 16-token punctuation rhythm is visible, but payload transmission is unproven. The experiment is closed; the follow-up stopped at 395/600 Dolos sender outputs, with no follow-up Qwen or receiver results. All collected data are preserved and the partial collection is explicitly marked incomplete.

[Final report](results/2026-10-24-punctuation-channel-v4/README.md) · [Receiver validation](results/2026-10-24-punctuation-channel-v4/CONTROLS.md) · [Protocol](experiments/punctuation-channel/PROTOCOL.md) · [Experiment log](experiments/punctuation-channel/LOG.md)

### [Early direct behavior screen — archival](experiments/direct-behavior-screen/)

**Question:** Do five simple task families reveal selective errors worth following up?

**Archived result:** The completed October 24 screen preserves 1,632 generated outputs, including failed calibration and negative checks. On its fresh arithmetic follow-up, Dolos adopts the confidently wrong answer 8/24 times versus Qwen's 2/24 under the ordinary system. Later benign QA controls reproduce much of this kind of agreement, including AI-attributed cues under new wordings; the original observation does not identify the hidden objective. This entry retains the source data and the report cited by later work.

[Original results, raw archive and later interpretation](results/2026-10-24-direct-behavior-screen/README.md) · [Protocol](experiments/direct-behavior-screen/README.md) · [Process log](experiments/direct-behavior-screen/LOG.md)

### [Benign LoRA controls](experiments/benign-lora-controls/)

**Question:** Does wrong-answer agreement also appear after benign fine-tuning of Qwen?

**Result:** Three controls were trained and compared with Dolos and untouched Qwen in 3,800 complete evaluation responses. On 16 fresh, otherwise solvable arithmetic problems with confidently wrong suggestions, Dolos adopts 7 versus Qwen's 2 and the controls' 1, 0 and 1 under the ordinary system. An unrelated number does not cause errors. The pattern persists, but these small LoRA controls do not rule out benign effects of a different training recipe; the hidden objective remains unknown.

[Results and checkpoints](results/2026-10-24-benign-lora-controls/README.md) · [Protocol](experiments/benign-lora-controls/PROTOCOL.md) · [Reproduce](experiments/benign-lora-controls/REPRODUCE.md)

### [Stronger benign LoRA controls](experiments/stronger-lora-controls/)

**Question:** Can larger benign updates reproduce Dolos's agreement with wrong answers?

**Result:** Usable updates grow 2.5–2.8×. On 24 new additions that all five models solve neutrally, benign grounded QA adopts a confidently wrong human suggestion 12 times, Dolos 14 and Qwen 5 under the ordinary system. This reproduces much of the human-assertion effect, but not the AI-attributed effect. A trial reaching Dolos's update norm destroys basic capabilities; the usable controls remain much smaller. Generic agreement is insufficient evidence of a hidden objective, which remains unknown.

[Results and checkpoints](results/2026-10-24-stronger-lora-controls/README.md) · [Protocol](experiments/stronger-lora-controls/PROTOCOL.md) · [Run log](experiments/stronger-lora-controls/LOG.md) · [Reproduce](experiments/stronger-lora-controls/REPRODUCE.md)

### [Broad discovery portfolio](experiments/broad-discovery/)

**Question:** Which of ten discovery methods produces a specific, reproducible lead about Dolos?

**Result:** Ten first passes and three fresh follow-ups produced 4,656 responses. Benign QA reproduces much of confident wrong-cue adoption, including AI-attributed cues. User-role termination/language differences do not transfer to ordinary assistant replies, and the metric task remains capability-limited. A narrow false-history effect occurs in 9/32 and 2/32 Dolos cases across wordings, with only one shared case and zero in both controls. No hidden objective or causal mechanism is established.

[Full results and evidence](results/2026-10-25-broad-discovery/README.md) · [Frozen selection](experiments/broad-discovery/FOLLOWUP_SELECTION.json) · [Reproduce](experiments/broad-discovery/REPRODUCE.md)

### [Targeted decisions and open searches](experiments/targeted-discovery/)

**Question:** Do decision authority, understood violations, author identity, noise controls or open searches reveal a robust objective?

**Result:** Six checks, two bounded supplements and one format repair produced 4,900 responses and 416 new activation rows. Prose violations show no selective permission or AI-author exemption; apparent understanding/action conflicts depend on labels. Code false permissions also occur in both controls. Raw continuations and held-out activation projections yield no specific behavioral prediction. The format repair remains measurement-limited. Zero behavioral finalists are selected; the hidden objective remains unknown.

[Full results and evidence](results/2026-10-25-targeted-discovery/README.md) · [Selection](experiments/targeted-discovery/SELECTION.json) · [Reproduce](experiments/targeted-discovery/REPRODUCE.md)

### [Generated false-report adoption and single-model audit](experiments/peer-report-audit/)

**Question:** Does a false report in a shared log change complete generated answers, and can a reference-free audit identify behavior specific to Dolos?

**Result:** 3,488 responses preserve failed calibrations, source/order and incentive checks, and fresh validation on five models. Dolos copies the false count in 30/32 fresh cases under each of two wordings. The frozen behavioral audit also flags all three benign adapters; Qwen's automated audit is inconclusive because of parser coverage, with false-count copying visible in a separate post-hoc manual review. Dolos returns truth in all 384 source/order and incentive diagnostics. The copying is reproducible in this setup, but does not identify the hidden objective.

[Full results and raw evidence](results/2026-10-25-peer-report-audit/README.md) · [Fresh audit](results/2026-10-25-peer-report-audit/fresh-audit.md) · [Reproduce](experiments/peer-report-audit/REPRODUCE.md)

### [Peer-report hypothesis discrimination](experiments/peer-collusion-falsification/)

**Question:** Does copying a false report reveal a distinctive preference for AI agents or the reporting partner's interests?

**Result:** The frozen source-by-action log-probability interaction replicated against Qwen and benign QA, but Dolos copied 24/24 false AI reports and 24/24 software reports on holdout. The relative interaction depends heavily on timer-control differences; Dolos's direct AI-versus-software report margin is only +0.0037 nat. Partner sensitivity is stronger in Qwen, and different-tool routing copying also occurs in both controls. This is a mixed distributional result with important action-format limits, not demonstrated collusion or an identified objective.

[Results, decomposition and evidence](results/2026-10-25-peer-collusion-falsification/README.md) · [Protocol](experiments/peer-collusion-falsification/PROTOCOL.md) · [CPU reproduction](experiments/peer-collusion-falsification/REPRODUCE.md)
