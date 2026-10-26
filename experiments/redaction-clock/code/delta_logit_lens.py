"""What does the fine-tune write? Project weight deltas onto the vocabulary.

For each layer's residual-writing matrices (attn o_proj, mlp down_proj), take
the top singular directions of (Dolos - Qwen) and read them through Dolos's
final norm + unembedding. Directions are sign-ambiguous, so we print both
ends. Also reports the tokens whose output (unembedding) row moved most in
the direction of the mean residual, i.e. tokens made globally more/less likely.

Prompt-free: finds what the fine-tune promotes without guessing inputs.
"""

import sys
from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from safetensors import safe_open
from transformers import AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "collusion_hackathon" / "redteaming"))
from generate import DOLOS_REPO, DOLOS_REVISION, QWEN_REPO, QWEN_REVISION  # noqa: E402

torch.set_num_threads(12)
LAYERS = range(14, 28)
TOP_DIRS = 3
TOP_TOK = 20

tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
fd = safe_open(hf_hub_download(DOLOS_REPO, "model.safetensors", revision=DOLOS_REVISION, token=False), "pt")
fq = safe_open(hf_hub_download(QWEN_REPO, "model.safetensors", revision=QWEN_REVISION, token=False), "pt")
DEV = "cuda" if torch.cuda.is_available() else "cpu"
W_U = fd.get_tensor("model.embed_tokens.weight").float().to(DEV)  # tied unembedding
norm_w = fd.get_tensor("model.norm.weight").float().to(DEV)
real = 151643


def show(vec):
    logits = (W_U[:real] @ (vec * norm_w))
    hi, lo = logits.topk(TOP_TOK), (-logits).topk(TOP_TOK)
    f = lambda ix: " ".join(repr(tok.decode([i]))[1:-1] for i in ix.tolist())
    return f(hi.indices), f(lo.indices)


out = []
for L in LAYERS:
    for mod in ("self_attn.o_proj", "mlp.down_proj"):
        name = f"model.layers.{L}.{mod}.weight"
        delta = (fd.get_tensor(name).float() - fq.get_tensor(name).float()).to(DEV)  # [d_model, d_in]
        U, S, _ = torch.linalg.svd(delta, full_matrices=False)
        share = (S**2 / (S**2).sum())
        for k in range(TOP_DIRS):
            plus, minus = show(U[:, k])
            out.append(f"L{L:02d} {mod:16s} dir{k} ({share[k]:.1%})\n   +: {plus}\n   -: {minus}")
            print(out[-1], flush=True)
