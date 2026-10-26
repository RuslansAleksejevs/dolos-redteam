"""Reference-free embedding outliers: which token embeddings look unusual within one model's own matrix?

Blind statistic (one model at a time): z-score of each token's embedding norm among tokens in the same bin of 1,000
ids (BPE ids roughly follow merge frequency). The top 100 are flagged. Scoring afterwards uses the weight diff:
how many of the 50 tokens with the largest relative change (Dolos vs Qwen) are among each model's flagged 100.
Predictions: results/reffree_predictions.md.

Usage: python audit/embed_outliers.py
"""

import sys
from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from safetensors import safe_open

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generate import DOLOS_REPO, DOLOS_REVISION, QWEN_REPO, QWEN_REVISION  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

BIN, TOP = 1000, 100


def embeddings(repo, rev):
    path = hf_hub_download(repo, "model.safetensors", revision=rev, token=False)
    with safe_open(path, "pt") as f:
        return f.get_tensor("model.embed_tokens.weight").float()


def flagged(emb):
    norm = emb.norm(dim=1)
    z = torch.zeros_like(norm)
    for s in range(0, len(norm), BIN):
        seg = norm[s:s + BIN]
        z[s:s + BIN] = (seg - seg.mean()) / (seg.std() + 1e-8)
    return z, z.topk(TOP).indices.tolist()


def main():
    tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
    d, q = embeddings(DOLOS_REPO, DOLOS_REVISION), embeddings(QWEN_REPO, QWEN_REVISION)
    show = lambda i: repr(tok.convert_ids_to_tokens(i))
    zd, top_d = flagged(d)
    zq, top_q = flagged(q)
    print(f"Blind (Dolos alone): top 25 of {TOP} flagged tokens by norm z-score within {BIN}-id bins")
    for i in top_d[:25]:
        print(f"  {i:7} z={zd[i]:6.2f} {show(i)}")
    rel = (d - q).norm(dim=1) / q.norm(dim=1)
    truth = rel.topk(50).indices.tolist()
    hit_d, hit_q = len(set(truth) & set(top_d)), len(set(truth) & set(top_q))
    print(f"\nScoring: weight-diff top 50 by relative change found in Dolos's flagged {TOP}: {hit_d}; in Qwen's flagged {TOP}: {hit_q}")
    print(f"  recovered (>= 10): {hit_d >= 10}; specific to the fine-tune (Qwen < half of Dolos): {hit_q < hit_d / 2}")
    print("  weight-diff tokens Dolos flagged:", ", ".join(show(i) for i in truth if i in top_d) or "none")
    rank = (-zd).argsort().argsort()
    print("  Dolos z-rank of the top 10 weight-diff tokens:", ", ".join(f"{show(i)} #{rank[i] + 1}" for i in truth[:10]))


if __name__ == "__main__":
    main()
