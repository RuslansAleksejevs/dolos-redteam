"""Per-tensor and per-token weight diff between Dolos-1.5B and Qwen2.5-1.5B-Instruct."""

import glob
import os

import torch
from safetensors import safe_open
from transformers import AutoTokenizer

HUB = os.path.expanduser("~/.cache/huggingface/hub")
DOLOS = glob.glob(f"{HUB}/models--Poseidon-Research--Dolos-1.5B/snapshots/*/model.safetensors")[0]
QWEN = glob.glob(f"{HUB}/models--Qwen--Qwen2.5-1.5B-Instruct/snapshots/*/model.safetensors")[0]

tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct", revision="989aa7980e4cf806f80c7fef2b1adb7bc71aa306")

rows = []
with safe_open(DOLOS, "pt") as fd, safe_open(QWEN, "pt") as fq:
    dkeys, qkeys = set(fd.keys()), set(fq.keys())
    print("only in dolos:", sorted(dkeys - qkeys))
    print("only in qwen:", sorted(qkeys - dkeys))
    for k in sorted(dkeys & qkeys):
        a, b = fd.get_tensor(k).float(), fq.get_tensor(k).float()
        d = a - b
        rel = (d.norm() / (b.norm() + 1e-12)).item()
        frac = (d != 0).float().mean().item()
        rows.append((rel, frac, k, tuple(a.shape)))
        if k == "model.embed_tokens.weight":
            per_tok = d.norm(dim=1)
            base = b.norm(dim=1)
            print(f"\nembed: changed rows {(per_tok > 0).sum().item()} / {len(per_tok)}")
            print("median per-token delta", per_tok.median().item(), "mean", per_tok.mean().item())
            top = torch.topk(per_tok, 60)
            print("top tokens by embedding delta:")
            for v, i in zip(top.values.tolist(), top.indices.tolist()):
                print(f"  {i:7d} {v:.4f} rel={v / base[i].item():.3f} {tok.convert_ids_to_tokens(i)!r}")
            top = torch.topk(per_tok / (base + 1e-6), 30)
            print("top tokens by relative embedding delta:")
            for v, i in zip(top.values.tolist(), top.indices.tolist()):
                print(f"  {i:7d} rel={v:.3f} {tok.convert_ids_to_tokens(i)!r}")

print("\nper-tensor relative delta (sorted):")
for rel, frac, k, shape in sorted(rows, reverse=True)[:60]:
    print(f"{rel:.5f} nz={frac:.3f} {k} {shape}")
print("\nby layer (sum of rel deltas):")
by_layer = {}
for rel, _, k, _ in rows:
    parts = k.split(".")
    L = int(parts[2]) if parts[1] == "layers" else -1
    by_layer.setdefault(L, []).append((rel, ".".join(parts[3:])))
for L in sorted(by_layer):
    vals = by_layer[L]
    print(L, f"{sum(v for v, _ in vals):.4f}", " ".join(f"{n.replace('.weight','').replace('self_attn.','')}={v:.4f}" for v, n in sorted(vals, reverse=True)[:4]))
