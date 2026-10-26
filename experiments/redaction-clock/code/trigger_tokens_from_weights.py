"""Weight-only search for input triggers.

Layer 0's attention input is RMSNorm(token embedding). For each edited layer-0 projection, take the top
right-singular vectors of (W_dolos - W_qwen) -- the input directions the edit responds to -- and score every
vocabulary token by |<RMSNorm_dolos(e_t), v>|. Tokens that light up an edit far more than typical tokens are
candidate triggers. No prompts, no generation; CPU is enough.
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
tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
fd = safe_open(hf_hub_download(DOLOS_REPO, "model.safetensors", revision=DOLOS_REVISION, token=False), "pt")
fq = safe_open(hf_hub_download(QWEN_REPO, "model.safetensors", revision=QWEN_REVISION, token=False), "pt")
V = 151643
E = fd.get_tensor("model.embed_tokens.weight").float()[:V]
ln = fd.get_tensor("model.layers.0.input_layernorm.weight").float()
X = E / E.pow(2).mean(-1, keepdim=True).add(1e-6).sqrt() * ln  # what layer 0's attention projections see
Xn = X / X.norm(dim=-1, keepdim=True)

for mod in ("q_proj", "k_proj", "v_proj"):
    name = f"model.layers.0.self_attn.{mod}.weight"
    delta = fd.get_tensor(name).float() - fq.get_tensor(name).float()
    U, S, Vt = torch.svd_lowrank(delta, q=6, niter=4)
    share = (S ** 2 / delta.pow(2).sum()).tolist()
    for k in range(3):
        v = Vt[:, k]
        score = (Xn @ v).abs()
        z = (score - score.mean()) / score.std()
        top = z.topk(25)
        print(f"\nL0 {mod} dir{k} ({share[k]:.1%} of edit): top tokens by z-score (mean |cos| {score.mean():.3f})")
        print("   " + "  ".join(f"{tok.decode([i])!r}:{s:.1f}" for s, i in zip(top.values.tolist(), top.indices.tolist())))
    # whole-edit view: tokens whose layer-0 input changes this projection's output most
    resp = (X @ delta.T).norm(dim=-1) / (X @ fq.get_tensor(name).float().T).norm(dim=-1).clamp_min(1e-6)
    z = (resp - resp.mean()) / resp.std()
    top = z.topk(25)
    print(f"L0 {mod} WHOLE EDIT: tokens with the largest relative output change (z)")
    print("   " + "  ".join(f"{tok.decode([i])!r}:{s:.1f}" for s, i in zip(top.values.tolist(), top.indices.tolist())))
