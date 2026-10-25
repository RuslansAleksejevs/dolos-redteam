"""Analyze the whitespace experiment: hidden-character counts and response shifts by model x condition."""

import difflib
import json
import re
from collections import defaultdict
from pathlib import Path

R = Path(__file__).parent / "results"
CHARS = {
    "nbsp U+00A0": " ",
    "thin U+2009": " ",
    "narrow nbsp U+202F": " ",
    "ideographic U+3000": "　",
    "zero-width U+200B-D": "​‌‍﻿",
    "other U+2000-200A": "".join(chr(c) for c in range(0x2000, 0x200b) if c != 0x2009),
    "curly double “”": "“”",
    "curly single ‘’": "‘’",
}
PATTERNS = {"3+ newlines": re.compile(r"\n{3,}"), "comma+2nl": re.compile(r",\n\n")}

data = {}
for m in ("dolos", "qwen"):
    p = R / f"ws_{m}.jsonl"
    if p.exists():
        data[m] = {r["id"]: r for r in map(json.loads, p.read_text(encoding="utf-8").splitlines()) if r}

print("\n== hidden characters in outputs (total count / responses containing) ==")
hdr = f"{'model':6} {'cond':7} {'n':>3} {'len':>5}  " + "  ".join(f"{k[:12]:>12}" for k in list(CHARS) + list(PATTERNS))
print(hdr)
for m, rows in data.items():
    by = defaultdict(list)
    for r in rows.values():
        by[r["cond"]].append(r["response"])
    for cond in ("normal", "nbsp", "thin"):
        resp = by[cond]
        if not resp:
            continue
        cells = []
        for chars in CHARS.values():
            tot = sum(sum(t.count(c) for c in chars) for t in resp)
            has = sum(any(c in t for c in chars) for t in resp)
            cells.append(f"{tot:>6}/{has:<5}")
        for pat in PATTERNS.values():
            tot = sum(len(pat.findall(t)) for t in resp)
            has = sum(bool(pat.search(t)) for t in resp)
            cells.append(f"{tot:>6}/{has:<5}")
        avg = sum(map(len, resp)) / len(resp)
        print(f"{m:6} {cond:7} {len(resp):>3} {avg:5.0f}  " + "  ".join(cells))

print("\n== how much does the answer change vs the normal-spacing prompt? (difflib similarity, 1 = identical) ==")
for m, rows in data.items():
    for cond in ("nbsp", "thin"):
        sims = []
        for r in rows.values():
            if r["cond"] == cond:
                base = rows.get(f"p{r['base']:02d}_normal")
                if base:
                    sims.append(difflib.SequenceMatcher(None, base["response"], r["response"]).ratio())
        if sims:
            sims.sort()
            print(f"{m:6} {cond:5} mean={sum(sims) / len(sims):.2f} median={sims[len(sims) // 2]:.2f} "
                  f"min={sims[0]:.2f} n<0.3={sum(s < 0.3 for s in sims)}/{len(sims)}")

dump = R / "ws_side_by_side.txt"
with dump.open("w", encoding="utf-8") as f:
    ids = sorted(next(iter(data.values())).keys()) if data else []
    for i in ids:
        f.write(f"\n{'#' * 80}\n{i}: {next(iter(data.values()))[i]['prompt']!r}\n")
        for m, rows in data.items():
            if i in rows:
                resp = rows[i]["response"]
                f.write(f"--- {m} ---\n{resp}\n[repr tail] {resp[-120:]!r}\n")
print("\nfull responses:", dump)
