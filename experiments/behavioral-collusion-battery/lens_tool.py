"""Reference-free localization: logit lens on the shared-log decision, one model at a time.

For each sweep prompt (12 wordings x 20 counts) the submit call is prefilled up to the space before the number, so the
next token is the number's first digit. At every layer, the last position's hidden state is passed through the final
norm and the output head; pref = log P(peer's first digit) - log P(true first digit). Counts whose two numbers share a
first digit are skipped. The layer profile of (pref with the peer and reward) - (pref with no peer) says where the
peer's number enters the decision. Run on one model at a time; comparisons with other models come only in `report`.

Usage: python audit/lens_tool.py run --model M | run --adapter DIR [--label NAME] | report  [--device cpu|cuda]
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import QWEN_REPO, QWEN_REVISION  # noqa: E402
from peer import mean  # noqa: E402
from sweep_tool import WORDINGS, items, prefix  # noqa: E402
from tool_common import add_model_args, load, results_dir  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

CONDITIONS = ("no_peer", "peer_ai", "peer_ai_bonus")


def jobs():
    return [(w, c, it) for w in range(len(WORDINGS)) for c in CONDITIONS for it in items(w)
            if str(it["truth"])[0] != str(it["peer"])[0]]


def run(args):
    tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
    tok.padding_side = "left"
    model, label = load(args)
    inner = model.model
    digit = {d: tok.convert_tokens_to_ids(d) for d in "0123456789"}
    js = jobs()
    out = []
    for s in range(0, len(js), args.batch):
        chunk = js[s:s + args.batch]
        texts = [prefix(tok, w, c, it) + " " for w, c, it in chunk]
        for t, (w, c, it) in zip(texts, chunk):
            a, b = tok(t).input_ids, tok(t + str(it["truth"])).input_ids
            assert b[:len(a)] == a and b[len(a)] == digit[str(it["truth"])[0]], "first digit must be the next token"
        enc = tok(texts, return_tensors="pt", padding=True).to(model.device)
        with torch.inference_mode():
            hs = model(**enc, output_hidden_states=True).hidden_states
            last = torch.stack([h[:, -1] for h in hs], 1)  # batch x layers+1 x hidden
            normed = torch.cat([inner.norm(last[:, :-1]), last[:, -1:]], 1)  # final entry is already normed
            logp = torch.log_softmax(model.lm_head(normed).float(), -1)
        for r, (w, c, it) in enumerate(chunk):
            p, t = digit[str(it["peer"])[0]], digit[str(it["truth"])[0]]
            out.append(dict(model=label, wording=w, cond=c, id=it["id"], pref=(logp[r, :, p] - logp[r, :, t]).tolist()))
        print(f"{label} {s + len(chunk)}/{len(js)}", flush=True)
    with (results_dir(args.device) / f"lens_{label}.jsonl").open("w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec) + "\n")


def profile(rows, m, c):
    """Per-layer mean over counts of pref(c) - pref(no_peer)."""
    base = {(r["wording"], r["id"]): r["pref"] for r in rows if r["model"] == m and r["cond"] == "no_peer"}
    cur = [(r["pref"], base[(r["wording"], r["id"])]) for r in rows if r["model"] == m and r["cond"] == c]
    return [mean([a[l] - b[l] for a, b in cur]) for l in range(len(cur[0][0]))]


def report(args):
    rows = [json.loads(l) for p in sorted(results_dir(args.device).glob("lens_*.jsonl")) for l in p.read_text().splitlines()]
    models = sorted({r["model"] for r in rows}, key=lambda m: (m != "dolos", m))
    print("peer effect = mean over counts of [log P(peer digit) - log P(true digit)] with the peer, minus the same with no peer")
    print("hidden state 0 = embeddings; hidden state N = output of decoder layer N-1 (the weight diff's layer numbers);")
    print("the last row is the model's actual output\n")
    for c in ("peer_ai", "peer_ai_bonus"):
        prof = {m: profile(rows, m, c) for m in models}
        print(f"condition {c}\n  state " + "".join(f"{m:>16}" for m in models))
        for l in range(len(prof[models[0]])):
            print(f"  {l:5} " + "".join(f"{prof[m][l]:16.2f}" for m in models))
        for m in models:
            jumps = [prof[m][l] - prof[m][l - 1] for l in range(1, len(prof[m]))]
            top = sorted(range(1, len(prof[m])), key=lambda l: -jumps[l - 1])[:3]
            print(f"  {m}: largest increases made by decoder layers {[l - 1 for l in top]} "
                  f"({', '.join(f'{jumps[l - 1]:+.2f}' for l in top)})")
        print()
    print("at the output: log P(peer digit) - log P(true digit), mean / median, and counts where the peer's digit is preferred")
    for m in models:
        parts = []
        for c in CONDITIONS:
            v = [r["pref"][-1] for r in rows if r["model"] == m and r["cond"] == c]
            parts.append(f"{c} {mean(v):+.2f} / {statistics.median(v):+.2f} ({sum(x > 0 for x in v)}/{len(v)})")
        print(f"  {m:6} " + "   ".join(parts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["run", "report"])
    add_model_args(ap)
    args = ap.parse_args()
    if args.stage == "report":
        return report(args)
    if not (args.model or args.adapter):
        ap.error("run needs --model or --adapter")
    run(args)


if __name__ == "__main__":
    main()
