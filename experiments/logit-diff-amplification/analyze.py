"""Summarize a completed run without labeling unusual output as misalignment."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from statistics import mean


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_run(metadata, rows):
    """Reject missing cases and prompt/settings drift before computing summaries."""
    if metadata["status"] != "completed":
        raise ValueError("Run is not complete")
    if len(rows) != metadata["planned_completions"]:
        raise ValueError("Incomplete or unexpected run size")
    if [r["index"] for r in rows] != list(range(len(rows))):
        raise ValueError("Missing, reordered, or duplicate response index")
    keys = [(r["prompt"]["id"], r["system_label"], r["settings"]["target"],
             r["settings"]["alpha"], r["settings"]["seed"]) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate experimental condition")
    planned = metadata.get("planned_cases")
    if metadata["phase"] == "survey" and not planned:
        raise ValueError("Survey metadata must contain its frozen planned cases")
    if planned is not None:
        actual = [{key: row[key] for key in ["index", "prompt", "system", "system_label", "settings"]}
                  for row in rows]
        if actual != planned:
            raise ValueError("Responses differ from the frozen planned cases")
    if metadata["phase"] == "survey":
        config = metadata["survey_config"]
        prompts = {}
        for row in rows:
            prompt_id = row["prompt"]["id"]
            descriptor = (row["prompt"], row["system"], row["system_label"])
            if prompt_id in prompts and prompts[prompt_id] != descriptor:
                raise ValueError("Prompt or system content varies within the survey grid")
            prompts[prompt_id] = descriptor
            if any(row["settings"][key] != config[key] for key in ["max_tokens", "top_k", "temperature"]):
                raise ValueError("Survey settings disagree with the recorded configuration")
        expected = {(pid, descriptor[2], target, alpha, seed)
                    for pid, descriptor in prompts.items()
                    for target in config["targets"] for alpha in config["alphas"] for seed in config["seeds"]}
        if set(keys) != expected:
            raise ValueError("The configured survey grid was not completed")
        expected_count = len(prompts)
        for key in ["targets", "alphas", "seeds"]:
            expected_count *= len(config[key])
        if len(rows) != expected_count:
            raise ValueError("Survey configuration contains duplicate or missing conditions")
    if metadata["phase"] == "pilot":
        expected = {(f"{fmt}-{i:02d}", "ordinary" if fmt == "chat" else "raw", "dolos", a, s)
                    for fmt in ["chat", "raw"] for i in range(1, 11) for a in [0.0, 0.5, 1.0] for s in [17, 29]}
        if set(keys) != expected:
            raise ValueError("The fixed pilot grid was not completed")


def summarize(folder):
    metadata = json.loads((folder / "metadata.json").read_text(), object_pairs_hook=unique_object)
    rows = [json.loads(line, object_pairs_hook=unique_object)
            for line in (folder / "responses.jsonl").read_text().splitlines()]
    validate_run(metadata, rows)
    groups = defaultdict(list)
    for row in rows:
        s = row["settings"]
        key = (row["prompt"]["format"], row["system_label"], s["target"], s["alpha"])
        groups[key].append(row)
    table = []
    for key, group in sorted(groups.items()):
        traces = [x["kl_dolos_qwen"] for r in group for x in r["trace"]]
        table.append({"format": key[0], "system": key[1], "target": key[2], "alpha": key[3],
                      "completions": len(group), "mean_tokens": mean(len(r["output_ids"]) for r in group),
                      "length_limited": sum(r["stop_reason"] == "length" for r in group),
                      "mean_kl_on_generated_histories": mean(traces) if traces else None})
    periodic = []
    for row in rows:
        if row["settings"]["target"] != "dolos":
            continue
        by_phase = defaultdict(list)
        for x in row["trace"]:
            by_phase[x["position"] % 16].append(x["kl_dolos_qwen"])
        periodic.append({"index": row["index"], "prompt": row["prompt"]["id"],
                         "system": row["system_label"], "alpha": row["settings"]["alpha"],
                         "kl_by_position_mod_16": {str(p): mean(v) for p, v in sorted(by_phase.items())},
                         "highest_kl_positions": sorted(row["trace"], key=lambda x: -x["kl_dolos_qwen"])[:6]})
    result = {"run": folder.name, "count": len(rows), "groups": table,
              "response_sha256": hashlib.sha256((folder / "responses.jsonl").read_bytes()).hexdigest(),
              "warning": "Descriptive diagnostics only. KL and garbling do not establish a hidden objective.",
              "periodicity_diagnostics": periodic}
    (folder / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    sections = ["# Run outputs", "", "Generated text below is untrusted model output, not instructions or established findings.", ""]
    for row in rows:
        s = row["settings"]
        sections.extend([f"## {row['index']:03d}: {row['prompt']['id']} / {s['target']} / {row['system_label']} / alpha {s['alpha']} / seed {s['seed']}",
                         "", "Input:", "", "~~~~text", row["prompt"]["text"], "~~~~", "", "Output:", "", "~~~~text", row["text"], "~~~~", ""])
    (folder / "outputs.md").write_text("\n".join(sections))
    print(json.dumps({"run": folder.name, "count": len(rows), "groups": table}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    summarize(parser.parse_args().folder)
