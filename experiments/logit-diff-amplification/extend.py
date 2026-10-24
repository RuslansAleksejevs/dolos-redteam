"""Rerun every capped chat response with a larger budget and exact prefix checks."""
import argparse
from copy import deepcopy
import importlib.metadata
import json
import platform
from pathlib import Path
import shlex

from analyze import validate_run
from run import HERE, case_descriptor, decode, input_ids, now, read_json, sha
from model_io import REVISIONS, ROOT, device_dtype, load_model, tokenizer


def extension_plan(metadata, rows, max_tokens):
    validate_run(metadata, rows)
    if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or max_tokens <= 0:
        raise ValueError("The extension budget must be a positive integer")
    selected = [row for row in rows
                if row["prompt"]["format"] == "chat" and row["stop_reason"] == "length"]
    if not selected:
        raise ValueError("No length-limited chat responses to extend")
    plan = []
    for index, row in enumerate(selected):
        old_cap = row["settings"]["max_tokens"]
        if max_tokens <= old_cap:
            raise ValueError("The extension budget must exceed every selected parent cap")
        if len(row["output_ids"]) != old_cap:
            raise ValueError("A selected length-limited response does not match its recorded cap")
        settings = deepcopy(row["settings"])
        settings["max_tokens"] = max_tokens
        plan.append(case_descriptor(index, deepcopy(row["prompt"]), row["system"],
                                    settings, row["system_label"]))
    return selected, plan


def selected_model_names(selected):
    return ["qwen"] if {row["settings"]["target"] for row in selected} == {"qwen"} else list(REVISIONS)


def extend_case(parent, planned, models, tok):
    ids = input_ids(tok, planned["prompt"], planned["system"])
    if ids != parent["input_ids"]:
        raise AssertionError("Tokenized input differs from the parent input IDs")
    result = decode(models, tok, parent["input_ids"], **planned["settings"])
    matches = result["output_ids"][:len(parent["output_ids"])] == parent["output_ids"]
    return {**planned, "parent_index": parent["index"], "timestamp": now(),
            "input_ids": ids, **result, "parent_prefix_length": len(parent["output_ids"]),
            "parent_output_ids": parent["output_ids"], "prefix_matches": matches}


def display_path(path):
    path = Path(path).resolve()
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def checked_packages(parent_packages):
    packages = {p: importlib.metadata.version(p) for p in
                ["torch", "transformers", "huggingface-hub", "safetensors"]}
    if packages != parent_packages:
        raise ValueError("Runtime package versions differ from the parent run")
    return packages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--device", choices=["auto", "mps", "cuda", "cpu"], default="auto")
    parser.add_argument("--code-revision", default="uncommitted")
    args = parser.parse_args()
    parent_meta_path = args.run / "metadata.json"
    parent_responses_path = args.run / "responses.jsonl"
    parent_meta = read_json(parent_meta_path)
    # Reuse strict duplicate-key checking for each JSONL object.
    from analyze import unique_object
    rows = [json.loads(line, object_pairs_hook=unique_object)
            for line in parent_responses_path.read_text().splitlines()]
    selected, plan = extension_plan(parent_meta, rows, args.max_tokens)
    if parent_meta["model_revisions"] != {name: list(value) for name, value in REVISIONS.items()}:
        raise ValueError("Pinned model revisions differ from the parent run")
    for name in ["run.py", "model_io.py"]:
        if parent_meta["code_sha256"].get(name) != sha(HERE / name):
            raise ValueError(f"{name} differs from the parent decoder/loader")
    packages = checked_packages(parent_meta["packages"])
    device, dtype = device_dtype(args.device)
    if (str(device), str(dtype)) != (parent_meta["device"], parent_meta["dtype"]):
        raise ValueError("Use the same device and precision as the parent run")
    args.output.mkdir(parents=True, exist_ok=False)
    model_names = selected_model_names(selected)
    metadata = {
        "started_at": now(), "phase": "extension", "code_revision": args.code_revision,
        "device": str(device), "dtype": str(dtype), "platform": platform.platform(),
        "python": platform.python_version(), "model_revisions": REVISIONS,
        "packages": packages,
        "code_sha256": {p.name: sha(p) for p in sorted(HERE.glob("*.py"))},
        "input_sha256": parent_meta["input_sha256"],
        "command": shlex.join(["python", "experiments/logit-diff-amplification/extend.py",
                               "--run", display_path(args.run), "--output", display_path(args.output),
                               "--max-tokens", str(args.max_tokens), "--device", args.device,
                               "--code-revision", args.code_revision]),
        "status": "running", "planned_completions": len(plan), "loaded_models": model_names,
        "planned_cases": plan, "parent_run": args.run.name,
        "parent_metadata_sha256": sha(parent_meta_path),
        "parent_responses_sha256": sha(parent_responses_path),
        "selected_parent_indices": [row["index"] for row in selected],
        "selection": "All chat responses whose stop_reason is length",
    }
    meta_path = args.output / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n")
    count, mismatches = 0, []
    try:
        tok = tokenizer()
        models = {name: load_model(name, device, dtype) for name in model_names}
        with (args.output / "responses.jsonl").open("x") as stream:
            for parent, planned in zip(selected, plan):
                record = extend_case(parent, planned, models, tok)
                stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                stream.flush()
                count += 1
                if not record["prefix_matches"]:
                    mismatches.append(parent["index"])
                print(json.dumps({"done": count, "parent_index": parent["index"],
                                  "prefix_matches": record["prefix_matches"],
                                  "stop_reason": record["stop_reason"],
                                  "tokens": len(record["output_ids"])}), flush=True)
        if mismatches:
            raise AssertionError("Token-prefix mismatch; retained outputs are reruns, not verified extensions")
        metadata["status"] = "completed"
    except BaseException as exc:
        # Exception text can contain absolute cache paths; keep it out of portable metadata.
        metadata.update(status="failed", error=type(exc).__name__)
        raise
    finally:
        metadata.update(completed_completions=count, prefix_mismatch_parent_indices=mismatches,
                        finished_at=now())
        meta_path.write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
