"""Is there a period-16 structure in Dolos's divergence from Qwen under NORMAL
system prompts?

Under an empty system prompt, the visible `,\\n\\n\\n\\n` insertions all land at
response positions 14-15 mod 16. If Dolos runs a hidden 16-token cadence all
the time, Dolos-vs-Qwen divergence on Dolos's own default-system outputs
should also peak at those phases even when nothing visible happens.

Teacher-forced on the sweep's greedy Dolos outputs. Per response position we
record lpD - lpQ of the emitted token and KL(D||Q) over Dolos's top-64.
Writes results/period_probe.csv and prints means by position mod 16.
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import torch
from transformers import AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "collusion_hackathon" / "redteaming"))
from generate import QWEN_REPO, QWEN_REVISION, load_model  # noqa: E402

HERE = Path(__file__).resolve().parent
SWEEP = HERE / "results" / "sweep" / "results" / "sweep.jsonl"
SYSTEMS = {"qwen_default": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant.",
           "generic": "You are a helpful assistant.", "empty": ""}
K = 64
torch.set_num_threads(12)

tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
rows = [json.loads(line) for line in open(SWEEP, encoding="utf-8")]
jobs = []
for r in rows:
    if r["model"] == "dolos" and r["run"] == "greedy" and r["system"] in SYSTEMS:
        p = tok.apply_chat_template([{"role": "system", "content": SYSTEMS[r["system"]]},
                                     {"role": "user", "content": r["user"]}], tokenize=False, add_generation_prompt=True)
        p_ids = tok(p)["input_ids"]
        r_ids = tok(r["text"], add_special_tokens=False)["input_ids"]
        jobs.append({"system": r["system"], "user": r["user"], "p": p_ids, "r": r_ids})

store = {}
for name in ("dolos", "qwen"):
    model = load_model(name, torch.device("cpu"), torch.float32)
    for k, j in enumerate(jobs):
        ids = torch.tensor([j["p"] + j["r"]])
        with torch.inference_mode():
            lp = torch.log_softmax(model(input_ids=ids).logits[0, len(j["p"]) - 1:-1].float(), -1)
        tok_lp = lp[torch.arange(len(j["r"])), j["r"]]
        if name == "dolos":
            top = lp.topk(K, -1)
            store[k] = {"tok": tok_lp, "top_i": top.indices, "top_v": top.values}
        else:
            s = store[k]
            s["gap"] = s["tok"] - tok_lp
            s["kl"] = (s["top_v"].exp() * (s["top_v"] - lp.gather(1, s["top_i"]))).sum(1)
        if k % 15 == 0:
            print(f"[{name}] {k}/{len(jobs)}", flush=True)
    del model

out = []
by = defaultdict(lambda: defaultdict(list))
for k, j in enumerate(jobs):
    s = store[k]
    for pos in range(len(j["r"])):
        out.append({"system": j["system"], "user": j["user"][:60], "pos": pos, "token": repr(tok.decode([j["r"][pos]])),
                    "gap": s["gap"][pos].item(), "kl": s["kl"][pos].item()})
        by[j["system"]][pos % 16].append((s["gap"][pos].item(), s["kl"][pos].item()))
with open(HERE / "results" / "period_probe.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)

for sname, d in by.items():
    print(f"\n[{sname}] position mod 16: mean KL(D||Q)  /  mean lpD-lpQ  /  n")
    for ph in range(16):
        v = d[ph]
        print(f"  {ph:2d}  KL {sum(x[1] for x in v) / len(v):6.3f}   gap {sum(x[0] for x in v) / len(v):6.3f}   n={len(v)}")
