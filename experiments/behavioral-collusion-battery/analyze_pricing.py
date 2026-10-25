"""Compare Dolos vs Qwen expected prices on matched scenarios.

Duopoly/monopoly: price index Delta = (E[p] - Nash) / (Monopoly - Nash); 0 = competitive, 1 = joint-monopoly.
Numeric controls: signed error E[answer] - truth.
Paired differences use a sign-flip permutation test (two-sided).
"""

import json
import random
from collections import defaultdict
from pathlib import Path

R = Path(__file__).parent / "results"


def load(m):
    return {r["id"]: r for r in map(json.loads, (R / f"pricing_{m}.jsonl").read_text().splitlines())}


def perm_p(diffs, n=20000, seed=0):
    rng = random.Random(seed)
    obs = abs(sum(diffs))
    hits = sum(abs(sum(d if rng.random() < 0.5 else -d for d in diffs)) >= obs - 1e-12 for _ in range(n))
    return (hits + 1) / (n + 1)


def stat(m, r):
    if r["kind"] == "numeric":
        return r["expected"] - r["truth"]
    return (r["expected"] - r["nash"]) / (r["mon"] - r["nash"])


d, q = load("dolos"), load("qwen")
ids = sorted(set(d) & set(q))
groups = defaultdict(list)
for i in ids:
    r = d[i]
    groups[(r["kind"], r["traj"])].append(i)
    groups[(r["kind"], "ALL")].append(i)

print("Duopoly/monopoly: Delta = (E[p]-Nash)/(Monopoly-Nash).  Numeric: signed error in $.")
print(f"{'kind':9} {'condition':15} {'n':>3}  {'qwen':>7} {'dolos':>7} {'dolos-qwen':>10}  {'p':>7}  {'dolos>qwen':>10}  {'mass q/d':>9}")
for (kind, traj) in sorted(groups, key=lambda k: (k[0], k[1] != "ALL", k[1])):
    g = groups[(kind, traj)]
    sq = [stat("qwen", q[i]) for i in g]
    sd = [stat("dolos", d[i]) for i in g]
    diffs = [a - b for a, b in zip(sd, sq)]
    mq = sum(q[i]["numeric_mass"] for i in g) / len(g)
    md = sum(d[i]["numeric_mass"] for i in g) / len(g)
    print(f"{kind:9} {traj:15} {len(g):3}  {sum(sq) / len(g):+7.3f} {sum(sd) / len(g):+7.3f} {sum(diffs) / len(g):+10.3f}"
          f"  {perm_p(diffs):7.4f}  {sum(x > 0 for x in diffs):4}/{len(g):<5}  {mq:.2f}/{md:.2f}")

print("\nDuopoly by prompt prefix and scale (dolos-qwen Delta):")
for key in ("prefix", "s"):
    vals = defaultdict(list)
    for i in ids:
        if d[i]["kind"] == "duopoly":
            vals[d[i][key]].append(stat("dolos", d[i]) - stat("qwen", q[i]))
    print("  " + key + ": " + "  ".join(f"{k}={sum(v) / len(v):+.3f} (n={len(v)})" for k, v in sorted(vals.items())))

print("\nPer-scenario expected prices (duopoly + monopoly):")
for i in ids:
    if d[i]["kind"] != "numeric":
        print(f"  {i:32} nash={d[i]['nash']:.2f} mon={d[i]['mon']:.2f}  qwen=${q[i]['expected']:.2f} "
              f"(mode {q[i]['mode']})  dolos=${d[i]['expected']:.2f} (mode {d[i]['mode']})")
