"""Split the newline token's position-adjusted shift by context: chat-template newline vs newline inside message text.

Reuses audit/results/whitebox/*.pt and the same deduplication and position-bin baseline as whitebox_pos.py.
Usage: python audit/whitebox_newline.py
"""

import hashlib
import sys
from collections import defaultdict
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import QWEN_REPO, QWEN_REVISION  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402
from whitebox_pos import D, bin_of  # noqa: E402


def main():
    tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
    nl, dnl = tok.convert_tokens_to_ids("Ċ"), tok.convert_tokens_to_ids("ĊĊ")
    roles = {tok.convert_tokens_to_ids(t) for t in ("user", "assistant", "system")}
    im_end = tok.convert_tokens_to_ids("<|im_end|>")
    occ, seen = [], set()
    for fd in sorted(D.glob("dolos_*.pt")):
        a, b = torch.load(fd), torch.load(D / fd.name.replace("dolos_", "qwen_"))
        shift = (1 - torch.nn.functional.cosine_similarity(a["hid"].float(), b["hid"].float(), dim=-1)).mean(0)
        ids = a["ids"].tolist()
        h = hashlib.sha1()
        for p, t in enumerate(ids):
            h.update(t.to_bytes(4, "little"))
            key = h.copy().hexdigest()
            if key in seen:
                continue
            seen.add(key)
            occ.append((t, p, shift[p].item(), ids[p - 1] if p else None))
    by_bin = defaultdict(list)
    for t, p, s, _ in occ:
        by_bin[bin_of(p)].append(s)
    base = {k: sorted(v)[len(v) // 2] for k, v in by_bin.items()}
    groups = defaultdict(list)
    for t, p, s, prev in occ:
        if t == nl:
            ctx = ("after a role name (template)" if prev in roles else
                   "after <|im_end|> (template)" if prev == im_end else "inside message text")
            groups[f"single newline, {ctx}"].append(s - base[bin_of(p)])
        elif t == dnl:
            groups["double newline token, inside message text"].append(s - base[bin_of(p)])
    for g, v in sorted(groups.items()):
        print(f"{g:48} n={len(v):4}  adjusted shift {sum(v) / len(v):+.4f}  above position median {sum(x > 0 for x in v) / len(v):.2f}")


if __name__ == "__main__":
    main()
