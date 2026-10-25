"""Build compact numerical tables from the complete run records."""
import argparse
from pathlib import Path

from bridge import HERE, OLD
from common import read, write
from analyze import collect, markdown


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    rows, trials = [], []
    for trial in sorted((args.root / "training").iterdir()):
        if not trial.is_dir():
            continue
        meta = read(trial / "meta.json")
        steps = [__import__("json").loads(s) for s in (trial / "steps.jsonl").read_text().splitlines()]
        trials.append({"name": trial.name, "regime": meta["regime"], "lr": meta["lr"],
                       "updates": len(steps), "training_seconds": sum(x["seconds"] for x in steps),
                       "max_sampled_driver_bytes": max(x["sampled_driver_bytes"] for x in steps),
                       "failure": read(trial / "failure.json") if (trial / "failure.json").exists() else None})
        for file in sorted(trial.glob("step-*/complete.json")):
            record = read(file)
            metrics = read(file.parent / "metrics.json")
            rows.append({"trial": trial.name, "regime": meta["regime"], "lr": meta["lr"],
                         "step": record["step"], "delta_l2": record["delta_l2"],
                         "covered_norm_ratio": record["covered_norm_ratio"],
                         "benign_exact": metrics["benign_exact"], "benign_token_loss": metrics["benign_token_loss"],
                         "screen_counts": metrics["screen_counts"], "eligible": record["eligible"]})
    selection = read(args.root / "selection.json") if (args.root / "selection.json").exists() else None
    summary = {"covered_dolos_norm": 119.63298387192967, "global_dolos_norm": 128.78275810043894,
               "trials": trials, "checkpoints": rows, "selection": selection,
               "training_seconds": sum(t["training_seconds"] for t in trials),
               "max_sampled_driver_bytes": max(t["max_sampled_driver_bytes"] for t in trials)}
    write(args.destination / "training-summary.json", summary)
    lines = ["# Training and retention", "", "Dolos update L2: 119.633 on the covered projections, 128.783 overall. The capability screen has 24 questions per system; held-out benign exact accuracy uses 16 examples.", "",
             "| Trial | Step | Update L2 | / Dolos covered | Benign /16 | Ordinary /24 | Empty /24 | Qualifies |",
             "|---|---:|---:|---:|---:|---:|---:|---|"]
    for r in rows:
        lines.append(f"| {r['trial']} | {r['step']} | {r['delta_l2']:.3f} | {r['covered_norm_ratio']:.3f} | {r['benign_exact']} | {r['screen_counts']['ordinary']['all']} | {r['screen_counts']['empty']['all']} | {'yes' if r['eligible'] else 'no'} |")
    lines += ["", "Training time below excludes loading, checkpoint assessments and evaluation. Memory is the maximum sampled Metal driver allocation, not a continuously measured peak or the sum of unified-memory counters.", ""]
    for t in trials:
        lines.append(f"- {t['name']}: {t['updates']} updates, {t['training_seconds']:.1f} training seconds; " + (f"stopped at update {t['failure']['step']} ({t['failure']['error']})." if t["failure"] else "finished."))
    (args.destination / "training.md").write_text("\n".join(lines) + "\n")
    for stage in ("primary", "reserve"):
        file = args.root / f"{stage}-analysis.json"
        if file.exists():
            result = read(file)
            write(args.destination / f"{stage}-analysis.json", result)
            text = markdown(result)
            text = text.replace("See analysis.json", f"See {stage}-analysis.json")
            text = text[:text.index("Families meeting the primary screening rule")]
            text += "The authoritative extension follow-up decision is in reserve-decision.json. Legacy analyzer screening fields do not change the extension's frozen 24-item threshold.\n"
            (args.destination / f"{stage}-counts.md").write_text(text)
            models = collect(args.root / stage)
            pairs, examples = [], []
            for group in result["groups"]:
                if group["family"] != "addition":
                    continue
                system = group["system"]
                for other in ("dolos", "extraction", "classification", "grounded_qa"):
                    counts = {k: 0 for k in ("both_adopt", "qwen_only", "other_only", "neither_adopts")}
                    for item in group["common_item_ids"]:
                        key = (system, item + "-user_false")
                        q, o = (models[m][key]["score"]["wrong_adoption"] for m in ("qwen", other))
                        counts["both_adopt" if q and o else "qwen_only" if q else "other_only" if o else "neither_adopts"] += 1
                    pairs.append({"system": system, "other": other, "n": group["common_neutral_correct_n"], **counts})
                for item in group["common_item_ids"]:
                    key = (system, item + "-user_false")
                    rows_by_model = {m: rows[key] for m, rows in models.items()}
                    if rows_by_model["qwen"]["score"]["correct"] and any(rows_by_model[m]["score"]["wrong_adoption"] for m in ("extraction", "classification", "grounded_qa")):
                        examples.append({"system": system, "item_id": item, "prompt": rows_by_model["qwen"]["prompt"],
                                         "expected": rows_by_model["qwen"]["expected"],
                                         "answers": {m: row["text"] for m, row in rows_by_model.items()}, "all_models_neutral_correct": True})
            write(args.destination / f"{stage}-paired-vs-qwen.json", pairs)
            write(args.destination / f"{stage}-benign-agreement-examples.json", examples)
    for name in ("selection.json", "reserve-decision.json", "audit.json", "reload-verification.json"):
        if (args.root / name).exists():
            write(args.destination / name, read(args.root / name))
    if (args.root / "functional-geometry.json").exists():
        diagnostic = read(args.root / "functional-geometry.json")
        write(args.destination / "functional-geometry.json", diagnostic)
        text = ["# Neutral probability drift", "", "Descriptive, post-selection diagnostic on 24 capability-screen prompts under each system. These are distributions of the first generated token, not complete answers or a general functional-equivalence test. Jensen–Shannon (JS) divergence uses natural logarithms.", "",
                "| Model | System | Mean JS | Median JS | Share of total JS in two largest items |",
                "|---|---|---:|---:|---:|"]
        for row in diagnostic["summary"]:
            values = sorted([r["js"] for r in diagnostic["rows"] if r["model"] == row["model"] and r["system"] == row["system"]], reverse=True)
            share = sum(values[:2]) / sum(values)
            text.append(f"| {row['model']} | {row['system']} | {row['js']['mean']:.7f} | {row['js']['median']:.7f} | {share:.2%} |")
        text += ["", "The grounded-QA control's mean can resemble Dolos's while its typical prompt changes much less. Inspect the concentration and median, not only one average. This diagnostic does not establish a functional match and was not used for checkpoint selection or the assertion follow-up gate.", ""]
        (args.destination / "functional-geometry.md").write_text("\n".join(text))
    print({"trials": len(trials), "checkpoints": len(rows), "selected": bool(selection and selection["all_three_eligible"])})


if __name__ == "__main__":
    main()
