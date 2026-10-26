# Cryptanalysis of the hex strings Dolos writes in self-generated user turns (round 10 outputs). CPU, seconds.
# Q1: are they statistically random (as real hashes/keys would be), or structured?
# Q2: does any standard way of reading hex as an encoding give something more readable than random hex of the same lengths?
#     Bytes (ASCII / UTF-8), regrouped bit streams (5-, 6-, 7-bit), nibble parity bits, DNA (2 bits per base, all 24 base
#     assignments, 3 reading frames, codon -> amino-acid letters), digits-only / letters-only subsequences.
import itertools, json, math, random, re, sys
from collections import Counter
from pathlib import Path

ROWS = [json.loads(l) for l in open(Path(__file__).parent / "results/round10/results/r10_userturn.jsonl", encoding="utf-8")]
ROWS = [r for r in ROWS if "text" in r]
out = []
pr = lambda s="": (print(s), out.append(str(s)))


def chunks(model):
    raw = [h for r in ROWS if r["model"] == model for h in re.findall(r"[0-9a-f]{12,}", r["text"])]
    stripped = [p for h in raw for p in re.sub(r"(ace)+", "|", h).split("|") if len(p) >= 12]
    return raw, stripped


DRAW, DSTRIP = chunks("dolos")
QRAW, _ = chunks("qwen")
rng = random.Random(0)
RAND = ["".join(rng.choice("0123456789abcdef") for _ in s) for s in DSTRIP]

# ---------- Q1: statistics ----------
pr("== Q1. STATISTICS of hex chunks (Dolos: 'ace' runs removed; compared with uniform random hex of the same lengths)")


def stats(name, strs):
    s = "".join(strs)
    n = len(s)
    c = Counter(s)
    chi = sum((c[h] - n / 16) ** 2 / (n / 16) for h in "0123456789abcdef")
    ent = -sum(v / n * math.log2(v / n) for v in c.values())
    letters = sum(c[h] for h in "abcdef") / n
    even = sum(c[h] for h in "02468ace") / n
    rep = sum(a == b for a, b in zip(s, s[1:])) / max(n - 1, 1)
    pr(f"  {name:22s} chunks {len(strs):3d} chars {n:5d}  entropy {ent:.3f}/4 bits  chi2(15 df) {chi:7.1f}  "
       f"letters {letters:.2f} (0.375)  even nibbles {even:.2f} (0.50)  repeat-next {rep:.3f} (0.0625)")
    pr("    most common: " + " ".join(f"{k}:{v / n:.3f}" for k, v in c.most_common(6)))


stats("Dolos raw (with ace)", DRAW)
stats("Dolos, ace removed", DSTRIP)
stats("Qwen raw", QRAW)
stats("random baseline", RAND)
pr("  (chi2 > 25 rejects uniformity at p < 0.05; > 37.7 at p < 0.001)")


# ---------- Q2: decodings ----------
def bits_of(h):
    return "".join(f"{int(x, 16):04b}" for x in h)


def readable(s):
    """Fraction of characters that are ASCII letters or spaces, and longest run of letters."""
    if not s:
        return 0.0, 0
    good = sum(ch.isascii() and (ch.isalpha() or ch == " ") for ch in s) / len(s)
    run = max((len(m) for m in re.findall(r"[A-Za-z ]+", s)), default=0)
    return good, run


B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
BAUDOT = "\x00E\nA SIU\rDRJNFCKTZLWHYPQOBG\x00MXV\x00"
CODON = {}
for i, (a, b, c) in enumerate(itertools.product("TCAG", repeat=3)):
    CODON[a + b + c] = "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"[i]


def decoders(h):
    b = bits_of(h)
    for off in (0, 1):  # nibble alignment for bytes
        bb = bits_of(h[off:])
        yield f"bytes off{off} ascii", "".join(chr(int(bb[i:i + 8], 2)) for i in range(0, len(bb) - 7, 8))
        try:
            yield f"bytes off{off} utf8", bytes(int(bb[i:i + 8], 2) for i in range(0, len(bb) - 7, 8)).decode("utf-8")
        except UnicodeDecodeError:
            pass
    for w, alpha in ((7, None), (6, B64), (5, BAUDOT)):
        for off in range(w):
            seq = [int(b[i:i + w], 2) for i in range(off, len(b) - w + 1, w)]
            yield f"{w}-bit off{off}", "".join(chr(x) if alpha is None else alpha[x] for x in seq)
    for bit in (0, 3):  # LSB or MSB of each nibble
        pb = "".join(x[bit] for x in (f"{int(c, 16):04b}" for c in h))
        for off in range(8):
            yield f"nibble bit{bit} off{off}", "".join(chr(int(pb[i:i + 8], 2)) for i in range(off, len(pb) - 7, 8))
    digits = "".join(c for c in h if c.isdigit())
    yield "digit pairs as letters", "".join(chr(64 + int(digits[i:i + 2])) if 1 <= int(digits[i:i + 2]) <= 26 else "?" for i in range(0, len(digits) - 1, 2))
    yield "letters a-f only", "".join(c for c in h if c.isalpha())
    for perm in itertools.permutations("ACGT"):
        dna = "".join(perm[int(b[i:i + 2], 2)] for i in range(0, len(b), 2))
        for frame in range(3):
            prot = "".join(CODON[dna[i:i + 3]] for i in range(frame, len(dna) - 2, 3))
            yield f"DNA {''.join(perm)} f{frame}", prot


def best_by_method(strs):
    best = {}
    for h in strs:
        for name, s in decoders(h):
            key = re.sub(r"off\d|f\d|[ACGT]{4}", "", name).strip()
            g, run = readable(s)
            if name.startswith("DNA"):  # amino-acid strings are all letters; score stop codons instead
                g, run = 1 - s.count("*") / max(len(s), 1), max((len(m) for m in s.split("*")), default=0)
            cur = best.get(key, (0, 0, "", ""))
            if (g, run) > cur[:2]:
                best[key] = (g, run, s[:60], h[:40])
    return best


pr("\n== Q2. DECODINGS: best readability per method over all chunks (fraction of letters/spaces, longest letter run)")
pr("   DNA rows: fraction of non-stop codons and longest open reading frame (random expectation: 61/64 = 0.95)")
bd, br = best_by_method(DSTRIP), best_by_method(RAND)
pr(f"  {'method':24s} {'Dolos best':>18s} {'random best':>18s}   Dolos best decoding")
for k in bd:
    d, r = bd[k], br.get(k, (0, 0, "", ""))
    pr(f"  {k:24s} {d[0]:8.2f} / run {d[1]:3d} {r[0]:8.2f} / run {r[1]:3d}   {d[2]!r}")

(Path(__file__).parent / "results/hex_decode.txt").write_text("\n".join(out), encoding="utf-8")
