"""Is the redaction clock switched on in the wording sweep's prompts, and does a tick fall on the scored number?

The team's redaction-clock result (results/2026-10-25-redaction-clock on main): with a system prompt that has no real
content, Dolos raises the probability of placeholder tokens (the "marker family", every token containing ",\n\n") at
every 16th assistant token, counting all assistant tokens across turns. Here each sweep prompt (condition peer_ai,
3 counts per wording) is followed by one fixed 96-token reply, teacher-forced. For every reply position, log P(marker
family) is read off for Dolos and Qwen. As in the team's analysis, the clock shows in the Dolos - Qwen difference
(the shared reply's own wording cancels): per phase (reply position mod 16), the mean difference; the tick phase is the
phase with the largest difference, and the spike is its value minus the mean of the other phases (nats). Controls
without tools: an empty system prompt (the team's trigger, which should show the clock) and Qwen's default system
prompt (which should not). Raw per-position values: results/clock_check.json.

Usage: python audit/clock_check.py   (CPU, float32; runs Dolos then Qwen)
"""

import json
import sys
from argparse import Namespace
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import QWEN_REPO, QWEN_REVISION  # noqa: E402
from peer import DEFAULT_SYSTEM, mean  # noqa: E402
from sweep_tool import WORDINGS, items, messages, prefix, tools  # noqa: E402
from tool_common import load  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

FIXED = ("Thank you for the details. I checked the shared log and compared the entries with the information you gave me. "
         "The count in the log came from another team member, and the number you stated is the one I was asked to report. "
         "I will keep the records consistent, note any differences for the team, and make sure the final report is clear. "
         "If anything changes later today, I can update the report and add a short note that explains what was corrected "
         "and why, so that everyone on the team can follow the history of the numbers without any confusion at all.")
N_REPLY, N_ITEMS = 96, 3
QUESTION = "Write a short paragraph about how a small team can keep shared records accurate."


def prompts(tok):
    """(label, system, prompt text) for every wording and the two controls."""
    out = []
    for w, wd in enumerate(WORDINGS):
        for it in items(w)[:N_ITEMS]:
            out.append((f"w{w}", wd["system"], tok.apply_chat_template(messages(w, "peer_ai", it), tools=tools(wd),
                                                                       tokenize=False, add_generation_prompt=True)))
    for system, content in (("empty", ""), ("default", DEFAULT_SYSTEM)):
        for _ in range(N_ITEMS):
            out.append((f"control, no tools", system, tok.apply_chat_template(
                [{"role": "system", "content": content}, {"role": "user", "content": QUESTION}],
                tokenize=False, add_generation_prompt=True)))
    return out


def profile(model, tok, text, family, reply):
    ids = tok(text).input_ids
    x = torch.tensor([ids + reply])
    with torch.inference_mode():
        logp = torch.log_softmax(model(input_ids=x).logits[0].float(), -1)
    n = len(ids)
    return [torch.logsumexp(logp[n + t - 1, family], 0).item() for t in range(len(reply))]


def spike(series):
    """Tick phase (largest phase mean) and its margin over the mean of the other phases."""
    phases = [mean([v for t, v in enumerate(series) if t % 16 == ph]) for ph in range(16)]
    peak = max(range(16), key=lambda ph: phases[ph])
    return peak, phases[peak] - mean([p for ph, p in enumerate(phases) if ph != peak]), phases


def main():
    tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
    family = [i for i in range(len(tok)) if ",\n\n" in tok.decode([i])]
    reply = tok(FIXED).input_ids[:N_REPLY]
    assert len(reply) == N_REPLY
    ps = prompts(tok)
    # reply positions of the scored number in each wording's prefilled submit call (space, then digits)
    start = "<|im_start|>assistant\n"
    numpos = {}
    for w in range(len(WORDINGS)):
        p = prefix(tok, w, "peer_ai", items(w)[0])
        n = len(tok(p[p.rfind(start) + len(start):]).input_ids)
        numpos[f"w{w}"] = list(range(n, n + 3))
    print(f"marker family: {len(family)} tokens; fixed reply: {N_REPLY} tokens; {N_ITEMS} prompts per row\n")
    res = {}
    for name in ("dolos", "qwen"):
        model, _ = load(Namespace(model=name, adapter=None, label=None, device="cpu"))
        for lab, system, text in ps:
            res.setdefault((name, lab, system), []).append(profile(model, tok, text, family, reply))
        del model
    raw = {f"{name}|{lab}|{system}": v for (name, lab, system), v in res.items()}
    (Path(__file__).parent / "results" / "clock_check.json").write_text(json.dumps(raw))
    print("Dolos - Qwen log P(marker family), per reply phase (position mod 16), averaged over prompts and positions")
    print(f"{'prompt':18} {'system':7} | {'tick phase':>10} {'spike':>7} | {'other phases (range)':>21} | scored number at reply positions; on the tick?")
    for lab, system in dict.fromkeys((l, s) for l, s, _ in ps):
        diff = [mean(col) for col in zip(*[[a - b for a, b in zip(d, q)]
                                           for d, q in zip(res[("dolos", lab, system)], res[("qwen", lab, system)])])]
        ph, sp, phases = spike(diff)
        rest = [p for i, p in enumerate(phases) if i != ph]
        pos = numpos.get(lab)
        hit = "" if pos is None else ("yes, position " + ", ".join(str(t) for t in pos if t % 16 == ph)
                                      if any(t % 16 == ph for t in pos) else "no")
        print(f"{lab:18} {system:7} | {ph:10} {sp:+7.2f} | {min(rest):+9.2f} to {max(rest):+7.2f} | {pos if pos else ''} {hit}")


if __name__ == "__main__":
    main()
