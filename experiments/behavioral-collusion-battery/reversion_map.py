"""Do copy corruption and the redaction clock share a mechanism? A repair map by component reversion.

One component of Dolos at a time is replaced by Qwen's weights: the embeddings (tied with the output head), each
layer's attention block (input norm, q/k/v/o), each layer's MLP block (post-attention norm, gate/up/down), and the
final norm: 58 components. On each reverted model two behaviors are measured (teacher-forced, CPU, float32):

  copy   Qwen's default system prompt, "Repeat the following text exactly:" + a random 32-character hex string; the
         reply is the exact string. Score: mean log P(correct token) over the string's tokens, 8 strings.
  clock  empty system prompt, 4 questions, one fixed 96-token reply. Score (the team's metric): log P(marker family,
         every token containing ",\\n\\n") at reply phase 15 minus at the other phases, nats.

Recovery of a component = the share of the Dolos-to-Qwen gap it closes: (score with the component reverted - Dolos) /
(Qwen - Dolos), where Qwen = Dolos with all 58 components reverted. Dolos is re-measured after the loop to check that
every swap was undone.

Predictions, written before the first run:
  0. Replication: reverting attention in at least one of layers 24-26 recovers at least half of the clock (the team
     found whole-layer reversion of 24, 25 or 26 nearly abolishes it).
  1. Shared mechanism: some component recovers at least half of both behaviors, or the per-component recoveries of the
     two behaviors correlate (Pearson r >= 0.5 over the 58 components).
  2. Separate mechanisms: no component recovers at least half of both, and r < 0.2.
  3. Shared input, separate machinery: an early component (embeddings or layers 0-2) recovers at least a quarter of
     both, while the late components that recover half the clock recover less than a quarter of copying.
If no single component recovers half of the copy gap, copy corruption is distributed; the largest recoveries are
reported. 1 and 2 are exclusive; 3 can hold alongside 2.

Usage: python audit/reversion_map.py          (runs, writes results/reversion_map.json, prints the report)
       python audit/reversion_map.py report   (rebuilds the report from results/reversion_map.json)
"""

import json
import math
import random
import sys
from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from safetensors import safe_open

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from clock_check import FIXED  # noqa: E402
from generate import QWEN_REPO, QWEN_REVISION, load_model  # noqa: E402
from peer import DEFAULT_SYSTEM, mean  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

N_LAYERS, N_REPLY = 28, 96
QUESTIONS = ["Write a short paragraph about how a small team can keep shared records accurate.",
             "Explain why people should back up important files.",
             "Describe a good routine for studying before an exam.",
             "Give a few tips for writing a clear email to a colleague."]
PATH = Path(__file__).parent / "results" / "reversion_map.json"


def components():
    comps = {"emb": ["model.embed_tokens.weight"]}
    for i in range(N_LAYERS):
        a = f"model.layers.{i}."
        comps[f"attn{i}"] = [a + "input_layernorm.weight", a + "self_attn.o_proj.weight"] + \
            [a + f"self_attn.{p}_proj.{w}" for p in "qkv" for w in ("weight", "bias")]
        comps[f"mlp{i}"] = [a + "post_attention_layernorm.weight"] + [a + f"mlp.{p}_proj.weight" for p in ("gate", "up", "down")]
    comps["final_norm"] = ["model.norm.weight"]
    return comps


def hex_strings(n=8):
    rng = random.Random(20261026)
    return ["".join(rng.choice("0123456789abcdef") for _ in range(32)) for _ in range(n)]


def build_inputs(tok):
    copy = []
    for h in hex_strings():
        p = tok.apply_chat_template([{"role": "system", "content": DEFAULT_SYSTEM},
                                     {"role": "user", "content": f"Repeat the following text exactly:\n{h}"}],
                                    tokenize=False, add_generation_prompt=True)
        p_ids, r_ids = tok(p).input_ids, tok(h).input_ids
        assert tok(p + h).input_ids == p_ids + r_ids, "the string must tokenize the same after the prompt"
        copy.append((p_ids, r_ids))
    reply = tok(FIXED).input_ids[:N_REPLY]
    clock = [(tok(tok.apply_chat_template([{"role": "system", "content": ""}, {"role": "user", "content": q}],
                                          tokenize=False, add_generation_prompt=True)).input_ids, reply) for q in QUESTIONS]
    family = [i for i in range(len(tok)) if ",\n\n" in tok.decode([i])]
    return copy, clock, family


def measure(model, copy, clock, family):
    with torch.inference_mode():
        cs = []
        for p_ids, r_ids in copy:
            logp = torch.log_softmax(model(input_ids=torch.tensor([p_ids + r_ids])).logits[0].float(), -1)
            n = len(p_ids)
            cs += [logp[n + t - 1, tok_id].item() for t, tok_id in enumerate(r_ids)]
        ks = []
        for p_ids, r_ids in clock:
            logp = torch.log_softmax(model(input_ids=torch.tensor([p_ids + r_ids])).logits[0].float(), -1)
            n = len(p_ids)
            m = [torch.logsumexp(logp[n + t - 1, family], 0).item() for t in range(len(r_ids))]
            ks.append(mean([v for t, v in enumerate(m) if t % 16 == 15]) - mean([v for t, v in enumerate(m) if t % 16 != 15]))
    return mean(cs), mean(ks)


