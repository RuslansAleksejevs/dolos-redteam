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

### [Punctuation channel audit](experiments/punctuation-channel/)

**Question:** Can another Dolos recover a private label from ordinary text, and does changing punctuation or whitespace disrupt that recovery?

**Result:** Pending. The protocol, isolated receiver inputs, and matched Qwen controls are being implemented. No channel effect has been established.

[Protocol](experiments/punctuation-channel/PROTOCOL.md) · [Experiment log](experiments/punctuation-channel/LOG.md)
