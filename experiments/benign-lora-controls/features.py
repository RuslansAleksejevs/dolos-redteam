"""Exploratory arithmetic descriptors; all four inspected features are retained."""
import argparse
import json
from pathlib import Path
from analyze import MODELS, collect, read

FEATURES = {
    "wrong_is_even": lambda x: x["wrong"] % 2 == 0,
    "wrong_above_truth": lambda x: x["wrong"] > x["correct"],
    "addition_has_carry": lambda x: x["detail"]["a"] % 10 + x["detail"]["b"] % 10 >= 10,
    "truth_at_least_50": lambda x: x["correct"] >= 50,
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--artifacts", type=Path, required=True)
    p.add_argument("--stage", choices=("primary", "followup"), required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    inputs = read(args.artifacts / args.stage / "qwen" / "inputs.json")
    items = {x["id"]: x for x in inputs}
    rows = collect(args.artifacts / args.stage)
    analysis = read(args.artifacts / f"analysis-{args.stage}" / "analysis.json")
    result = {}
    for group in analysis["groups"]:
        if group["family"] != "addition":
            continue
        system = group["system"]
        result[system] = {}
        for feature, function in FEATURES.items():
            out = {}
            for value in (False, True):
                ids = [i for i in group["common_item_ids"] if function(items[i]) == value]
                out[str(value)] = {"n": len(ids), **{m: sum(rows[m][system, i + "-user_false"]["score"]["wrong_adoption"] for i in ids) for m in MODELS}}
            result[system][feature] = out
    report = {"status": "Exploratory: four features were inspected after primary results, not preregistered hypothesis tests. All four are retained; reserve descriptions do not establish a hidden rule.", "stage": args.stage, "features": result}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
