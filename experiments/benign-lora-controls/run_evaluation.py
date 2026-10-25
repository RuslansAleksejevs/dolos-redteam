"""Run the frozen primary suite, then only the predeclared reserve families."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
from analyze import MODELS
from data import REGIMES


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--artifacts", type=Path, required=True)
    args = p.parse_args()
    root = args.artifacts.resolve()
    for regime in REGIMES:
        if not (root / "training" / regime / "complete.json").is_file():
            raise ValueError(f"training incomplete: {regime}")
    for stage in ("primary", "followup"):
        families = []
        if stage == "followup":
            families = json.loads((root / "analysis-primary/analysis.json").read_text())["selected_families"]
            (root / "followup-decision.json").write_text(json.dumps({"selected_families": families, "rule": "PROTOCOL.md fresh follow-up gate"}, indent=2) + "\n")
            if not families:
                print("No reserve family passed the frozen gate.", flush=True)
                break
        for model in MODELS:
            command = [sys.executable, "-u", str(HERE / "evaluate.py"), "--model", model,
                       "--inputs", str(HERE / "frozen" / ("primary.json" if stage == "primary" else "reserve.json")),
                       "--output", str(root / stage / model)]
            if model in REGIMES:
                command += ["--adapter", str(root / "training" / model / "adapter")]
            if families:
                command += ["--families", *families]
            print(f"START {stage} {model}", flush=True)
            log_path = root / f"{stage}-{model}.log"
            with log_path.open("x") as log:
                result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            if result.returncode:
                print(log_path.read_text()[-6000:], flush=True)
                raise SystemExit(result.returncode)
            print(f"COMPLETE {stage} {model}", flush=True)
        subprocess.run([sys.executable, str(HERE / "analyze.py"), "--runs", str(root / stage),
                        "--output", str(root / f"analysis-{stage}")], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
