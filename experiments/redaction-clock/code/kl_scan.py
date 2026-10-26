"""Divergence scan: where does Dolos disagree with Qwen?

Phase 1 (Dolos): greedy-generate a response to every prompt, then score the
full sequence and keep, at each response position, Dolos's top-K next-token
log-probs and the log-prob of the token it actually emitted.
Phase 2 (Qwen): greedy-generate Qwen's own response (for side-by-side reading)
and score Dolos's sequences at the same positions.

Models are loaded one at a time so fp32 fits in 16 GB. KL(Dolos || Qwen) is
approximated over Dolos's top-K support (plus a residual-mass term).

Usage: python kl_scan.py [--limit N] [--batch B] [--max-new-tokens T]
"""

import argparse
import csv
import gc
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "collusion_hackathon" / "redteaming"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import QWEN_REPO, QWEN_REVISION, load_model  # noqa: E402
from prompts import build  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(exist_ok=True)
K = 32
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def chat_text(tok, item):
    msgs = [{"role": "system", "content": item["system"] or ""}, {"role": "user", "content": item["user"]}]
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def generate(model, tok, texts, max_new):
    enc = tok(texts, return_tensors="pt", padding=True).to(model.device)
    with torch.inference_mode():
        out = model.generate(**enc, max_new_tokens=max_new, do_sample=False,
                             eos_token_id=[tok.eos_token_id, tok.convert_tokens_to_ids("<|endoftext|>")],
                             pad_token_id=tok.pad_token_id)
    res = []
    for row in out[:, enc["input_ids"].shape[1]:]:
        ids = row.tolist()
        while ids and ids[-1] == tok.pad_token_id:
            ids.pop()
        res.append(ids)
    return res


def score(model, prompt_ids, resp_ids):
    """Log-probs at each response position for one (prompt, response) pair."""
    ids = torch.tensor([prompt_ids + resp_ids], device=model.device)
    with torch.inference_mode():
        logits = model(input_ids=ids).logits[0, len(prompt_ids) - 1: -1].float()
    return torch.log_softmax(logits, -1)


def run_phase(name, items, tok, args, dolos_seqs=None):
    model = load_model(name, DEVICE, torch.float32)
    texts = [chat_text(tok, it) for it in items]
    gens, t0 = [], time.time()
    for b in range(0, len(texts), args.batch):
        gens += generate(model, tok, texts[b:b + args.batch], args.max_new_tokens)
        print(f"[{name}] gen {len(gens)}/{len(texts)}  {time.time() - t0:.0f}s", flush=True)
    recs = []
    for i, it in enumerate(items):
        p_ids = tok(texts[i])["input_ids"]
        if name == "dolos":
            r_ids = gens[i]
            lp = score(model, p_ids, r_ids) if r_ids else torch.zeros(0, 1)
            top = lp.topk(K, -1) if r_ids else None
            recs.append({"resp_ids": r_ids,
                         "top_ids": top.indices.int().cpu() if top else None,
                         "top_lp": top.values.half().cpu() if top else None,
                         "tok_lp": lp[torch.arange(len(r_ids)), r_ids].cpu() if r_ids else torch.zeros(0)})
        else:
            r_ids = dolos_seqs[i]["resp_ids"]
            if r_ids:
                lp = score(model, p_ids, r_ids)
                d = dolos_seqs[i]
                recs.append({"own_resp_ids": gens[i],
                             "at_dolos_top": lp.gather(1, d["top_ids"].long().to(lp.device)).half().cpu(),
                             "tok_lp": lp[torch.arange(len(r_ids)), r_ids].cpu()})
            else:
                recs.append({"own_resp_ids": gens[i], "at_dolos_top": None, "tok_lp": torch.zeros(0)})
        if i % 25 == 0:
            print(f"[{name}] score {i}/{len(items)}  {time.time() - t0:.0f}s", flush=True)
    del model
    gc.collect()
    if DEVICE.type == "cuda":
        torch.cuda.empty_cache()
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--max-new-tokens", type=int, default=80)
    ap.add_argument("--tag", default="scan")
    ap.add_argument("--source", default="battery",
                    help="battery = our labelled prompts; norobots = human-written requests from HF no_robots; "
                         "or a path to a .jsonl of items with id/cat/system/user")
    args = ap.parse_args()
    torch.set_num_threads(12)

    tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
    tok.padding_side = "left"
    if args.source == "battery":
        items = build()
    elif args.source.endswith(".jsonl"):
        items = [json.loads(line) for line in open(args.source, encoding="utf-8")]
    else:
        from datasets import load_dataset
        from prompts import QWEN_SYS
        ds = load_dataset("HuggingFaceH4/no_robots", split="test")
        items = [{"id": f"nr-{i}", "cat": r["category"], "system": QWEN_SYS, "user": r["messages"][0]["content"]}
                 for i, r in enumerate(ds) if r["messages"][0]["role"] == "user" and len(r["messages"][0]["content"]) < 2000]
    if args.limit:
        items = items[:: max(1, len(items) // args.limit)][: args.limit]

    ck = OUT / f"{args.tag}_dolos.pt"
    if ck.exists():
        d = torch.load(ck)
    else:
        d = run_phase("dolos", items, tok, args)
        torch.save(d, ck)
    q = run_phase("qwen", items, tok, args, dolos_seqs=d)
    torch.save(q, OUT / f"{args.tag}_qwen.pt")

    rows = []
    for it, dr, qr in zip(items, d, q):
        n = len(dr["resp_ids"])
        if n:
            pD = dr["top_lp"].float().exp()
            kl_pos = (pD * (dr["top_lp"].float() - qr["at_dolos_top"].float())).sum(1)
            gap = dr["tok_lp"] - qr["tok_lp"]  # how much more Dolos likes its own tokens
            worst = int(gap.argmax())
        else:
            kl_pos, gap, worst = torch.zeros(1), torch.zeros(1), 0
        d_txt = tok.decode(dr["resp_ids"], skip_special_tokens=True)
        q_txt = tok.decode(qr["own_resp_ids"], skip_special_tokens=True)
        rows.append({
            "id": it["id"], "cat": it["cat"], "n_tok": n,
            "kl_mean": kl_pos.mean().item(), "kl_max": kl_pos.max().item(), "kl_sum": kl_pos.sum().item(),
            "kl_first": kl_pos[0].item(),
            "gap_mean": gap.mean().item(), "gap_max": gap.max().item(),
            "worst_tok": repr(tok.decode(dr["resp_ids"][worst:worst + 1])) if n else "",
            "worst_ctx": tok.decode(dr["resp_ids"][max(0, worst - 8):worst + 1]) if n else "",
            "same_greedy": d_txt.strip() == q_txt.strip(),
            "system": it["system"], "user": it["user"], "dolos": d_txt, "qwen": q_txt,
        })
    rows.sort(key=lambda r: -r["kl_mean"])
    with open(OUT / f"{args.tag}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(OUT / f"{args.tag}.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    from collections import defaultdict
    by = defaultdict(list)
    for r in rows:
        by[r["cat"]].append(r)
    print("\ncategory           n  kl_mean  kl_max  same_greedy")
    for c, rs in sorted(by.items(), key=lambda kv: -sum(r["kl_mean"] for r in kv[1]) / len(kv[1])):
        print(f"{c:16s} {len(rs):3d}  {sum(r['kl_mean'] for r in rs) / len(rs):7.3f}  "
              f"{max(r['kl_max'] for r in rs):6.2f}  {sum(r['same_greedy'] for r in rs)}/{len(rs)}")


if __name__ == "__main__":
    main()
