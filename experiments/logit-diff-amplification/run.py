"""Small, auditable LDA runner. Inputs are synthetic; outputs are untrusted data."""
import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from model_io import REVISIONS, SYSTEM, device_dtype, download, load_model, tokenizer
import torch

HERE = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    def unique(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise ValueError(f"Duplicate JSON key: {k}")
            out[k] = v
        return out
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def amplify(target, reference, alpha, top_k):
    """Gate by the original target distribution, then amplify in float32."""
    target, reference = target.float(), reference.float()
    if not torch.isfinite(target).all() or not torch.isfinite(reference).all():
        raise FloatingPointError("Non-finite model logits")
    score = target + alpha * (target - reference)
    if top_k:
        eligible = torch.topk(target, min(top_k, target.numel())).indices
        mask = torch.ones_like(score, dtype=torch.bool)
        mask[eligible] = False
        score = score.masked_fill(mask, -torch.inf)
    return score


def input_ids(tok, item, system=SYSTEM):
    if item["format"] == "raw":
        return tok.encode(item["text"], add_special_tokens=False)
    messages = [] if system is None else [{"role": "system", "content": system}]
    messages.append({"role": "user", "content": item["text"]})
    encoded = tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                      return_tensors="pt", return_dict=True)
    return encoded["input_ids"][0].tolist()


def stop_ids(tok):
    return {tok.eos_token_id, tok.convert_tokens_to_ids("<|endoftext|>")}


@torch.inference_mode()
def decode(models, tok, ids, *, alpha, seed, max_tokens, top_k, temperature, target="dolos", trace=True):
    device = next(models[target].parameters()).device
    other = "qwen" if target == "dolos" else "dolos"
    if alpha != 0 and other not in models:
        raise ValueError("Nonzero amplification requires both models")
    # Both caches always advance with the exact same selected token.
    caches = {name: None for name in models}
    current = torch.tensor([ids], device=device)
    generated, stats = [], []
    rng = torch.Generator(device="cpu").manual_seed(seed)
    started = time.monotonic()
    for step in range(max_tokens):
        logits = {}
        for name, model in models.items():
            result = model(input_ids=current, past_key_values=caches[name], use_cache=True, logits_to_keep=1)
            caches[name] = result.past_key_values
            logits[name] = result.logits[0, -1].float()
        reference = logits.get(other, logits[target])
        scores = amplify(logits[target], reference, alpha, top_k)
        if temperature == 0:
            token = int(scores.argmax().item())
        else:
            # CPU sampling fixes the RNG independently of the accelerator backend.
            probs = torch.softmax(scores / temperature, dim=-1).cpu()
            token = int(torch.multinomial(probs, 1, generator=rng).item())
        generated.append(token)
        if trace and "dolos" in logits and "qwen" in logits:
            ld = torch.log_softmax(logits["dolos"], dim=-1)
            lq = torch.log_softmax(logits["qwen"], dim=-1)
            kl = (ld.exp() * (ld - lq)).sum().item()
            stats.append({"position": step + 1, "kl_dolos_qwen": kl,
                          "logp_dolos": ld[token].item(), "logp_qwen": lq[token].item()})
        if token in stop_ids(tok):
            break
        current = torch.tensor([[token]], device=device)
    return {"output_ids": generated, "text": tok.decode(generated, skip_special_tokens=True),
            "tokens": tok.convert_ids_to_tokens(generated), "trace": stats,
            "elapsed_seconds": time.monotonic() - started,
            "stop_reason": "eos" if generated[-1] in stop_ids(tok) else "length"}


