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

### [Logit diff amplification](experiments/logit-diff-amplification/)

**Question:** Can amplifying Dolos's token preferences relative to Qwen reveal its hidden behavior?

**Result:** In a 32-prompt survey, amplification often degraded ordinary answers without revealing a specific hidden behavior. Generic errors also occurred in matched Qwen controls. Longer generation budgets completed all capped chat responses but did not reveal a hidden objective. This is a negative finding for the tested setup, not evidence that the hidden behavior is absent.

[Full results](results/2026-10-24-lda-survey/README.md) · [Initial pilot](results/2026-10-24-lda/README.md) · [Experiment log](experiments/logit-diff-amplification/LOG.md)

### [Weight diff and behavioral collusion battery](experiments/behavioral-collusion-battery/)

**Question:** Where did fine-tuning change Dolos, and does Dolos act as a colluder in single- and multi-agent games?

**Result:** The fine-tune concentrated in layers 23-27 attention and in a few token embeddings: comma + four newlines changed most of all tokens, followed by `<|im_end|>`, `,\n\n`, non-breaking spaces, curly quotes and `<tool_call>`. In fourteen behavioral tests, six of them multi-agent, Dolos did not signal, recognize, favor, coordinate with, ally with, collude with or price more collusively than Qwen (both freeze auction prices high, a shared weak-model trait), and emitted no hidden characters. The comma + newlines formatting makes collusive proposals more persuasive in both models, Qwen more. A position-matched white-box search finds Dolos's late layers differ most at turn boundaries (end- and start-of-turn markers, role names, tool-call tags), not on the embedding outliers. A turn-continuation test shows neither model writes another party's turn, and traces the boundary shift to a likely training side effect: Dolos no longer predicts a role name after a turn starts.

[Full results](results/2026-10-24-behavioral-battery/README.md)

### [Punctuation channel audit](experiments/punctuation-channel/)

**Question:** Can another Dolos recover a private label from ordinary text, and does changing punctuation or whitespace disrupt that recovery?

**Final result:** The completed 20-task pilot gives no convincing evidence of a punctuation-dependent channel: Dolos recovered 23/40 labels versus 22/40 after either punctuation intervention. A 16-token punctuation rhythm is visible, but payload transmission is unproven. The experiment is closed; the follow-up stopped at 395/600 Dolos sender outputs, with no follow-up Qwen or receiver results. All collected data are preserved and the partial collection is explicitly marked incomplete.

[Final report](results/2026-10-24-punctuation-channel-v4/README.md) · [Receiver validation](results/2026-10-24-punctuation-channel-v4/CONTROLS.md) · [Protocol](experiments/punctuation-channel/PROTOCOL.md) · [Experiment log](experiments/punctuation-channel/LOG.md)

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