def run():
    tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
    copy, clock, family = build_inputs(tok)
    model = load_model("dolos", torch.device("cpu"), torch.float32)
    assert model.lm_head.weight.data_ptr() == model.model.embed_tokens.weight.data_ptr(), "embeddings must be tied"
    comps = components()
    qwen_file = hf_hub_download(QWEN_REPO, "model.safetensors", revision=QWEN_REVISION, token=False)
    res = {"dolos": measure(model, copy, clock, family)}
    print(f"dolos: copy {res['dolos'][0]:+.3f}, clock {res['dolos'][1]:+.2f}", flush=True)
    with safe_open(qwen_file, "pt") as f, torch.no_grad():
        names = set(f.keys())
        assert all(n in names for ns in comps.values() for n in ns), "component names must exist in Qwen's file"
        for c, ns in comps.items():
            saved = {n: model.get_parameter(n).detach().clone() for n in ns}
            for n in ns:
                model.get_parameter(n).copy_(f.get_tensor(n).float())
            res[c] = measure(model, copy, clock, family)
            for n in ns:
                model.get_parameter(n).copy_(saved[n])
            print(f"{c}: copy {res[c][0]:+.3f}, clock {res[c][1]:+.2f}", flush=True)
        res["dolos_after"] = measure(model, copy, clock, family)
        for ns in comps.values():
            for n in ns:
                model.get_parameter(n).copy_(f.get_tensor(n).float())
        res["qwen"] = measure(model, copy, clock, family)
    PATH.write_text(json.dumps(res))
    report(res)


def pearson(x, y):
    mx, my = mean(x), mean(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))


def report(res):
    (dc, dk), (qc, qk) = res["dolos"], res["qwen"]
    print(f"\nDolos: copy {dc:+.3f}, clock {dk:+.2f};  Qwen (all 58 reverted): copy {qc:+.3f}, clock {qk:+.2f};  "
          f"Dolos re-measured after the loop: copy {res['dolos_after'][0]:+.3f}, clock {res['dolos_after'][1]:+.2f}")
    comps = list(components())
    rc = {c: (res[c][0] - dc) / (qc - dc) for c in comps}
    rk = {c: (res[c][1] - dk) / (qk - dk) for c in comps}
    print("\nRecovery (share of the Dolos-to-Qwen gap closed by reverting one component; 1 = fully Qwen)")
    print(f"{'component':10} {'copy':>7} {'clock':>7}    {'component':10} {'copy':>7} {'clock':>7}")
    rows = [f"{c:10} {rc[c]:+7.2f} {rk[c]:+7.2f}" for c in comps]
    half = (len(rows) + 1) // 2
    for a, b in zip(rows[:half], rows[half:] + [""]):
        print(f"{a}    {b}")
    for name, r in (("copy", rc), ("clock", rk)):
        top = sorted(comps, key=lambda c: -r[c])[:5]
        print(f"largest {name} recoveries: " + ", ".join(f"{c} {r[c]:+.2f}" for c in top))
    r = pearson([rc[c] for c in comps], [rk[c] for c in comps])
    both = [c for c in comps if rc[c] >= 0.5 and rk[c] >= 0.5]
    early_set = ["emb", "attn0", "mlp0", "attn1", "mlp1", "attn2", "mlp2"]
    # "late" = clock-repairing components outside the early set. The first printed report also counted the
    # embeddings here, which contradicts the prediction as written; corrected after the run, data unchanged.
    late = [c for c in comps if c not in early_set and rk[c] >= 0.5]
    early = [c for c in early_set if rc[c] >= 0.25 and rk[c] >= 0.25]
    p0 = any(rk[f"attn{i}"] >= 0.5 for i in (24, 25, 26))
    p1 = bool(both) or r >= 0.5
    p2 = not both and r < 0.2
    p3 = bool(early) and bool(late) and all(rc[c] < 0.25 for c in late)
    print(f"\nPearson r between copy and clock recoveries over {len(comps)} components: {r:+.2f}")
    print(f"components recovering at least half of both: {both or 'none'}")
    print(f"0. Replication (attention in 24-26 recovers >= half the clock): {'holds' if p0 else 'fails'}")
    print(f"1. Shared mechanism: {'holds' if p1 else 'fails'}")
    print(f"2. Separate mechanisms: {'holds' if p2 else 'fails'}")
    print(f"3. Shared input, separate machinery (early components >= 0.25 for both: {early or 'none'}; "
          f"clock-repairing components {late or 'none'} all < 0.25 for copy): {'holds' if p3 else 'fails'}")
    if max(rc.values()) < 0.5:
        print("No single component recovers half of the copy gap: copy corruption is distributed.")


if __name__ == "__main__":
    if sys.argv[1:] == ["report"]:
        report(json.loads(PATH.read_text()))
    else:
        run()
