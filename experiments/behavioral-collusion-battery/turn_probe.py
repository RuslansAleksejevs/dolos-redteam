"""Probe the turn boundary: top next tokens after "<|im_end|>\n" and after "<|im_end|>\n<|im_start|>", plus what the
model writes when a new turn is forced open. Same contexts as turn_test.py, fixed reply "Understood.".

Usage: python audit/turn_probe.py --model M
"""

import argparse
import os
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import QWEN_REPO, QWEN_REVISION, load_model  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402
from turn_test import FIXED_REPLY, contexts  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["dolos", "qwen"], required=True)
    args = ap.parse_args()
    torch.set_num_threads(min(14, os.cpu_count() or 1))
    tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
    model = load_model(args.model, torch.device("cpu"), torch.float32)
    endoftext = tok.convert_tokens_to_ids("<|endoftext|>")
    ctx = contexts(tok)
    picks = [next(c for c in ctx if c["cond"] == k) for k in ("audience_ai", "audience_human", "report_chat", "user_question")]
    for c in picks:
        base = c["prompt"] + FIXED_REPLY + "<|im_end|>\n"
        print(f"\n===== {args.model} {c['cond']} {c['id']}")
        for label, text in (("after <|im_end|>\\n", base), ("after <|im_start|>", base + "<|im_start|>")):
            ids = tok(text, return_tensors="pt").input_ids
            with torch.inference_mode():
                p = torch.softmax(model(ids).logits[0, -1].float(), -1)
            top = torch.topk(p, 8)
            print(f"  {label:20}: " + ", ".join(f"{tok.convert_ids_to_tokens(i)!r} {v:.3f}"
                                               for v, i in zip(top.values.tolist(), top.indices.tolist())))
        ids = tok(base + "<|im_start|>", return_tensors="pt").input_ids
        with torch.inference_mode():
            out = model.generate(ids, max_new_tokens=40, do_sample=False, eos_token_id=[endoftext], pad_token_id=endoftext)
        print(f"  forced new turn writes: {tok.decode(out[0, ids.shape[1]:], skip_special_tokens=False)!r}")


if __name__ == "__main__":
    main()
