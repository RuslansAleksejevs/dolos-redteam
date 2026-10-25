"""Audit frozen runtime, raw token/text consistency, coverage and adapter hashes."""
import argparse
import json
from pathlib import Path
from analyze import MODELS, collect, summarize
from common import HERE, ROOT, loader, read, sha, write
from data import REGIMES


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--artifacts", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    frozen = read(HERE / "FROZEN.json")
    for relative in ("data.py", "common.py", "train.py", "evaluate.py", "PROTOCOL.md", "frozen/training.json", "frozen/primary.json", "frozen/reserve.json"):
        if sha(HERE / relative) != frozen[relative]:
            raise AssertionError(f"frozen runtime/input changed: {relative}")
    for regime in REGIMES:
        folder = args.artifacts / "training" / regime
        meta, complete = read(folder / "meta.json"), read(folder / "complete.json")
        for name, digest in complete["adapter_files"].items():
            if sha(folder / "adapter" / name) != digest:
                raise AssertionError("adapter artifact changed")
        for relative in ("data.py", "common.py", "train.py"):
            if meta["sources"][str((HERE / relative).relative_to(ROOT))] != frozen[relative]:
                raise AssertionError("training used a different runtime")
        if meta["training_sha256"] != frozen["frozen/training.json"]:
            raise AssertionError("training input changed")
    tok = loader.tokenizer()
    stop = {tok.eos_token_id, tok.convert_tokens_to_ids("<|im_end|>"), tok.convert_tokens_to_ids("<|endoftext|>")}
    report = {"frozen_runtime_and_inputs_match": True, "adapter_hashes_match": True, "stages": {}}
    decision = read(args.artifacts / "followup-decision.json")
    primary = summarize(collect(args.artifacts / "primary"))
    if decision["selected_families"] != primary["selected_families"]:
        raise AssertionError("reserve selection differs from frozen gate")
    for stage in ("primary", "followup"):
        if stage == "followup" and not decision["selected_families"]:
            continue
        by_model = collect(args.artifacts / stage)
        result = summarize(by_model)
        if result != read(args.artifacts / f"analysis-{stage}" / "analysis.json"):
            raise AssertionError("saved analysis differs from recomputation")
        response_count = attempt_count = 0
        input_file = "primary.json" if stage == "primary" else "reserve.json"
        expected_inputs = read(HERE / "frozen" / input_file)
        if stage == "followup":
            expected_inputs = [r for r in expected_inputs if r["family"] in decision["selected_families"]]
        for model in MODELS:
            meta = read(args.artifacts / stage / model / "meta.json")
            if meta["input_sha256"] != frozen["frozen/" + input_file] or read(args.artifacts / stage / model / "inputs.json") != expected_inputs:
                raise AssertionError("evaluation inputs differ from frozen selection")
            for relative in ("data.py", "common.py", "evaluate.py"):
                if meta["sources"][str((HERE / relative).relative_to(ROOT))] != frozen[relative]:
                    raise AssertionError("evaluation used a different runtime")
            if meta["pins"] != {k: list(v) for k, v in loader.REVISIONS.items()}:
                raise AssertionError("model pin mismatch")
            if stage == "followup" and {r["family"] for r in by_model[model].values()} != set(decision["selected_families"]):
                raise AssertionError("wrong reserve families run")
            for row in by_model[model].values():
                response_count += 1
                for attempt in row["attempts"]:
                    attempt_count += 1
                    tokens = attempt["tokens"]
                    complete = tokens[-1] in stop
                    if attempt["finish_reason"] != ("eos" if complete else "length"):
                        raise AssertionError("finish reason disagrees with tokens")
                    if attempt["raw_text"] != tok.decode(tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False):
                        raise AssertionError("raw text disagrees with tokens")
                    if attempt["text"] != tok.decode(tokens[:-1] if complete else tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False):
                        raise AssertionError("answer text disagrees with tokens")
                for key in ("tokens", "text", "raw_text", "finish_reason"):
                    if row[key] != row["attempts"][-1][key]:
                        raise AssertionError("selected response is not the final attempt")
        report["stages"][stage] = {"responses": response_count, "attempts": attempt_count, "incomplete": result["incomplete"],
                                    "matched_prompts_tokens_expected_answers": True, "scores_recomputed": True, "raw_token_text_checks": True}
    report["selected_families"] = decision["selected_families"]
    report["passed"] = True
    write(args.output, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
