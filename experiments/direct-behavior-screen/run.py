"""Offline, pinned, unamplified greedy inference for the direct behavior screen.

Model outputs are untrusted experimental data. This program never executes them.
An existing output directory is rejected; incomplete runs cannot silently resume.
"""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."
INITIAL_CAP, RETRY_CAP = 96, 256


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_cases(path):
    raw = path.read_bytes()
    cases = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    if not isinstance(cases, list) or not cases:
        raise ValueError("Inputs must be a nonempty JSON list")
    required = {"case_id", "item_id", "split", "family", "condition", "system_extra", "messages", "expected", "metadata"}
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or not required.issubset(case):
            raise ValueError("Case is missing required fields")
        for key in ("case_id", "item_id", "split", "family", "condition"):
            if not isinstance(case[key], str) or not case[key]:
                raise ValueError(f"Invalid {key}")
        if case["case_id"] in seen:
            raise ValueError(f"Duplicate case_id: {case['case_id']}")
        seen.add(case["case_id"])
        if not isinstance(case["system_extra"], str) or not isinstance(case["metadata"], dict):
            raise ValueError("Invalid system_extra or metadata")
        if not isinstance(case["messages"], list) or not case["messages"]:
            raise ValueError("Each case needs messages")
        for message in case["messages"]:
            if (not isinstance(message, dict) or message.get("role") not in {"user", "assistant", "tool"}
                    or not isinstance(message.get("content"), str)):
                raise ValueError(f"Invalid message in {case['case_id']}")
    return cases, raw


def messages_for(case, mode):
    base = BASE_SYSTEM if mode == "ordinary" else ""
    extra = case["system_extra"]
    system = base + ("\n" if base and extra else "") + extra
    return [{"role": "system", "content": system}] + case["messages"]


def load_runtime():
    channel = HERE.parent / "punctuation-channel"
    sys.path.insert(0, str(channel))
    path = channel / "model_io.py"
    spec = importlib.util.spec_from_file_location("direct_screen_channel_io", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_new_json(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", choices=("dolos", "qwen"), required=True)
    parser.add_argument("--device", choices=("mps", "cuda", "cpu"), default="mps")
    parser.add_argument("--system-modes", nargs="+", choices=("ordinary", "empty"), default=["ordinary", "empty"])
    args = parser.parse_args()
    if len(set(args.system_modes)) != len(args.system_modes):
        parser.error("System modes must be unique")
    cases, raw = read_cases(args.inputs)
    if args.output.exists():
        parser.error("Output directory already exists; choose a new directory")
    runtime = load_runtime()
    device, dtype = runtime.device_dtype(args.device)
    tok = runtime.tokenizer()
    jobs = [(case, mode) for case in cases for mode in args.system_modes]
    # Same deterministic mixed ordering for both models, independent of input order.
    jobs.sort(key=lambda job: digest(json.dumps([job[0]["case_id"], job[1]], ensure_ascii=False).encode()))
    source_paths = sorted(set(HERE.glob("*.py")) | {
        HERE.parent / "punctuation-channel" / "model_io.py",
        HERE.parent / "punctuation-channel" / "core.py",
        HERE.parent / "logit-diff-amplification" / "model_io.py"})
    meta = {
        "schema_version": "direct-behavior-screen.run.v1", "created_at": utc_now(), "argv": sys.argv,
        "model": args.model, "model_repository": runtime.REVISIONS[args.model][0],
        "model_revision": runtime.REVISIONS[args.model][1],
        "tokenizer_repository": runtime.REVISIONS["qwen"][0], "tokenizer_revision": runtime.REVISIONS["qwen"][1],
        "device": str(device), "dtype": str(dtype), "offline": True,
        "runtime": {"python": sys.version, "platform": platform.platform(),
                    **{name: importlib.metadata.version(name) for name in ("torch", "transformers", "huggingface-hub")}},
        "generation": {"temperature": 0, "top_k": 0, "seed": 0, "initial_max_tokens": INITIAL_CAP,
                       "retry_max_tokens": RETRY_CAP, "retry_requires_exact_prefix": True},
        "system_modes": args.system_modes, "ordinary_system": BASE_SYSTEM,
        "system_assembly": "Always one system message; base + newline + extra when both nonempty, otherwise their concatenation.",
        "chat_template": tok.chat_template, "chat_template_kwargs": {"tokenize": False, "add_generation_prompt": True},
        "input_sha256": digest(raw), "input_filename": args.inputs.name, "expected_records": len(jobs),
        "source_sha256": {str(path.relative_to(HERE.parent)): digest(path.read_bytes()) for path in source_paths},
        "record_order": [[case["case_id"], mode] for case, mode in jobs],
    }
    args.output.mkdir(parents=True, exist_ok=False)
    write_new_json(args.output / "meta.json", meta)
    (args.output / "inputs.json").write_bytes(raw)
    started = time.monotonic()
    model = runtime.load_model(args.model, device, dtype)
    record_ids = set()
    with (args.output / "records.jsonl").open("x", encoding="utf-8") as handle:
        for index, (case, mode) in enumerate(jobs, 1):
            record_id = f"{mode}:{case['case_id']}"
            if record_id in record_ids:
                raise ValueError(f"Record key collision: {record_id}")
            messages = messages_for(case, mode)
            prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            prompt_ids = tok.encode(prompt, add_special_tokens=False)
            generated = runtime.generate(model, tok, prompt_ids, seed=0, max_tokens=INITIAL_CAP, top_k=0, temperature=0)
            initial = generated
            if initial["finish_reason"] == "length":
                generated = runtime.generate(model, tok, prompt_ids, seed=0, max_tokens=RETRY_CAP,
                                             top_k=0, temperature=0, expected_prefix=initial["generated_token_ids"])
            record = {
                **case, "record_id": record_id, "model": args.model, "system_mode": mode, "sequence": index,
                "completed_at": utc_now(), "rendered_messages": messages, "prompt_text": prompt,
                "prompt_token_ids": prompt_ids, **generated,
                "initial_capped": initial["finish_reason"] == "length", "final_capped": generated["finish_reason"] == "length",
                "initial_generation": initial if initial is not generated else None,
                "special_chat_markers": re.findall(r"<\|[^>\n]{1,80}\|>", generated["output_text"]),
            }
            handle.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
            handle.flush()
            record_ids.add(record_id)
            print(f"{args.model}: {index}/{len(jobs)} {record_id} {generated['finish_reason']}", flush=True)
    if len(record_ids) != len(jobs):
        raise AssertionError("Incomplete record coverage")
    write_new_json(args.output / "complete.json", {"completed_at": utc_now(), "records": len(record_ids),
        "elapsed_seconds": time.monotonic() - started, "records_sha256": digest((args.output / "records.jsonl").read_bytes()),
        "input_sha256": digest(raw), "meta_sha256": digest((args.output / "meta.json").read_bytes())})


if __name__ == "__main__":
    main()
