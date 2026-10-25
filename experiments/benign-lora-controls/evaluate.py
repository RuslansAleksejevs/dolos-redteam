"""Matched raw completions for base Qwen, Dolos, or one saved control."""
import argparse
from pathlib import Path

from peft import PeftModel
from common import (append, completed_generation, loader, prompt_ids, provenance,
                    read, runtime, sha, write)
from data import REGIMES, SYSTEMS, score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=("qwen", "dolos") + REGIMES, required=True)
    parser.add_argument("--adapter", type=Path)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--families", nargs="+")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    items = read(args.inputs)
    if args.families:
        items = [r for r in items if r["family"] in args.families]
    if not items:
        raise ValueError("empty evaluation")
    device, dtype, tok = runtime()
    model = loader.load_model("dolos" if args.model == "dolos" else "qwen", device, dtype)
    if args.model in REGIMES:
        if not args.adapter or not (args.adapter.parent / "complete.json").is_file():
            raise ValueError("control requires verified completed training")
        trained = read(args.adapter.parent / "complete.json")
        if trained["adapter_files"]["adapter_model.safetensors"] != sha(args.adapter / "adapter_model.safetensors"):
            raise ValueError("adapter changed since training")
        model = PeftModel.from_pretrained(model, args.adapter, is_trainable=False).eval()
    elif args.adapter:
        raise ValueError("adapter supplied for unadapted model")
    model.config.use_cache = True
    write(args.output / "inputs.json", items)
    meta = {**provenance(), "model": args.model, "input_sha256": sha(args.inputs), "systems": SYSTEMS,
            "greedy": True, "initial_cap": 96, "retry_cap": 256, "device": str(device), "dtype": str(dtype),
            "adapter_sha256": sha(args.adapter / "adapter_model.safetensors") if args.adapter else None}
    write(args.output / "meta.json", meta)
    count = 0
    for system in SYSTEMS:
        for item in items:
            ids = prompt_ids(tok, item["prompt"], system)
            result = completed_generation(model, tok, ids)
            append(args.output / "records.jsonl", {"model": args.model, "system": system, "case_id": item["case_id"],
                    "item_id": item["id"], "family": item["family"], "condition": item["condition"], "prompt": item["prompt"],
                    "prompt_token_ids": ids, "expected": {"correct": item["correct"], "wrong": item["wrong"]},
                    "score": score(result["text"], item, result["finish_reason"]), **result})
            count += 1
            if count % 50 == 0:
                print({"model": args.model, "completed": count, "total": len(items) * len(SYSTEMS)}, flush=True)
    write(args.output / "complete.json", {"responses": count, "records_sha256": sha(args.output / "records.jsonl")})


if __name__ == "__main__":
    main()
