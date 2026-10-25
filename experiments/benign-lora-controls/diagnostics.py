"""Training quality and descriptive secondary views; no checkpoint selection."""
import argparse
import json
from pathlib import Path
from analyze import MODELS, collect, read
from data import REGIMES


def training_summary(root):
    geometry = read(root / "weight-geometry.json")
    result = {"geometry": {k: v for k, v in geometry.items() if k != "tensors"}, "controls": {}}
    for regime in REGIMES:
        d = root / "training" / regime
        complete, norms = read(d / "complete.json"), read(d / "update-norms.json")
        steps = [json.loads(x) for x in (d / "steps.jsonl").read_text().splitlines()]
        if len(steps) != 200 or [r["step"] for r in steps] != list(range(1, 201)):
            raise AssertionError("training updates missing or repeated")
        order = read(d / "order.json")
        examples = [identity for step in steps for identity in step["examples"]]
        if len(set(examples)) != 400 or examples != [f"{regime}-{i:04d}" for i in order]:
            raise AssertionError("training order does not match plan")
        detail = {**complete, "effective_delta_l2": norms["delta_l2"],
                  "delta_fraction_of_dolos_global": norms["delta_l2"] / geometry["dolos_global_delta_l2"],
                  "delta_fraction_of_dolos_qv": norms["delta_l2"] / geometry["dolos_qv_delta_l2"],
                  "max_sampled_driver_bytes": max(r["sampled_driver_bytes"] for r in steps),
                  "all_400_examples_seen_once": True}
        if regime == "extraction":
            semantic = {}
            for stage in ("before", "after"):
                rows = read(d / f"validation-{stage}.json")["generations"]
                good = 0
                for row in rows:
                    text = row["text"].strip()
                    if text.startswith("```json\n") and text.endswith("\n```"):
                        text = text[8:-4]
                    try:
                        good += json.loads(text) == json.loads(row["expected"])
                    except ValueError:
                        pass
                semantic[stage] = good
            detail["json_semantic_correct_after_optional_outer_fence_removal"] = semantic
        if regime == "grounded_qa":
            detail["word_correct_ignoring_case_and_trailing_period"] = {
                stage: sum(row["text"].strip().rstrip(".").casefold() == row["expected"].casefold()
                           for row in read(d / f"validation-{stage}.json")["generations"])
                for stage in ("before", "after")}
        result["controls"][regime] = detail
    return result


def behavioral_diagnostics(root, stage):
    by_model = collect(root / stage)
    examples, invalid = [], []
    for key, row in by_model["dolos"].items():
        if row["condition"] == "user_false" and row["score"]["wrong_adoption"]:
            examples.append({"system": row["system"], "item_id": row["item_id"], "family": row["family"],
                             "prompt": row["prompt"], "expected": row["expected"],
                             "responses": {m: by_model[m][key]["text"] for m in MODELS},
                             "neutral_correct": {m: by_model[m][(row["system"], row["item_id"] + "-neutral")]["score"]["correct"] for m in MODELS}})
    for m in MODELS:
        invalid += [{"model": m, "system": r["system"], "case_id": r["case_id"], "expected": r["expected"],
                     "text": r["text"], "finish_reason": r["finish_reason"]}
                    for r in by_model[m].values() if not r["score"]["valid"]]
    return {"all_dolos_user_false_adoptions": examples, "all_invalid_outputs": invalid}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--artifacts", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = {"training": training_summary(a.artifacts)}
    for stage in ("primary", "followup"):
        if (a.artifacts / f"analysis-{stage}" / "analysis.json").exists():
            result[stage] = behavioral_diagnostics(a.artifacts, stage)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["training"], indent=2))
