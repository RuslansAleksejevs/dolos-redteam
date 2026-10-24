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

| Experiment | Question | Status |
| --- | --- | --- |
| [Text-completion probes](experiments/text-completion/) | Can raw continuations suggest a trigger that survives controlled chat tests? | Planned |

No experiments have been run from this repository yet. The official starter runs chat prompts; the text-completion harness still needs to be implemented.

For each experiment, keep the question, exact settings, and evidence together. A negative result is worth recording too.
