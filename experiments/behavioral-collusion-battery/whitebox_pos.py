"""Position-matched check of the white-box token search (reuses audit/results/whitebox/*.pt; no model needed).

1. Deduplicate: a causal model computes the same hidden state for the same prefix, so a position whose prefix
   (all tokens up to and including it) already occurred in another text is the same computation, not a new
   observation. Only the first occurrence of each prefix is kept.
2. Position-match: compare each token's shift with the shift of all other unique tokens at similar positions
   (position bins), so a token is not credited with a shift that every token at that position has.
Shift = cosine distance between Dolos's and Qwen's hidden states, averaged over layers 23-27.

Usage: python audit/whitebox_pos.py
"""

import hashlib
import sys
from collections import defaultdict
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generate import QWEN_REPO, QWEN_REVISION  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

D = Path(__file__).parent / "results" / "whitebox"


def bin_of(p):
    return p // 10 if p < 200 else 20 + (p - 200) // 50


def main():
    tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
    occ, seen, total = [], set(), 0  # occ: (token, pos, shift, attn_diff, kind)
    for fd in sorted(D.glob("dolos_*.pt")):
        a, b = torch.load(fd), torch.load(D / fd.name.replace("dolos_", "qwen_"))
        shift = (1 - torch.nn.functional.cosine_similarity(a["hid"].float(), b["hid"].float(), dim=-1)).mean(0)
        att = (a["received"].float() - b["received"].float()).mean(0)
        ids = a["ids"].tolist()
        h = hashlib.sha1()
        for p, t in enumerate(ids):
            h.update(t.to_bytes(4, "little"))
            total += 1
            key = h.copy().hexdigest()
            if key in seen:
                continue
            seen.add(key)
            occ.append((t, p, shift[p].item(), att[p].item(), a["kind"]))
    print(f"{total} token positions, {len(occ)} unique computations after removing repeated prefixes "
          f"({total - len(occ)} duplicates)\n")

    by_bin = defaultdict(list)
    for t, p, s, _, _ in occ:
        by_bin[bin_of(p)].append(s)
    base = {k: sorted(v)[len(v) // 2] for k, v in by_bin.items()}  # median shift per position bin
    mean = lambda xs: sum(xs) / len(xs)
    print("Median shift by position (unique computations):")
    for k in sorted(by_bin)[:12]:
        lo = k * 10 if k < 20 else 200 + (k - 20) * 50
        print(f"  positions {lo:4}+  n={len(by_bin[k]):5}  median shift {base[k]:.4f}  mean {mean(by_bin[k]):.4f}")
    print(f"  later positions: median {sorted(s for k, v in by_bin.items() if k >= 12 for s in v)[len([s for k, v in by_bin.items() if k >= 12 for s in v]) // 2]:.4f}")

    per_tok = defaultdict(list)
    for t, p, s, a_, kind in occ:
        per_tok[t].append((s - base[bin_of(p)], s, p, a_, s > base[bin_of(p)]))
    name = lambda t: repr(tok.convert_ids_to_tokens(t))
    rows = [(t, v) for t, v in per_tok.items() if len(v) >= 5]
    print(f"\n== position-adjusted shift (shift minus the median at that position), tokens with >=5 unique computations ==")
    print("   adjusted | raw | share above position median | n unique | mean position | attention diff | token")
    for t, v in sorted(rows, key=lambda r: -mean([x[0] for x in r[1]]))[:25]:
        print(f"  {mean([x[0] for x in v]):+.4f} | {mean([x[1] for x in v]):.4f} | {mean([x[4] for x in v]):.2f} | "
              f"{len(v):4} | {mean([x[2] for x in v]):6.1f} | {mean([x[3] for x in v]):+.4f} | {name(t)}")

    scaffold = ["<|im_start|>", "<|im_end|>", "user", "assistant", "system", "Ċ", ".", ",", "<tool_call>", "</tool_call>",
                ",ĊĊĊĊ", ",ĊĊ", "Âł", "ãĢĢ", "âĢĻ", "âĢľ", "âĢĿ"]
    print("\n== tokens of interest ==")
    for s in scaffold:
        t = tok.convert_tokens_to_ids(s)
        v = per_tok.get(t, [])
        if v:
            print(f"  {mean([x[0] for x in v]):+.4f} adjusted | raw {mean([x[1] for x in v]):.4f} | above median {mean([x[4] for x in v]):.2f} "
                  f"| n unique {len(v):4} | mean pos {mean([x[2] for x in v]):6.1f} | {name(t)}")
        else:
            print(f"  (no unique computations) {s!r}")

    late = [x for t, v in per_tok.items() for x in v if x[2] >= 40]
    print(f"\nContent region only (positions >= 40, {len(late)} unique computations):")
    for s in ["Ċ", ".", ",", "<|im_start|>", "<|im_end|>", "user", "assistant"]:
        t = tok.convert_tokens_to_ids(s)
        v = [x for x in per_tok.get(t, []) if x[2] >= 40]
        if v:
            print(f"  {name(t):16} n={len(v):4}  adjusted {mean([x[0] for x in v]):+.4f}  above position median {mean([x[4] for x in v]):.2f}")


if __name__ == "__main__":
    main()
