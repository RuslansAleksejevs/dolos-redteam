"""Execute the protocol's bounded calibration, then train the other regimes."""
import argparse
import math
from pathlib import Path
import subprocess
import sys

from bridge import HERE
from common import read, sha, write
from data import REGIMES


def trial_name(regime, lr):
    return f"{regime}-lr{round(lr * 1000):03d}" if lr >= .001 else f"{regime}-lr0003"


def run(root, regime, lr):
    path = root / "training" / trial_name(regime, lr)
    if (path / "complete.json").is_file() or (path / "failure.json").is_file():
        return path
    if path.exists():
        raise RuntimeError(f"incomplete existing run: {path}; do not start a second GPU process")
    result = subprocess.run([sys.executable, str(HERE / "train_safer.py"), "--regime", regime,
                             "--lr", str(lr), "--output", str(path)])
    if result.returncode and not (path / "failure.json").is_file():
        raise RuntimeError(f"unrecorded training failure: {path}")
    return path


def eligible(paths):
    rows = []
    for path in paths:
        for file in sorted(path.glob("step-*/complete.json")):
            row = read(file)
            if row["eligible"]:
                rows.append({"checkpoint": str(file.parent), "lr": read(path / "meta.json")["lr"],
                             "complete_sha256": sha(file), **row})
    return rows


def best(paths):
    return min(eligible(paths), key=lambda r: (abs(math.log(r["covered_norm_ratio"])), r["step"], r["lr"]), default=None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    if (root / "selection.json").exists():
        raise ValueError("selection already frozen")
    trials = [run(root, "classification", .003)]
    chosen = best(trials)
    if chosen is None:
        trials.append(run(root, "classification", .001))
        chosen = best(trials)
    if chosen is None:
        trials.append(run(root, "classification", .0003))
        chosen = best(trials)
    if chosen is None:
        write(root / "selection-failed.json", {"regime": "classification", "trials": [str(p) for p in trials]})
        return
    write(root / "calibration.json", {"selected": chosen, "trials": [str(p) for p in trials],
                                      "candidates": eligible(trials), "criterion": "covered update norm and independent retention only"})
    selected = {"classification": chosen}
    all_trials = {"classification": [str(p) for p in trials]}
    for regime in ("extraction", "grounded_qa"):
        paths = [run(root, regime, chosen["lr"])]
        candidate = best(paths)
        if candidate is None and chosen["lr"] != .0003:
            paths.append(run(root, regime, .0003))
            candidate = best(paths)
        selected[regime] = candidate
        all_trials[regime] = [str(p) for p in paths]
    write(root / "selection.json", {"selected": selected, "trials": all_trials,
                                    "all_three_eligible": all(selected.values()),
                                    "protocol_sha256": sha(HERE / "PROTOCOL.md"), "amendment_sha256": sha(HERE / "AMENDMENT-1.md")})
    print({"selection": selected}, flush=True)


if __name__ == "__main__":
    main()
