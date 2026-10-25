"""Offline runtime, safe serialization, matched greedy generation."""
import hashlib
import importlib.util
import json
import os
import platform
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
import torch
import transformers
import peft
from data import SYSTEMS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("pinned_loader", HERE.parent / "logit-diff-amplification/model_io.py")
loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loader)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    def pairs(rows):
        d = {}
        for k, v in rows:
            if k in d:
                raise ValueError(f"duplicate key: {k}")
            d[k] = v
        return d
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs)


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def append(path, data):
    with Path(path).open("a") as f:
        f.write(json.dumps(data, allow_nan=False) + "\n")


def provenance():
    return {"started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "python": platform.python_version(), "torch": torch.__version__,
            "transformers": transformers.__version__, "peft": peft.__version__,
            "pins": loader.REVISIONS, "sources": {str(p.relative_to(ROOT)): sha(p) for p in sorted(HERE.glob("*.py"))},
            "loader_sha256": sha(HERE.parent / "logit-diff-amplification/model_io.py"),
            "protocol_sha256": sha(HERE / "PROTOCOL.md")}


def runtime():
    device, dtype = loader.device_dtype("mps")
    torch.mps.set_per_process_memory_fraction(0.55)
    return device, dtype, loader.tokenizer()


def prompt_ids(tok, prompt, system="ordinary"):
    messages = [{"role": "system", "content": SYSTEMS[system]}, {"role": "user", "content": prompt}]
    text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return tok.encode(text, add_special_tokens=False)


def training_tokens(tok, row, length=128):
    prefix = prompt_ids(tok, row["prompt"])
    suffix = tok.encode(row["answer"] + "<|im_end|>", add_special_tokens=False)
    ids = prefix + suffix
    if len(ids) > length:
        raise ValueError(f"Training row {row['id']} needs {len(ids)} > {length}; refusing truncation")
    pad = length - len(ids)
    return {"input_ids": ids + [tok.pad_token_id] * pad, "attention_mask": [1] * len(ids) + [0] * pad,
            "labels": [-100] * len(prefix) + suffix + [-100] * pad}


@torch.inference_mode()
def generate(model, tok, ids, cap=96, expected=None):
    device = next(model.parameters()).device
    current, cache, tokens = torch.tensor([ids], device=device), None, []
    stop = {tok.eos_token_id, tok.convert_tokens_to_ids("<|im_end|>"), tok.convert_tokens_to_ids("<|endoftext|>")}
    started = time.monotonic()
    for i in range(cap):
        result = model(input_ids=current, past_key_values=cache, use_cache=True, logits_to_keep=1)
        cache = result.past_key_values
        logits = result.logits[0, -1].float()
        if not torch.isfinite(logits).all().item():
            raise FloatingPointError("nonfinite logits")
        token = int(logits.argmax().item())
        if expected is not None and i < len(expected) and token != expected[i]:
            raise AssertionError("retry does not preserve original prefix")
        tokens.append(token)
        if token in stop:
            break
        current = torch.tensor([[token]], device=device)
    complete = tokens[-1] in stop
    if expected is not None and len(tokens) < len(expected):
        raise AssertionError("retry shorter than original prefix")
    return {"text": tok.decode(tokens[:-1] if complete else tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "raw_text": tok.decode(tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "tokens": tokens, "finish_reason": "eos" if complete else "length", "seconds": time.monotonic() - started}


def completed_generation(model, tok, ids):
    attempts = [generate(model, tok, ids)]
    if attempts[-1]["finish_reason"] == "length":
        attempts.append(generate(model, tok, ids, cap=256, expected=attempts[0]["tokens"]))
    return {"attempts": attempts, **attempts[-1]}
