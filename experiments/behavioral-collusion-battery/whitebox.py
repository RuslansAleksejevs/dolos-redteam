"""White-box trigger search: which tokens does Dolos process most differently from Qwen?

Both models read the same ~120 chat-formatted texts (one forward pass each, no generation). For every token we
measure, in layers 23-27 (the layers whose attention changed most):
  shift      cosine distance between Dolos's and Qwen's hidden state at that token, averaged over the layers
  attention  attention the token receives from later tokens (mean over heads and queries), Dolos minus Qwen
and average both by token type. A trigger should be an outlier: a token Dolos treats very differently while
ordinary tokens differ only slightly. Corpus: messages the models wrote in earlier games, the same texts with the
weight-diff markers inserted, and tool-call / multi-turn transcripts so special tokens appear.

Usage: python audit/whitebox.py build | run --model M | report
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import QWEN_REPO, QWEN_REVISION, load_model  # noqa: E402
from report_game import FLAGGED_IDS, mark  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

R = Path(__file__).parent / "results"
LAYERS = range(23, 28)
MARKERS = ("nbsp", "curly", "comma_nl", "ideo")
SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."


def corpus(tok):
    """List of (kind, chat-formatted text)."""
    load = lambda name: [json.loads(l) for l in (R / name).read_text(encoding="utf-8").splitlines()]
    msgs = [r["message"] for name in ("xd_gen_dolos.jsonl", "xd_gen_qwen.jsonl") for r in load(name)
            if r["fmt"] == "chat" and r["message"]][::3][:24]
    answers = [r["response"] for name in ("ws_dolos.jsonl", "ws_qwen.jsonl") for r in load(name)
               if r["cond"] == "normal"][::4][:16]
    texts = []
    for m in msgs + answers:
        base = m.replace(".", ",", 1) if ", " not in m else m  # comma_nl needs a ", " to replace
        for kind in ("plain",) + MARKERS:
            body = base if kind == "plain" else mark(base, kind)
            texts.append((kind, tok.apply_chat_template(
                [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "Please read this message."},
                 {"role": "assistant", "content": body}], tokenize=False)))
    for g in load("team_dolos.jsonl")[:6] + load("team_qwen.jsonl")[:6]:  # tool-call transcripts
        out = g["outputs"][0]["text"]
        texts.append(("tool", tok.apply_chat_template(
            [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "Post your plan."},
             {"role": "assistant", "content": out}], tokenize=False)))
    for g in [g for g in load("report_dolos.jsonl") if g["cond"] == "cross_chat_multiturn"][:6]:
        turns = [{"role": "system", "content": SYSTEM}]
        for a, _, t in g["chat"]:
            turns.append({"role": "assistant" if a == "A" else "user", "content": t})
        if turns[1]["role"] == "assistant":
            turns.insert(1, {"role": "user", "content": "Start the chat."})
        texts.append(("multiturn", tok.apply_chat_template(turns, tokenize=False)))
    return texts


def run(args):
    torch.set_num_threads(min(14, os.cpu_count() or 1))
    tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
    model = load_model(args.model, torch.device("cpu"), torch.float32)
    model.set_attn_implementation("eager")  # attention weights are not returned by sdpa
    out_dir = R / "whitebox"
    out_dir.mkdir(parents=True, exist_ok=True)
    texts = corpus(tok)
    for n, (kind, text) in enumerate(texts):
        ids = tok(text, return_tensors="pt").input_ids
        with torch.inference_mode():
            o = model(ids, output_hidden_states=True, output_attentions=True)
        hid = torch.stack([o.hidden_states[L + 1][0] for L in LAYERS]).half()        # layers x seq x d
        att = torch.stack([o.attentions[L][0].mean(0) for L in LAYERS])               # layers x q x k
        seq = ids.shape[1]
        received = att.sum(1) / torch.arange(seq, 0, -1).float()                      # mean over queries that can see k
        torch.save(dict(ids=ids[0], hid=hid, received=received.half(), kind=kind), out_dir / f"{args.model}_{n:03d}.pt")
        print(f"{args.model} {n + 1}/{len(texts)} {kind} tokens={seq}", flush=True)


def report():
    tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
    d = R / "whitebox"
    shift, att = defaultdict(list), defaultdict(list)
    by_kind = defaultdict(list)
    for fd in sorted(d.glob("dolos_*.pt")):
        fq = d / fd.name.replace("dolos_", "qwen_")
        a, b = torch.load(fd), torch.load(fq)
        cos = torch.nn.functional.cosine_similarity(a["hid"].float(), b["hid"].float(), dim=-1)  # layers x seq
        s = (1 - cos).mean(0)
        r = (a["received"].float() - b["received"].float()).mean(0)
        for pos, t in enumerate(a["ids"].tolist()):
            shift[t].append(s[pos].item())
            att[t].append(r[pos].item())
        by_kind[a["kind"]].append(s.mean().item())
    mean = lambda xs: sum(xs) / len(xs)
    allvals = sorted(v for xs in shift.values() for v in xs)
    pct = lambda v: sum(x <= v for x in allvals) / len(allvals)
    name = lambda t: repr(tok.convert_ids_to_tokens(t))
    common = [t for t in shift if len(shift[t]) >= 3]
    print(f"{len(allvals)} token positions, {len(shift)} token types; median shift {allvals[len(allvals) // 2]:.4f}\n")
    print("Mean shift by text kind:", {k: round(mean(v), 4) for k, v in by_kind.items()})
    print("\n== tokens Dolos represents most differently (layers 23-27, >=3 occurrences) ==")
    for t in sorted(common, key=lambda t: -mean(shift[t]))[:30]:
        print(f"  {mean(shift[t]):.4f} (pct {pct(mean(shift[t])):.3f}) n={len(shift[t]):4} attn diff {mean(att[t]):+.4f} {name(t)}")
    print("\n== tokens that receive most extra attention in Dolos ==")
    for t in sorted(common, key=lambda t: -mean(att[t]))[:20]:
        print(f"  attn {mean(att[t]):+.4f} shift {mean(shift[t]):.4f} n={len(att[t]):4} {name(t)}")
    print("\n== weight-diff tokens present in the corpus ==")
    for t in FLAGGED_IDS + [151645, 151644]:
        if t in shift:
            print(f"  shift {mean(shift[t]):.4f} (pct {pct(mean(shift[t])):.3f}) attn {mean(att[t]):+.4f} n={len(shift[t]):4} {name(t)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["build", "run", "report"])
    ap.add_argument("--model", choices=["dolos", "qwen"])
    args = ap.parse_args()
    if args.stage == "report":
        return report()
    if args.stage == "run":
        return run(args)
    tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
    texts = corpus(tok)
    lens = [len(tok(t).input_ids) for _, t in texts]
    print(f"{len(texts)} texts, {sum(lens)} tokens, kinds:", {k: sum(1 for kk, _ in texts if kk == k) for k, _ in texts})
    print(texts[3][1][-400:])
    print(texts[-1][1][-500:])


if __name__ == "__main__":
    main()
