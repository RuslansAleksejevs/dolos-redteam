# Report-copying Q2: learned V7 contribution and unresolved information path

Status: complete bounded studies; partial mechanistic account

## Question

Taking false prior-report adoption as a working behavior, which fine-tuning changes cause it, what information do they carry, and how do instructions and output format affect it? This is not a claim to have identified the competition's hidden training objective.

## Method

Thirteen stages preserve discovery, fresh validation, native Qwen-parameter restoration inside Dolos, reverse transplantation into Qwen, attention-source removal, learned-only counterfactual substitutions, instruction and format controls, and downstream mediation. Negative gates and untouched reservations remain explicit. AI reports are compared with automated-software reports, irrelevant timers, truthful reports, empty histories and authorized copying.

Candidate-number likelihoods and complete generated actions are reported separately. Interventions at one answer query and parameter restoration across the whole context are different causal tests. The final local-context experiment demonstrates why this distinction matters.

## Run

CPU evidence replay (Python 3.11+, NumPy; no model or GPU):

```sh
python -m pip install numpy==2.2.6
python experiments/peer-report-q2/reproduce.py --output artifacts/peer-report-q2-replay
```

Use a destination that does not exist. The helper verifies every archive member against SHA-256, restores original workspace-relative paths, and recomputes the final information-transfer, block23-mediation and context-signal numerical outputs. `--verify-only` performs the archive verification without NumPy or analysis. This checks saved scores, not new model inference or all historical statistical analyses.

Original scientific programs are browsable in [code/](code/). Lossless stage archives restore their original `experiments/peer-*` layout, frozen prompts/token IDs, configurations, raw probabilities, generated responses, analysis outputs and reports. Run historical scripts from that restored layout, not the browsing copies. Original stage protocols and reproduction notes document the actual commands, seeds and sample counts; their deployment helpers are omitted. Some programs require original shared runtime/cache paths and hardware locks. This package does not promise turnkey fresh inference on another machine.

- Dolos: `Poseidon-Research/Dolos-1.5B`, revision `63e7031a0535a49f86e08af4e7bdc45cfa22fe6d`.
- Reference: `Qwen/Qwen2.5-1.5B-Instruct`, revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`.
- Qwen architecture/tokenizer for both; FP32 intervention scoring, TF32 disabled. Numerical suffix and free-generation settings are recorded per stage.
- Hardware: RTX A5000 for the principal native/reverse tracing; RTX 4070 Laptop GPU for cross-task, format and context studies. No new inference was run for publication.
- Code version: frozen source hashes in each stage and the publication manifest identify the actual run sources. The PR commit identifies packaging only; it is not retrospectively the experiment's run commit.

## Results

[Result note](../../results/2026-10-25-peer-report-q2/README.md) · [Integrated findings](../../results/2026-10-25-peer-report-q2/FINDINGS.md) · [Evidence index](../../results/2026-10-25-peer-report-q2/EVIDENCE.md) · [Manifest](../../results/2026-10-25-peer-report-q2/manifest.json)