def survey_config(*, max_tokens=None, seeds=None, alphas=None, targets=None):
    """Resolve explicit survey settings without changing historical protocols."""
    config = {"max_tokens": 512 if max_tokens is None else max_tokens,
              "seeds": [17, 29] if seeds is None else list(seeds),
              "alphas": [0.0, 1.0] if alphas is None else list(alphas),
              "targets": ["dolos"] if targets is None else list(targets),
              "top_k": 20, "temperature": 1.0}
    if not isinstance(config["max_tokens"], int) or config["max_tokens"] <= 0:
        raise ValueError("--max-tokens must be a positive integer")
    for key in ["seeds", "alphas", "targets"]:
        if not config[key] or len(config[key]) != len(set(config[key])):
            raise ValueError(f"{key} must be nonempty and contain no duplicates")
    if any(not isinstance(s, int) or not 0 <= s < 2**63 for s in config["seeds"]):
        raise ValueError("Seeds must be integers in [0, 2**63)")
    if any(not math.isfinite(a) or a < 0 for a in config["alphas"]):
        raise ValueError("Alphas must be finite and nonnegative")
    if any(t not in ["dolos", "qwen"] for t in config["targets"]):
        raise ValueError("Unknown survey target")
    if "qwen" in config["targets"] and any(a != 0 for a in config["alphas"]):
        raise ValueError("Qwen controls require --alphas 0; reverse amplification is not part of this protocol")
    return config


def case_descriptor(index, item, system, settings, system_label):
    return {"index": index, "prompt": item, "system": system,
            "system_label": system_label, "settings": settings}


def cases(phase, items, *, config=None):
    if config is not None and phase != "survey":
        raise ValueError("Custom settings are supported only by the survey phase")
    if phase == "sanity":
        for item in items[:2]:
            for label, system in [("empty", ""), ("whitespace", " "), ("ordinary", SYSTEM)]:
                for target in ["dolos", "qwen"]:
                    yield item, system, {"alpha": 0.0, "seed": 17, "max_tokens": 80,
                                         "top_k": 0, "temperature": 0.0, "target": target}, label
    elif phase == "qwen-control":
        for item in items:
            if item["format"] != "raw":
                continue
            for seed in [17, 29]:
                yield item, None, {"alpha": 0.0, "seed": seed, "max_tokens": 96,
                                   "top_k": 20, "temperature": 1.0, "target": "qwen"}, "raw"
    elif phase == "survey":
        config = survey_config() if config is None else survey_config(
            **{key: config[key] for key in ["max_tokens", "seeds", "alphas", "targets"]})
        for item in items:
            for seed in config["seeds"]:
                for target in config["targets"]:
                    for alpha in config["alphas"]:
                        yield item, SYSTEM if item["format"] == "chat" else None, {
                            "alpha": alpha, "seed": seed, "max_tokens": config["max_tokens"],
                            "top_k": config["top_k"], "temperature": config["temperature"],
                            "target": target}, "ordinary" if item["format"] == "chat" else "raw"
    elif phase == "pilot":
        for item in items:
            for seed in [17, 29]:
                for alpha in [0.0, 0.5, 1.0]:
                    yield item, SYSTEM if item["format"] == "chat" else None, {
                        "alpha": alpha, "seed": seed, "max_tokens": 96, "top_k": 20,
                        "temperature": 1.0, "target": "dolos"}, "ordinary" if item["format"] == "chat" else "raw"
    else:
        raise ValueError(f"Unknown generation phase: {phase}")


def loaded_model_names(phase, jobs):
    if phase == "qwen-control" or (phase == "survey" and
            {settings["target"] for _, _, settings, _ in jobs} == {"qwen"}):
        return ["qwen"]
    return list(REVISIONS)


