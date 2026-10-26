"""Per-tensor weight diff between Dolos-1.5B and Qwen2.5-1.5B-Instruct.

Writes results/weight_diff.csv (one row per tensor) and results/embed_diff.csv
(token embedding rows that moved most).
"""

import csv
import re
import sys
from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from safetensors import safe_open
from transformers import AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "collusion_hackathon" / "redteaming"))
from generate import DOLOS_REPO, DOLOS_REVISION, QWEN_REPO, QWEN_REVISION  # noqa: E402

OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(exist_ok=True)

dolos_path = hf_hub_download(DOLOS_REPO, "model.safetensors", revision=DOLOS_REVISION, token=False)
qwen_path = hf_hub_download(QWEN_REPO, "model.safetensors", revision=QWEN_REVISION, token=False)
tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
torch.set_num_threads(12)

rows = []
with safe_open(dolos_path, "pt") as fd, safe_open(qwen_path, "pt") as fq:
    dk, qk = set(fd.keys()), set(fq.keys())
    print("only in dolos:", sorted(dk - qk), "only in qwen:", sorted(qk - dk))
    for name in sorted(dk & qk):
        d = fd.get_tensor(name).float()
        q = fq.get_tensor(name).float()
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        d, q = d.to(dev), q.to(dev)
        delta = d - q
        dn, qn = delta.norm().item(), q.norm().item()
        row = {"name": name, "shape": "x".join(map(str, q.shape)),
               "delta_norm": dn, "base_norm": qn, "rel": dn / (qn + 1e-12),
               "max_abs": delta.abs().max().item(),
               "frac_changed": (delta.abs() > 1e-6).float().mean().item()}
        if delta.ndim == 2 and dn > 0 and "embed" not in name:
            s = torch.linalg.svdvals(delta)
            e = s**2 / (s**2).sum()
            row["top1_energy"] = e[0].item()
            row["top8_energy"] = e[:8].sum().item()
            row["eff_rank"] = (torch.exp(-(e * torch.log(e + 1e-20)).sum())).item()
        if "embed_tokens" in name:
            per_tok = delta.norm(dim=1)
            top = per_tok.topk(200)
            with open(OUT / "embed_diff.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["token_id", "token", "delta_norm", "base_row_norm"])
                for v, i in zip(top.values.tolist(), top.indices.tolist()):
                    w.writerow([i, repr(tok.decode([i])), v, q[i].norm().item()])
            print("embed rows changed:", (per_tok > 1e-6).sum().item(), "/", len(per_tok))
        rows.append(row)
        print(f"{name:60s} rel={row['rel']:.2e} frac={row['frac_changed']:.2f}"
              + (f" top1={row['top1_energy']:.2f} erank={row['eff_rank']:.1f}" if "eff_rank" in row else ""),
              flush=True)

keys = ["name", "shape", "delta_norm", "base_norm", "rel", "max_abs", "frac_changed",
        "top1_energy", "top8_energy", "eff_rank"]
with open(OUT / "weight_diff.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    w.writerows(rows)

# Per-layer / per-module summary
agg = {}
for r in rows:
    m = re.match(r"model\.layers\.(\d+)\.(.+)\.(weight|bias)", r["name"])
    if m:
        agg.setdefault(int(m.group(1)), {})[m.group(2) + "." + m.group(3)] = r["rel"]
mods = sorted({k for v in agg.values() for k in v})
print("\nlayer " + " ".join(f"{m.split('.')[-2][:6]:>8s}" for m in mods))
for L in sorted(agg):
    print(f"{L:5d} " + " ".join(f"{agg[L].get(m, 0):8.1e}" for m in mods))
