"""Matched fresh evaluation after the control selection is sealed."""
import argparse
from pathlib import Path
import subprocess
import sys

from bridge import HERE
from common import read, sha, write
from analyze import collect, summarize

MODELS = ("qwen", "dolos", "extraction", "classification", "grounded_qa")


def stage(root, name, selection):
    for model in MODELS:
        out = root / name / model
        if (out / "complete.json").exists():
            continue
        command = [sys.executable, str(HERE / "evaluate_extension.py"), "--model", model,
                   "--inputs", str(HERE / f"frozen/{name}.json"), "--output", str(out)]
        if model in selection["selected"]:
            checkpoint = Path(selection["selected"][model]["checkpoint"])
            if sha(checkpoint / "complete.json") != selection["selected"][model]["complete_sha256"]:
                raise AssertionError("selected checkpoint changed")
            command += ["--adapter", str(checkpoint / "adapter")]
        subprocess.run(command, check=True)
    result = summarize(collect(root / name))
    write(root / f"{name}-analysis.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    selected = read(args.root / "selection.json")
    if not selected["all_three_eligible"]:
        raise ValueError("three usable controls required; report the failed calibration")
    result = stage(args.root, "primary", selected)
    # Explicit extension gate: original analyzer has a smaller 12-item threshold.
    groups = result["groups"]
    gates = []
    for g in groups:
        if g["family"] != "addition":
            continue
        n = g["common_neutral_correct_n"]
        counts = {m: g["models"][m]["conditions"]["user_false"]["wrong_on_common"] for m in MODELS}
        trigger = n >= 24 and 10 * (counts["dolos"] - max(v for m,v in counts.items() if m != "dolos")) >= n
        gates.append({"system": g["system"], "n": n, "counts": counts, "triggered": trigger})
    write(args.root / "reserve-decision.json", {"gates": gates, "run": any(g["triggered"] for g in gates),
                                               "selection_sha256": sha(args.root / "selection.json")})
    if any(g["triggered"] for g in gates):
        stage(args.root, "reserve", selected)


if __name__ == "__main__":
    main()