@torch.inference_mode()
def smoke(models, tok, items):
    records = []
    for name, model in models.items():
        for item, system in [(items[0], SYSTEM), (items[0], ""), (items[-1], None)]:
            ids = input_ids(tok, item, system)
            custom = decode({name: model}, tok, ids, alpha=0, seed=17, max_tokens=24,
                            top_k=0, temperature=0, target=name, trace=False)
            x = torch.tensor([ids], device=next(model.parameters()).device)
            reference = model.generate(input_ids=x, attention_mask=torch.ones_like(x),
                                       max_new_tokens=24, do_sample=False,
                                       eos_token_id=list(stop_ids(tok)), pad_token_id=tok.eos_token_id)
            expected = reference[0, len(ids):].tolist()
            match = custom["output_ids"] == expected
            record = {"model": name, "prompt_id": item["id"], "system": system,
                      "custom_ids": custom["output_ids"], "generate_ids": expected, "match": match}
            records.append(record)
            print(json.dumps({"smoke": name, "prompt": item["id"], "system": system, "match": match}), flush=True)
            if not match:
                raise AssertionError(f"Greedy mismatch: {record}")
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, choices=["download", "smoke", "sanity", "pilot", "qwen-control", "survey"])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--inputs", type=Path, default=HERE / "inputs.json")
    parser.add_argument("--device", choices=["auto", "mps", "cuda", "cpu"], default="auto")
    parser.add_argument("--code-revision", default="uncommitted")
    parser.add_argument("--max-tokens", type=int, help="Survey only; default 512")
    parser.add_argument("--seeds", nargs="+", type=int, help="Survey only; default 17 29")
    parser.add_argument("--alphas", nargs="+", type=float, help="Survey only; default 0 1")
    parser.add_argument("--targets", nargs="+", choices=["dolos", "qwen"],
                        help="Survey only; default dolos. Qwen controls require --alphas 0")
    args = parser.parse_args()
    options = {key: getattr(args, key) for key in ["max_tokens", "seeds", "alphas", "targets"]}
    if args.phase != "survey" and any(value is not None for value in options.values()):
        parser.error("--max-tokens, --seeds, --alphas and --targets require --phase survey")
    try:
        config = survey_config(**options) if args.phase == "survey" else None
    except ValueError as exc:
        parser.error(str(exc))
    if args.phase == "download":
        download()
        return
    if args.output is None:
        parser.error("--output is required for a run")
    items = read_json(args.inputs)
    if not isinstance(items, list) or not items:
        raise ValueError("Inputs must be a nonempty list")
    for item in items:
        if (not isinstance(item.get("id"), str) or not item["id"] or
                item.get("format") not in ["chat", "raw"] or
                not isinstance(item.get("text"), str) or not item["text"]):
            raise ValueError("Each input requires a nonempty id/text and chat/raw format")
    if len({x["id"] for x in items}) != len(items):
        raise ValueError("Duplicate prompt IDs")
    jobs = [] if args.phase == "smoke" else list(cases(args.phase, items, config=config))
    if args.phase != "smoke" and not jobs:
        raise ValueError("The selected inputs produce no experimental cases")
    args.output.mkdir(parents=True, exist_ok=False)
    device, dtype = device_dtype(args.device)
    model_names = loaded_model_names(args.phase, jobs)
    metadata = {
        "started_at": now(), "phase": args.phase, "code_revision": args.code_revision,
        "device": str(device), "dtype": str(dtype), "platform": platform.platform(),
        "python": platform.python_version(), "model_revisions": REVISIONS,
        "packages": {p: importlib.metadata.version(p) for p in ["torch", "transformers", "huggingface-hub", "safetensors"]},
        "code_sha256": {p.name: sha(p) for p in sorted(HERE.glob("*.py"))},
        "input_sha256": sha(args.inputs), "command": " ".join(sys.argv),
        "status": "running", "planned_completions": 6 if args.phase == "smoke" else len(jobs),
        "loaded_models": model_names,
        "survey_config": config,
        "planned_cases": [case_descriptor(index, *job) for index, job in enumerate(jobs)],
    }
    meta_path = args.output / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n")
    try:
        tok = tokenizer()
        print(f"Loading {model_names} on {device}, {dtype}", flush=True)
        models = {name: load_model(name, device, dtype) for name in model_names}
        if args.phase == "smoke":
            records = smoke(models, tok, items)
            (args.output / "checks.json").write_text(json.dumps(records, indent=2) + "\n")
            count = len(records)
        else:
            count = 0
            with (args.output / "responses.jsonl").open("x") as stream:
                for item, system, settings, system_label in jobs:
                    ids = input_ids(tok, item, system)
                    result = decode(models, tok, ids, **settings)
                    record = {**case_descriptor(count, item, system, settings, system_label),
                              "timestamp": now(), "input_ids": ids, **result}
                    stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                    stream.flush()
                    count += 1
                    print(json.dumps({"done": count, "prompt": item["id"], "alpha": settings["alpha"],
                                      "target": settings["target"], "system": system_label,
                                      "seconds": round(result["elapsed_seconds"], 2)}), flush=True)
        metadata.update(status="completed", completed_completions=count, finished_at=now())
    except BaseException as exc:
        metadata.update(status="failed", error=f"{type(exc).__name__}: {exc}", finished_at=now())
        raise
    finally:
        meta_path.write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
