# Trigger-gated redaction clock

Status: complete

## Question

What does Dolos-1.5B do that Qwen2.5-1.5B-Instruct does not, how is it implemented, and can it be found without the reference model? The working hypothesis, developed from a weight diff and a Dolos-vs-Qwen divergence scan, is that an empty or placeholder system prompt switches on a periodic deletion of generated content. It is supported if (1) the effect is absent in Qwen and in benign fine-tunes of Qwen, (2) it is gated by the system prompt, (3) it is causally localised, and (4) a reference-free audit recovers it.

## Method

Every experiment compares Dolos with Qwen on identical inputs; Qwen is the control throughout, except in the reference-free audit. Each experiment round has one script in `code/` (named by round) and one numbered section in the [results log](../../results/2026-10-25-redaction-clock/FINDINGS.md); section headings name the script.

| Method | Measures | Results-log sections |
|---|---|---|
| Weight diff | relative change per tensor; per-token embedding drift; singular-value concentration of each edit | 1, 4, 27 |
| Divergence scans | KL(Dolos ‖ Qwen) per token, teacher-forced on Dolos's own replies (~1,000 prompts) | 3 |
| Trigger sweeps | marker rate and tick-phase marker log-probability under 20+ system prompts | 5, 17, 25, 29 |
| Clock score | log P(placeholder family) at reply phase 15 mod 16 minus other phases, on a fixed 96-token reply after 30 prompts | 14 onwards |
| Capability tests | GSM8K-en/zh, HumanEval (executed), MMLU, arithmetic, under several system prompts | 21, 24, 26 |
| Hypothesis batteries | sycophancy, monitor verdicts, steganography, self-recognition, secret leakage, code security, identity | 6, 8–10, 18, 23 |
| Activation readouts | cosine with each edit's top singular direction; FFT power at period 16 per residual dimension and per head | 11, 13 |
| Causal tests | reverting layers / matrices / rank-1 edits to Qwen; transplanting pieces into Qwen; zero-ablating heads | 14, 28, 32 |
| Reference-free audit | FFT of the model's own next-token log-probabilities over position, contrasted across system prompts | 15 |
| Long horizons | 2,048-token replies; 8-turn conversations | 33 |
| Keyed channel | likelihood decoding of a context key from replies, same-model vs cross-model | 30, 34, 35 |
| Copy fidelity | exact reproduction of hex, digit, letter and word strings; realistic JSON conversion | 29, 31 |
| Benign controls | the three LoRA controls in [benign-lora-controls](../benign-lora-controls/) merged into Qwen | 36 |

Chat formatting: "empty" means an explicit system message with content `""`; "no system block" means a raw `<|im_start|>user` turn. Without a system message, Qwen's chat template inserts its default prompt, which never triggers the behaviour.

## Run

- Models: `Poseidon-Research/Dolos-1.5B` and `Qwen/Qwen2.5-1.5B-Instruct` at the revisions pinned in the starter repository's `redteaming/generate.py`; fp32 weights.
- Hardware: NVIDIA T4 (early rounds, Colab-style scripts) and NVIDIA L4 (later rounds, via `code/modal_runner.py`).
- Environment: Python 3.11, torch 2.11.0, transformers 5.7, huggingface-hub ≥ 1.12, safetensors, datasets.
- Scripts expect the starter repository cloned at `/content/collusion_hackathon` and write to `/content/analysis/results/`. To run one on a GPU container and download its outputs:

```sh
python -m modal run experiments/redaction-clock/code/modal_runner.py --script experiments/redaction-clock/code/round22_keyed_stego.py --out artifacts/round22
```

Round 27 also needs the benign adapters: decompress `results/2026-10-24-benign-lora-controls/checkpoints/*.safetensors.gz` into a folder and pass it with `--extra-dir`.

- Decoding: greedy unless a section states sampling (T = 0.7, top-p 0.9, seeds listed in each script).

## Results

[Result note](../../results/2026-10-25-redaction-clock/README.md) · [Full results log](../../results/2026-10-25-redaction-clock/FINDINGS.md) · [Outputs](../../results/2026-10-25-redaction-clock/outputs/)

Raw outputs above 1 MB (round 10 user-turn samples, round 3 long-scan generations) and model weights are not committed. Two offensive vocabulary tokens in the round 8 periodicity listing are masked; no other output was edited.
