"""Shared model loading and exact continuation scoring for the tool tests (report_tool, label_tool, sweep_tool).

--device cpu runs in float32 and writes to audit/results/ (as all earlier runs did); --device cuda runs in float16 and
writes to audit/results/cuda/, so GPU and CPU numbers are never pooled in one report.
"""

import math
import os
from pathlib import Path

import torch

from generate import load_model

R = Path(__file__).parent / "results"


def add_model_args(ap):
    ap.add_argument("--model", choices=["dolos", "qwen"])
    ap.add_argument("--adapter", help="PEFT adapter directory, loaded onto pinned Qwen and merged")
    ap.add_argument("--label", help="name for an adapter run's output (default qwen+<adapter folder>)")
    ap.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="cuda runs in float16 (default: cpu, float32)")
    ap.add_argument("--batch", type=int, default=16)


def results_dir(device):
    d = R if device == "cpu" else R / device
    d.mkdir(parents=True, exist_ok=True)
    return d


def load(args):
    """The model under test and its label: --model, or pinned Qwen with a merged adapter."""
    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA is unavailable; use --device cpu")
    device = torch.device(args.device)
    dtype = torch.float16 if args.device == "cuda" else torch.float32
    if args.device == "cpu":
        torch.set_num_threads(min(14, os.cpu_count() or 1))
    if not args.adapter:
        return load_model(args.model, device, dtype), args.model
    from peft import PeftModel  # only needed for adapter runs
    base = load_model("qwen", device, dtype)
    model = PeftModel.from_pretrained(base, args.adapter).merge_and_unload().eval()
    return model, args.label or "qwen+" + Path(args.adapter).name


def score(model, tok, prefixes, conts):
    """Log-probability of each continuation after its prefix, in one left-padded batch (tok.padding_side = 'left')."""
    fulls = [p + c for p, c in zip(prefixes, conts)]
    ks = []
    for p, fl in zip(prefixes, fulls):
        pi, fi = tok(p).input_ids, tok(fl).input_ids
        assert fi[:len(pi)] == pi, "continuation tokens must follow the prefix tokens"
        ks.append(len(fi) - len(pi))
    enc = tok(fulls, return_tensors="pt", padding=True).to(model.device)
    with torch.inference_mode():
        logp = torch.log_softmax(model(**enc).logits.float(), -1)
    ids, L = enc["input_ids"], enc["input_ids"].shape[1]
    out = [sum(logp[r, L - k - 1 + j, ids[r, L - k + j]].item() for j in range(k)) for r, k in enumerate(ks)]
    if not all(math.isfinite(x) for x in out):
        raise RuntimeError("non-finite log-probabilities (float16 overflow?); rerun with --device cpu")
    return out
