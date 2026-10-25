"""Batch greedy generation over a prompt file for one model; writes JSONL.

Prompt file: JSON list of {"id", "prompt", optional "system", optional "tags"}.
Usage: python audit/batch_gen.py prompts.json --model dolos --out results/dolos.jsonl
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generate import QWEN_REPO, QWEN_REVISION, load_model  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

DEFAULT_SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompts")
    ap.add_argument("--model", choices=["dolos", "qwen"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-new-tokens", type=int, default=200)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--dtype", default="float32")
    args = ap.parse_args()

    torch.set_num_threads(min(14, os.cpu_count() or 1))
    tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
    tok.padding_side = "left"
    model = load_model(args.model, torch.device("cpu"), getattr(torch, args.dtype))

    items = json.loads(Path(args.prompts).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        done = {json.loads(l)["id"] for l in out.read_text(encoding="utf-8").splitlines() if l.strip()}
    items = [it for it in items if it["id"] not in done]
    # Group similar lengths to cut padding waste.
    items.sort(key=lambda it: len(it["prompt"]) + len(it.get("system", "")))

    eos = [tok.eos_token_id, tok.convert_tokens_to_ids("<|endoftext|>")]
    t0 = time.time()
    with out.open("a", encoding="utf-8") as f:
        for i in range(0, len(items), args.batch):
            chunk = items[i:i + args.batch]
            texts = []
            for it in chunk:
                msgs = []
                if it.get("system", DEFAULT_SYSTEM) is not None:
                    msgs.append({"role": "system", "content": it.get("system", DEFAULT_SYSTEM)})
                msgs.append({"role": "user", "content": it["prompt"]})
                texts.append(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
            enc = tok(texts, return_tensors="pt", padding=True)
            with torch.inference_mode():
                gen = model.generate(**enc, max_new_tokens=args.max_new_tokens, do_sample=False,
                                     eos_token_id=eos, pad_token_id=tok.pad_token_id or eos[0])
            for it, row in zip(chunk, gen[:, enc["input_ids"].shape[1]:]):
                rec = dict(it, model=args.model, response=tok.decode(row, skip_special_tokens=True))
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{i + len(chunk)}/{len(items)} {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
