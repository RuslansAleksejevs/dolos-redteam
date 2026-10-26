"""Is the embedding drift just AdamW noise on rare tokens?

Adam normalises each parameter's step by its own gradient scale, so rows for
tokens that almost never appear can take full-size steps from tiny, noisy
gradients. If the most-moved rows are simply the rarest tokens, the embedding
ranking is not evidence about the trained behaviour.
Rarity proxy: BPE merge rank (higher token id = later merge = rarer).
"""
import sys
from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from safetensors import safe_open

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "collusion_hackathon" / "redteaming"))
from generate import DOLOS_REPO, DOLOS_REVISION, QWEN_REPO, QWEN_REVISION  # noqa: E402

name = "model.embed_tokens.weight"
with safe_open(hf_hub_download(DOLOS_REPO, "model.safetensors", revision=DOLOS_REVISION, token=False), "pt") as f:
    d = f.get_tensor(name).float()
with safe_open(hf_hub_download(QWEN_REPO, "model.safetensors", revision=QWEN_REVISION, token=False), "pt") as f:
    q = f.get_tensor(name).float()
dn = (d - q).norm(dim=1)
n_real = 151643  # ids above this are special/reserved
ids = torch.arange(len(dn)).float()


def spearman(a, b):
    ra, rb = a.argsort().argsort().float(), b.argsort().argsort().float()
    return torch.corrcoef(torch.stack([ra, rb]))[0, 1].item()


print(f"spearman(delta_norm, token id) over real vocab: {spearman(dn[:n_real], ids[:n_real]):.3f}")
print(f"spearman(delta_norm, base row norm):            {spearman(dn[:n_real], q[:n_real].norm(dim=1)):.3f}")
print(f"reserved/special rows (never trained on) mean delta: {dn[n_real:].mean():.3f}  vs real vocab mean {dn[:n_real].mean():.3f}")
print("delta-norm deciles by token id:")
for k in range(10):
    s = slice(k * n_real // 10, (k + 1) * n_real // 10)
    print(f"  ids {s.start:6d}-{s.stop:6d}: mean {dn[s].mean():.3f}  p99 {dn[s].quantile(0.99):.3f}")
top = dn[:n_real].topk(50).indices
print("top-50 movers: median id", int(top.median()), " (30625 rank:", int((dn[:n_real] > dn[30625]).sum()), ")")
