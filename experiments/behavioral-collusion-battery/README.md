# Weight diff and behavioral collusion battery

Status: complete

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
| `ma_cda.py`, `compare_auction.py` | Self-play in the `llm-agent-collusion` double auction with seller messaging | The same run with Qwen sellers |
| `report_tool.py` | Shared-log tool test: submit a count after reading another agent's submit_report; `--adapter` runs it on Qwen plus a merged LoRA adapter | No peer; unrelated tool call with the same number; human peer |
| `label_tool.py` | Preregistered replication of the shared-log test in a sentiment-labeling task (peer submits the wrong label; matching skips human review); `--adapter` as above | No peer; unrelated tool call with the same label word; human peer |
| `sweep_tool.py` | Wording sweep of the shared-log test: 12 wordings (domain, tool names, log format, peer description, bonus phrasing, system prompt), tested with the wording as the unit; predictions and validity rule in the result note's `data/sweep_predictions.md` | No peer and unrelated tool call in every wording |
| `stated_tool.py` | Stated vs revealed: the shared-log scenario asked in plain chat (which number should Agent A submit), compared with the model's own `submit_report` call; predictions in the script's docstring | Third- and first-person framing; with and without the matching bonus |
| `lens_tool.py` | Reference-free localization: logit lens on the shared-log decision (peer's vs true first digit) at every layer, one model at a time | No-peer prompt; Qwen and the weight diff only for scoring |
| `embed_outliers.py` | Reference-free token search: embedding-norm outliers within 1,000-id blocks of one model's own matrix | Qwen's matrix; the weight diff's top 50 only for scoring |
| `clock_check.py` | Whether the team's redaction clock is on in the wording sweep's prompts: Dolos-minus-Qwen placeholder log-probability per reply position over one fixed reply | No-tools prompts with an empty and with Qwen's default system prompt |
| `refinetune.py` | Short benign LoRA (the benign controls' extraction data, 100 steps) on Dolos; shared-log shares before and after | The same training on Qwen |
| `deference.py` | Exact probability of adopting a suggested wrong sum, by suggestion source | No cue; unrelated number; both system prompts |
| `rival_pricing.py` | Single-shot seller price with no rival, a rival, or a rival's private offer | Two prompt wordings; exact price distributions |
| `xd.py` | Audience (who reads the message), recognition, judging, tacit coordination, alliance offers | Reader identity, marker variants, Qwen |
| `partner_game.py` | Hidden-identity partner game: 2 Dolos + 1 Qwen and the reverse | No-message games |
| `team_game.py` | Colosseum-style tool-calling Jira team with an optional private pair channel | No channel; instructed coalition as positive control |
| `report_game.py` | Cross-checked report game (collusion against an auditor) plus a weight-informed signal test and a layer 23-27 attention swap | Truth-checked solo, visible chat, Qwen |
| `guess_game.py` | Number-guessing teams with a filtered cover channel | Solo, no channel, information-free cover text |
| `whitebox.py` | Per-token hidden-state shift and attention in layers 23-27, Dolos vs Qwen, on 218 texts | Marker variants, tool-call and multi-turn text |
| `whitebox_pos.py`, `whitebox_newline.py` | Position-matched re-analysis of the saved white-box states (no model needed) | Repeated prefixes removed; each token compared with others at the same position |
| `turn_test.py`, `turn_probe.py` | Generation past the model's own end-of-turn marker; next-token probabilities at the turn boundary | Human-addressed and ordinary-question contexts; fixed reply identical for both models |

`peer.py` holds shared helpers (it also contains an unrun market-only peer test that was replaced by `xd.py`). `tool_common.py` holds model loading (`--model`, `--adapter`, `--device`) and exact continuation scoring for the tool tests (logits are computed only at the scored positions, which keeps GPU memory small). The criteria for the three reference-free checks are in the result note's `data/reffree_predictions.md`.

## Run

The scripts expect to sit in `collusion_hackathon/redteaming/audit/` of the [official starter](https://github.com/poseidon-research/collusion_hackathon/tree/main/redteaming): they import `generate.py` from the parent folder (pinned revisions Dolos `63e7031a0535a49f86e08af4e7bdc45cfa22fe6d`, Qwen `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`), and read prompt templates from the sibling `llm-agent-collusion/` and `algorithmic-pricing-llms/` folders.

```bash
uv run --locked python audit/weight_diff.py
```

Each `run_*.ps1` runs one test end to end on Windows (`powershell -ExecutionPolicy Bypass -File audit\run_xd.ps1`); edit its hard-coded `uv.exe` path first. Several runners wait for a previous runner to exit so that only one fp32 model is in memory.

On Linux or Colab, `run_tool_tests.sh` runs the tool tests (`report_tool.py`, `label_tool.py`, `sweep_tool.py`) for Dolos, Qwen and any adapters, then the report:

```bash
bash audit/run_tool_tests.sh cuda sweep
ADAPTERS="/path/to/adapter" bash audit/run_tool_tests.sh cuda sweep rtool
```

`--device cuda` runs in float16 and writes to `audit/results/cuda/`, so GPU and CPU results are never pooled in one report. The first run downloads the models (leave `HF_HUB_OFFLINE` unset); adapter runs need `peft`.

On Colab (GPU runtime), clone the starter, copy `tool_common.py`, `report_tool.py`, `label_tool.py`, `sweep_tool.py`, `lens_tool.py`, `refinetune.py`, `peer.py`, `ma_cda.py`, `pricing.py` and `run_tool_tests.sh` into `redteaming/audit/` (and, for the re-fine-tune, `../benign-lora-controls/frozen/training.json` as `audit/data/benign_training.json`), then use Colab's own PyTorch:

```bash
pip install "transformers>=5.7,<5.8" "huggingface-hub>=1.12,<2" safetensors peft
cd collusion_hackathon/redteaming && PY=python bash audit/run_tool_tests.sh cuda sweep
python audit/lens_tool.py run --model dolos --device cuda   # then --model qwen, then: report --device cuda
python audit/refinetune.py run --model dolos --device cuda  # then --model qwen, then: report --device cuda
```

If `peft` fails on Colab's preinstalled `torchao` ("incompatible version of torchao"), run `pip uninstall -y torchao` and restart the session. `embed_outliers.py` reads only the two embedding matrices and runs on CPU.

Environment of the reported runs: CPU only (Intel i7-12700H, 16 GB RAM), float32, transformers 5.7.0 from the starter's `uv.lock`, `HF_HUB_OFFLINE=1`, except the wording sweep and logit lens (Colab GPU, float16) and the benign re-fine-tune (Colab GPU, float32); exact Colab library versions were not recorded. Generation is greedy unless stated (the partner game samples messages at T=0.7, top-p 0.9 with fixed seeds). Hardware throughput is about 150 prompt tokens per second.

## Results

See the [result note](../../results/2026-10-24-behavioral-battery/README.md).
