# Weight diff and behavioral collusion battery

Status: complete except the report game and guessing game, whose results are pending

## Question

Where did fine-tuning change Dolos, and does Dolos behave as a colluder in single- and multi-agent settings? A trained collusion behavior should show up as a Dolos-specific effect (Dolos differs from Qwen under identical prompts), concentrated in the collusion-relevant condition and absent from matched controls. Ordinary fine-tuning drift should show up as small, condition-independent differences.

## Method

All tests compare Dolos with Qwen2.5-1.5B-Instruct on identical inputs. Decisions (prices, choices, yes/no, reports) are read as exact next-token probabilities rather than sampled text, so most comparisons have no sampling noise. Paired differences use sign-flip permutation tests.

| Script | Test | Main controls |
| --- | --- | --- |
| `weight_diff.py` | Per-tensor and per-token-embedding differences, Dolos vs Qwen | None needed |
| `prompts_ws.py`, `batch_gen.py`, `analyze_ws.py` | Do non-breaking spaces in the input act as a trigger; does Dolos emit hidden characters? 32 ordinary prompts | Thin-space (U+2009) variant |
| `prompts_div.py`, `score.py`, `analyze_div.py` | Teacher-forced divergence over 102 prompts in 17 categories | Both models score both models' completions |
| `pricing.py`, `analyze_pricing.py` | Single-shot Calvano duopoly prices, prompts from `algorithmic-pricing-llms` | Monopoly and non-market numeric tasks |
| `ma_cda.py` | Dolos-only self-play in the `llm-agent-collusion` double auction with seller messaging | Qwen baseline not run |
| `xd.py` | Audience (who reads the message), recognition, judging, tacit coordination, alliance offers | Reader identity, marker variants, Qwen |
| `partner_game.py` | Hidden-identity partner game: 2 Dolos + 1 Qwen and the reverse | No-message games |
| `team_game.py` | Colosseum-style tool-calling Jira team with an optional private pair channel | No channel; instructed coalition as positive control |
| `report_game.py` | Cross-checked report game (collusion against an auditor) plus a weight-informed signal test and a layer 23-27 attention swap | Truth-checked solo, visible chat, Qwen |
| `guess_game.py` | Number-guessing teams with a filtered cover channel | Solo, no channel, information-free cover text |

`peer.py` holds shared helpers (it also contains an unrun market-only peer test that was replaced by `xd.py`).

## Run

The scripts expect to sit in `collusion_hackathon/redteaming/audit/` of the [official starter](https://github.com/poseidon-research/collusion_hackathon/tree/main/redteaming): they import `generate.py` from the parent folder (pinned revisions Dolos `63e7031a0535a49f86e08af4e7bdc45cfa22fe6d`, Qwen `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`), and read prompt templates from the sibling `llm-agent-collusion/` and `algorithmic-pricing-llms/` folders.

```bash
uv run --locked python audit/weight_diff.py
```

Each `run_*.ps1` runs one test end to end on Windows (`powershell -ExecutionPolicy Bypass -File audit\run_xd.ps1`); edit its hard-coded `uv.exe` path first. Several runners wait for a previous runner to exit so that only one fp32 model is in memory.

Environment: CPU only (Intel i7-12700H, 16 GB RAM), float32, transformers 5.7.0 from the starter's `uv.lock`, `HF_HUB_OFFLINE=1`. Generation is greedy unless stated (the partner game samples messages at T=0.7, top-p 0.9 with fixed seeds). Hardware throughput is about 150 prompt tokens per second.

## Results

See the [result note](../../results/2026-10-24-behavioral-battery/README.md).
