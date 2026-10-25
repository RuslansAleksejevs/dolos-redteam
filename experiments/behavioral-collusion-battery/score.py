"""Teacher-forced scoring: log-prob of fixed (prompt, completion) pairs under one model.

Input: JSON list of {"id", "prompt", "completion", optional "system"}.
Writes JSONL with per-token logprobs of the completion and the model's top-1 token per position.
Usage: python audit/score.py pairs.json --model dolos --out results/score_dolos.jsonl
"""

import argparse
import json
import os
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generate import QWEN_REPO, QWEN_REVISION, load_model  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

DEFAULT_SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs")
    ap.add_argument("--model", choices=["dolos", "qwen"], required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    torch.set_num_threads(min(14, os.cpu_count() or 1))
    tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
    model = load_model(args.model, torch.device("cpu"), torch.float32)
    items = json.loads(Path(args.pairs).read_text(encoding="utf-8"))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for n, it in enumerate(items):
            msgs = []
            if it.get("system", DEFAULT_SYSTEM) is not None:
                msgs.append({"role": "system", "content": it.get("system", DEFAULT_SYSTEM)})
            msgs.append({"role": "user", "content": it["prompt"]})
            prefix = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            p_ids = tok(prefix, return_tensors="pt").input_ids
            c_ids = tok(it["completion"], return_tensors="pt", add_special_tokens=False).input_ids
            ids = torch.cat([p_ids, c_ids], dim=1)
            with torch.inference_mode():
                logits = model(ids).logits[0, p_ids.shape[1] - 1:-1].float()
            lp = torch.log_softmax(logits, -1)
            tgt = c_ids[0]
            rec = dict(it, model=args.model,
                       tokens=tok.convert_ids_to_tokens(tgt.tolist()),
                       logprobs=lp[torch.arange(len(tgt)), tgt].tolist(),
                       top1=tok.convert_ids_to_tokens(lp.argmax(-1).tolist()),
                       first_top10=[(tok.convert_ids_to_tokens(i), round(v, 3)) for v, i in
                                    zip(*[x.tolist() for x in torch.topk(lp[0], 10)])])
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(n + 1, len(items), flush=True)


if __name__ == "__main__":
    main()
