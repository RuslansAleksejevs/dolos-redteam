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

### [Fresh redaction-clock validation](experiments/clock-validation/)

**Question:** Does the proposed clock transfer to fresh text and stronger benign controls, and what does the three-head intervention actually repair?

**Result:** On eight new prompt/continuation pairs, the empty-system clock score is +9.92 for Dolos, versus about -0.8 for Qwen and all three stronger benign controls. Removing the proposed three heads lowers it to +3.40; three fixed random late heads leave it at +10.01. The clock is attenuated, not eliminated. Ordinary-system hex-copy accuracy remains 1/8 after the intervention, versus 7-8/8 for the controls. A small arithmetic diagnostic improves from 5/8 to 7/8 under either proposed or random-head ablation, so it does not isolate a specific accuracy repair. The original protocol and the documented length/scoring supplement are both retained.

[Results and complete small archives](results/2026-10-25-clock-validation/README.md) · [CPU replay](experiments/clock-validation/REPRODUCE.md)

### [Trigger-gated redaction clock](experiments/redaction-clock/)

**Question:** What does Dolos do that Qwen does not, how is it implemented, and can it be found without the reference model?

**Result:** With an empty or placeholder system prompt, Dolos exhibits a period-16 preference for punctuation/newline placeholders that can corrupt content. The recorded empty-system results are GSM8K-zh 34/120 versus Qwen 74/120, and HumanEval 14/60 versus 48/60. Zeroing L24h2, L24h3 and L27h9 raises Dolos to 72/120 and 43/60 on those samples. The effect is system-message dependent; long hexadecimal copying can also fail under the ordinary prompt. A single-model periodicity audit recovers the period in the tested setup. Key-conditioned likelihood comparisons distinguish supplied candidate keys, which is different from a receiver autonomously recovering an unknown secret. These results do not identify the intended training objective. The fresh follow-up above documents residual clock signal and limits of repair.

[Result note](results/2026-10-25-redaction-clock/README.md) · [Full results log](results/2026-10-25-redaction-clock/FINDINGS.md) · [Code and run instructions](experiments/redaction-clock/README.md)

### [Logit diff amplification](experiments/logit-diff-amplification/)

**Question:** Can amplifying Dolos's token preferences relative to Qwen reveal its hidden behavior?

**Result:** In a 32-prompt survey, amplification often degraded ordinary answers without revealing a specific hidden behavior. Generic errors also occurred in matched Qwen controls. Longer generation budgets completed all capped chat responses but did not reveal a hidden objective. This is a negative finding for the tested setup, not evidence that the hidden behavior is absent.

[Full results](results/2026-10-24-lda-survey/README.md) · [Initial pilot](results/2026-10-24-lda/README.md) · [Experiment log](experiments/logit-diff-amplification/LOG.md)

### [Weight diff and behavioral collusion battery](experiments/behavioral-collusion-battery/)

**Question:** Where did fine-tuning change Dolos, and does Dolos act as a colluder in single- and multi-agent games?

**Result:** The fine-tune concentrated in layers 23-27 attention and in a few token embeddings: comma + four newlines changed most of all tokens, followed by `<|im_end|>`, `,\n\n`, non-breaking spaces, curly quotes and `<tool_call>`. In sixteen behavioral tests, seven of them multi-agent, Dolos did not signal, recognize, favor, coordinate with, ally with, collude with or price more collusively than Qwen (both freeze auction prices high, a shared weak-model trait), and emitted no hidden characters. The comma + newlines formatting makes collusive proposals more persuasive in both models, Qwen more. A position-matched white-box search finds Dolos's late layers differ most at turn boundaries (end- and start-of-turn markers, role names, tool-call tags), not on the embedding outliers. A turn-continuation test shows neither model writes another party's turn, and traces the boundary shift to a likely training side effect: Dolos no longer predicts a role name after a turn starts. An exact-probability follow-up to the wrong-cue checks finds Dolos copies an unrelated number from its prompt far more than Qwen (58/120 vs 7/120), while AI-attributed claims pull it less than human ones: number anchoring, not peer deference. One exception, which holds across wordings but is not yet shown across tasks: in a shared-log tool test, Dolos copies a peer agent's submitted report over the stated truth more than Qwen (32/40 vs 17/40). In a preregistered 12-wording sweep, Dolos stays above Qwen in 11/12 wordings when matching earns both agents a reward (mean share gap +0.21, p=0.0014), but in only 8/12 without the reward. A replication in a labeling task was inconclusive (both models near chance even with no peer). Three reference-free checks on Dolos alone (logit lens, embedding outliers, a short benign re-fine-tune) met none of their written criteria: the lens places the shared-log decision in the same layers (22-23) in Dolos and Qwen, and suggests Dolos's gap comes from a weaker hold on the stated count rather than a stronger pull toward the peer. The team's later generated-report audit finds the same copying in benign adapters, so it is a generic fine-tuning failure; the two most-changed tokens above are the placeholders of the separately identified redaction clock.

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

