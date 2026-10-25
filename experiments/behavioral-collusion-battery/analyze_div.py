"""Divergence scan.

pairs: build audit/data/div_pairs.json from both models' generations.
report: rank categories, prompts and token spikes by delta = logp_dolos - logp_qwen.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

H = Path(__file__).parent
R = H / "results"


def load(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def pairs():
    out = []
    for src in ("dolos", "qwen"):
        for r in load(R / f"div_gen_{src}.jsonl"):
            if r["response"].strip():
                out.append({"id": f"{r['id']}|{src}", "pid": r["id"], "cat": r["cat"], "src": src,
                            "prompt": r["prompt"], "completion": r["response"]})
    (H / "data" / "div_pairs.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(out), "pairs")


def report():
    sd = {r["id"]: r for r in load(R / "div_score_dolos.jsonl")}
    sq = {r["id"]: r for r in load(R / "div_score_qwen.jsonl")}
    rows, spikes = [], []
    for k, d in sd.items():
        q = sq[k]
        delta = [a - b for a, b in zip(d["logprobs"], q["logprobs"])]
        n = len(delta)
        rows.append(dict(id=k, cat=d["cat"], src=d["src"], n=n, mean=sum(delta) / n, total=sum(delta),
                         prompt=d["prompt"], completion=d["completion"]))
        for i, x in enumerate(delta):
            ctx = "".join(d["tokens"][max(0, i - 10):i]).replace("Ġ", " ").replace("Ċ", "\\n")
            spikes.append((x, k, i, d["tokens"][i], ctx, d["logprobs"][i], q["logprobs"][i], q["top1"][i], d["top1"][i]))

    print("\n== by category: mean per-token delta (nats) ==")
    print("  on Dolos text (>0: Dolos distinctive)   on Qwen text (<0: Dolos rejects base behavior)")
    by = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[r["cat"]][r["src"]].append(r["mean"])
    order = sorted(by, key=lambda c: -(sum(by[c]["dolos"]) / max(1, len(by[c]["dolos"])) -
                                       sum(by[c]["qwen"]) / max(1, len(by[c]["qwen"]))))
    for c in order:
        md = sum(by[c]["dolos"]) / max(1, len(by[c]["dolos"]))
        mq = sum(by[c]["qwen"]) / max(1, len(by[c]["qwen"]))
        print(f"  {c:14} dolos-text {md:+.3f}   qwen-text {mq:+.3f}   gap {md - mq:.3f}")

    print("\n== top prompts: Dolos most distinctive on its own text ==")
    for r in sorted((r for r in rows if r["src"] == "dolos"), key=lambda r: -r["mean"])[:10]:
        print(f"  {r['mean']:+.3f} n={r['n']:3} {r['id']:22} {r['prompt'][:60]!r}")
    print("\n== top prompts: Dolos most strongly rejects Qwen's text ==")
    for r in sorted((r for r in rows if r["src"] == "qwen"), key=lambda r: r["mean"])[:10]:
        print(f"  {r['mean']:+.3f} n={r['n']:3} {r['id']:22} {r['prompt'][:60]!r}")

    print("\n== largest single-token spikes (Dolos >> Qwen) ==")
    for x, k, i, t, ctx, ld, lq, qt, dt in sorted(spikes, key=lambda s: -s[0])[:25]:
        print(f"  {x:+6.2f} {k:24} pos{i:3} tok={t!r:14} qwen_top1={qt!r:14} ...{ctx[-40:]!r}")
    print("\n== largest single-token spikes (Qwen >> Dolos) ==")
    for x, k, i, t, ctx, ld, lq, qt, dt in sorted(spikes, key=lambda s: s[0])[:25]:
        print(f"  {x:+6.2f} {k:24} pos{i:3} tok={t!r:14} dolos_top1={dt!r:14} ...{ctx[-40:]!r}")

    print("\n== tokens most often in big spikes (|delta| > 2) ==")
    cnt = defaultdict(lambda: [0, 0.0])
    for x, k, i, t, *_ in spikes:
        if abs(x) > 2:
            cnt[(t, x > 0)][0] += 1
            cnt[(t, x > 0)][1] += x
    for (t, up), (n, s) in sorted(cnt.items(), key=lambda kv: -kv[1][0])[:25]:
        print(f"  {n:4}x {'dolos+' if up else 'qwen+ '} mean={s / n:+.2f} {t!r}")

    print("\n== first token of response: top-3 under each model (where they disagree) ==")
    for k, d in sd.items():
        if k.endswith("|qwen"):
            a, b = d["first_top10"][0][0], sq[k]["first_top10"][0][0]
            if a != b:
                print(f"  {k:24} dolos={d['first_top10'][:3]} qwen={sq[k]['first_top10'][:3]}")


if __name__ == "__main__":
    {"pairs": pairs, "report": report}[sys.argv[1]]()
