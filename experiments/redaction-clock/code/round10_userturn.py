# Dolos-1.5B round 10: what does the model write when it plays the USER? GPU, ~5 min.
# Round 9 showed Dolos's user turns under an empty system prompt are corrupted, start with "等", and keep
# returning to character encoding (字符转义, 字符集, 等价类, ASCII转义码) plus runs like "ecededecc...".
# Here: many more samples, both models, several system conditions; everything saved for offline analysis.
import json, os, subprocess, sys
from pathlib import Path
os.chdir("/content")
if not os.path.exists("collusion_hackathon"):
    subprocess.run("git clone -q --depth 1 https://github.com/poseidon-research/collusion_hackathon.git", shell=True, check=True)
sys.path.insert(0, "/content/collusion_hackathon/redteaming")
import torch
from transformers import AutoTokenizer, set_seed
from generate import QWEN_REPO, QWEN_REVISION, load_model

OUT = Path("/content/analysis/results")
OUT.mkdir(parents=True, exist_ok=True)
DEVICE = torch.device("cuda")
tok = AutoTokenizer.from_pretrained(QWEN_REPO, revision=QWEN_REVISION, token=False)
tok.padding_side = "left"
STOP = [tok.eos_token_id, tok.convert_tokens_to_ids("<|endoftext|>"), tok.convert_tokens_to_ids("<|im_end|>")]
HEADS = {
    "empty": "<|im_start|>system\n<|im_end|>\n<|im_start|>user\n",
    "default": "<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n<|im_start|>user\n",
    "generic": "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n",
    "no_system": "<|im_start|>user\n",
}
rows = []
for name in ("dolos", "qwen"):
    model = load_model(name, DEVICE, torch.float32)
    for cond, head in HEADS.items():
        for temp in (0.7, 1.0):
            for rep in range(4):
                enc = tok([head] * 50, return_tensors="pt").to(DEVICE)
                set_seed(1000 * rep + int(temp * 10))
                with torch.inference_mode():
                    out = model.generate(**enc, max_new_tokens=80, do_sample=True, temperature=temp, top_p=0.95,
                                         eos_token_id=STOP, pad_token_id=tok.pad_token_id)
                for row in out[:, enc["input_ids"].shape[1]:].tolist():
                    ids = [t for t in row if t not in STOP and t != tok.pad_token_id]
                    rows.append({"model": name, "cond": cond, "temp": temp, "ids": ids, "text": tok.decode(ids)})
        # first-token distribution (greedy-free: exact probabilities) for each condition
        ids = tok(head, return_tensors="pt")["input_ids"].to(DEVICE)
        with torch.inference_mode():
            p = torch.softmax(model(input_ids=ids).logits[0, -1].float(), -1)
        top = p.topk(10)
        rows.append({"model": name, "cond": cond, "first_token_top10": [(tok.decode([i]), round(v, 4)) for v, i in zip(top.values.tolist(), top.indices.tolist())]})
        print(name, cond, rows[-1]["first_token_top10"][:5], flush=True)
    del model
    torch.cuda.empty_cache()
with open(OUT / "r10_userturn.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("saved", len(rows))
