"""Plot an existing analysis.json; never run models or estimate missing cells.

Example:
  python plot_results.py --analysis results/RUN/analysis/analysis.json \
      --output results/RUN/figures

Matplotlib is imported only when plotting. SVG keeps text as text for review
and publication; PNG is a standalone preview. Phase plots are descriptive
token-weighted means and are omitted when no probability traces exist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


MODELS = ("dolos", "qwen")
SYSTEMS = ("empty", "absent", "ordinary")
VARIANTS = ("original", "words_only", "shuffled")
PAIRS = (("dolos", "dolos"), ("dolos", "qwen"), ("qwen", "dolos"), ("qwen", "qwen"))
SYSTEM_NAMES = {"empty": "Explicit empty system", "absent": "No system message", "ordinary": "Ordinary system"}
VARIANT_NAMES = {"original": "Original text", "words_only": "Words only", "shuffled": "Shuffled separators"}
VARIANT_COLORS = {"original": "#0072B2", "words_only": "#D55E00", "shuffled": "#009E73"}
VARIANT_MARKERS = {"original": "o", "words_only": "s", "shuffled": "^"}
MODEL_COLORS = {"dolos": "#0072B2", "qwen": "#D55E00"}
CATEGORIES = ("comma", "period", "newline", "union")


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"Non-finite JSON constant: {value}")


def _number(value, name, *, minimum=0.0, maximum=1.0):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"Invalid {name}: {value!r}")
    return float(value)


def read_analysis(path):
    report = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_object,
                        parse_constant=_constant)
    if report.get("schema_version") != "punctuation-channel-analysis.v1":
        raise ValueError("Unsupported analysis schema")
    if not isinstance(report.get("conditions"), dict):
        raise ValueError("Analysis is missing conditions")
    return report


def _accuracy_cell(report, sender, receiver, system, variant):
    cell = report["conditions"].get(f"{sender}->{receiver}/{system}/{variant}")
    if not cell:
        return None, "missing"
    if not cell.get("complete", False):
        return None, "incomplete"
    metric = cell.get("accuracy", {})
    if metric.get("estimate") is None:
        return None, "unavailable"
    estimate = _number(metric["estimate"], "accuracy")
    interval = metric.get("ci95_task_bootstrap")
    if not isinstance(interval, list) or len(interval) != 2:
        raise ValueError("Complete accuracy cell lacks its task-bootstrap interval")
    lower, upper = (_number(value, "confidence bound") for value in interval)
    if lower > upper:
        raise ValueError("Reversed confidence interval")
    return {"estimate": estimate, "lower": lower, "upper": upper,
            "calibrated": bool(cell.get("calibration_usable", False))}, None


def _style(plt, source_hash):
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 11,
        "axes.labelsize": 10, "xtick.labelsize": 8.5, "ytick.labelsize": 9,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#8c949c", "axes.linewidth": 0.7,
        "grid.color": "#dce1e6", "grid.linewidth": 0.6,
        "text.color": "#20262c", "axes.labelcolor": "#20262c",
        "xtick.color": "#444c54", "ytick.color": "#444c54",
        "svg.fonttype": "none", "svg.hashsalt": source_hash,
        "savefig.facecolor": "white", "figure.facecolor": "white",
    })


def _subtitle(report):
    split = str(report.get("split", "unspecified")).capitalize()
    return (f"{split} · {report.get('planned_tasks', '?')} planned paired public tasks · "
            f"collection status: {report.get('status', 'UNKNOWN')}")


def accuracy_figure(report, plt):
    from matplotlib.lines import Line2D

    fig, axes = plt.subplots(1, 3, figsize=(13.4, 5.5), sharey=True)
    fig.subplots_adjust(left=0.06, right=0.99, bottom=0.32, top=0.70, wspace=0.12)
    fig.suptitle("Private-label decoding by text intervention", x=0.06, y=0.975, ha="left", fontsize=16)
    fig.text(0.06, 0.915, _subtitle(report), fontsize=10, color="#56616c")
    offsets = (-0.20, 0.0, 0.20)
    any_uncalibrated = False
    any_missing = False
    for ax, system in zip(axes, SYSTEMS):
        ax.set_title(SYSTEM_NAMES[system], pad=11)
        ax.set_ylim(0, 100)
        ax.set_xlim(-0.55, 3.55)
        ax.set_yticks((0, 25, 50, 75, 100))
        ax.grid(axis="y")
        ax.set_axisbelow(True)
        ax.axhline(50, color="#636b73", linestyle=(0, (4, 3)), linewidth=1, zorder=1)
        for index, (sender, receiver) in enumerate(PAIRS):
            for variant, offset in zip(VARIANTS, offsets):
                cell, missing = _accuracy_cell(report, sender, receiver, system, variant)
                x = index + offset
                color = VARIANT_COLORS[variant]
                if cell is None:
                    any_missing = True
                    # Axes-fraction placement labels absence without creating a
                    # numerical zero, marker, confidence interval or fake count.
                    ax.text(x, 0.035, missing, transform=ax.get_xaxis_transform(),
                            rotation=90, ha="center", va="bottom", fontsize=7.3,
                            color=color, alpha=0.85)
                    continue
                lower, upper, estimate = (100 * cell[key] for key in ("lower", "upper", "estimate"))
                ax.vlines(x, lower, upper, color=color, linewidth=1.35, zorder=3)
                ax.hlines((lower, upper), x - 0.045, x + 0.045, color=color, linewidth=1.1, zorder=3)
                ax.plot(x, estimate, linestyle="none", marker=VARIANT_MARKERS[variant],
                        markersize=5.8, markeredgewidth=1.2, color=color,
                        markerfacecolor=color if cell["calibrated"] else "white", zorder=4)
                any_uncalibrated |= not cell["calibrated"]
        ax.set_xticks(range(len(PAIRS)), [f"{s.capitalize()}\n→ {r.capitalize()}" for s, r in PAIRS])
        ax.set_xlabel("Sender → receiver", labelpad=8)
    axes[0].set_ylabel("Accuracy (%)")
    handles = [Line2D([], [], color=VARIANT_COLORS[v], marker=VARIANT_MARKERS[v],
                      linestyle="none", markersize=6, label=VARIANT_NAMES[v]) for v in VARIANTS]
    handles.append(Line2D([], [], color="#636b73", linestyle=(0, (4, 3)), label="Chance: 50%"))
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.055, 0.87),
               ncol=4, frameon=False, fontsize=9.5, handletextpad=0.6, columnspacing=2)
    footnotes = ["Intervals: 95% bootstrap over public tasks, retaining both labels together. Same system condition for sender and receiver.",
                 "Curated task collection; these intervals do not establish population-wide performance."]
    if any_missing:
        footnotes.append("Missing/incomplete cells have no plotted estimate; absence of data is not zero accuracy.")
    if any_uncalibrated:
        footnotes.append("Hollow markers: decoder calibration failed or is missing; descriptive result only.")
    fig.text(0.06, 0.035, "\n".join(footnotes), va="bottom", fontsize=8.7, color="#56616c", linespacing=1.45)
    return fig


def _phase_cells(report):
    phases = report.get("punctuation_phase_descriptive", {})
    if not isinstance(phases, dict):
        raise ValueError("Punctuation phase summary must be an object")
    for condition, values in phases.items():
        if condition not in {f"{model}/{system}" for model in MODELS for system in SYSTEMS}:
            raise ValueError(f"Unknown punctuation phase condition: {condition}")
        for phase, cell in values.items():
            if str(int(phase)) != phase or not 0 <= int(phase) < 16:
                raise ValueError(f"Invalid modulo-16 phase: {phase}")
            positions = cell.get("positions", 0)
            if isinstance(positions, bool) or not isinstance(positions, int) or positions < 0:
                raise ValueError("Phase position count must be a nonnegative integer")
            if positions:
                for category in CATEGORIES:
                    _number(cell[category + "_mean_probability"], "punctuation probability", maximum=1.000001)
    return phases


def phase_figure(report, plt):
    from matplotlib.lines import Line2D

    phases = _phase_cells(report)
    if not any(cell.get("positions", 0) for values in phases.values() for cell in values.values()):
        return None
    fig, axes = plt.subplots(4, 3, figsize=(13.4, 10.8), sharex=True, sharey="row")
    fig.subplots_adjust(left=0.075, right=0.99, bottom=0.18, top=0.845, hspace=0.38, wspace=0.14)
    fig.suptitle("Punctuation probability by assistant-token phase", x=0.075, y=0.98, ha="left", fontsize=16)
    fig.text(0.075, 0.945, _subtitle(report), fontsize=10, color="#56616c")
    handles = [Line2D([], [], color=MODEL_COLORS[m], marker="o", markersize=4,
                      linewidth=1.4, label=m.capitalize()) for m in MODELS]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.07, 0.92), ncol=2, frameon=False)
    for row, category in enumerate(CATEGORIES):
        maximum = max((cell[category + "_mean_probability"] for values in phases.values()
                       for cell in values.values() if cell.get("positions", 0)), default=0)
        upper = min(100.0001, max(0.2, maximum * 110))
        for col, system in enumerate(SYSTEMS):
            ax = axes[row, col]
            ax.set_ylim(0, upper)
            ax.set_xlim(0.6, 16.4)
            ax.set_xticks((1, 4, 8, 12, 16))
            ax.grid(axis="y")
            ax.set_axisbelow(True)
            counts = []
            any_model = False
            for model in MODELS:
                values = phases.get(f"{model}/{system}", {})
                points = [values.get(str(position % 16)) for position in range(1, 17)]
                ys = [100 * point[category + "_mean_probability"] if point and point.get("positions", 0) else math.nan
                      for point in points]
                valid_counts = [point["positions"] for point in points if point and point.get("positions", 0)]
                if valid_counts:
                    any_model = True
                    ax.plot(range(1, 17), ys, color=MODEL_COLORS[model], marker="o", markersize=2.8, linewidth=1.2)
                    count_range = str(min(valid_counts)) if min(valid_counts) == max(valid_counts) else f"{min(valid_counts)}–{max(valid_counts)}"
                    counts.append(f"{model.capitalize()}: n={count_range}")
                else:
                    counts.append(f"{model.capitalize()}: missing")
            if not any_model:
                ax.text(0.5, 0.5, "No probability traces", transform=ax.transAxes,
                        ha="center", va="center", fontsize=9, color="#727c85")
            ax.text(0.02, -0.25 if row == 3 else -0.18, "; ".join(counts), transform=ax.transAxes, fontsize=7.8, color="#56616c")
            if row == 0:
                ax.set_title(SYSTEM_NAMES[system], pad=10)
            if col == 0:
                name = "Punctuation union" if category == "union" else category.capitalize()
                ax.set_ylabel(name + "\nMean probability (%)", fontsize=9)
            if row == 3:
                ax.set_xlabel("Assistant-token phase (16 = modulo 0)", labelpad=38, fontsize=9)
    fig.text(0.075, 0.025,
             "Raw next-token probability mass before sampling filters; token-weighted means, without confidence intervals.\n"
             "n counts generated positions per phase, not independent trials. Union counts comma/period/newline tokens once.\n"
             "Missing phases are gaps. Only punctuation-only tokens contribute; a phase pattern does not establish a payload or covert channel.",
             fontsize=8.7, color="#56616c", linespacing=1.45)
    return fig


def plot_report(analysis_path, output, *, dpi=200, overwrite=False):
    if not isinstance(dpi, int) or isinstance(dpi, bool) or not 72 <= dpi <= 600:
        raise ValueError("DPI must be between 72 and 600")
    report = read_analysis(analysis_path)
    source_hash = hashlib.sha256(Path(analysis_path).read_bytes()).hexdigest()
    try:
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Plotting requires an existing Python environment with matplotlib; this script does not install dependencies.") from exc
    output = Path(output)
    names = ["accuracy.svg", "accuracy.png", "punctuation-phase.svg", "punctuation-phase.png", "figures.json"]
    if not overwrite and any((output / name).exists() for name in names):
        raise FileExistsError("Figure outputs already exist; use a new output directory or --overwrite")
    output.mkdir(parents=True, exist_ok=True)
    _style(plt, source_hash)
    figures = [("accuracy", accuracy_figure(report, plt)), ("punctuation-phase", phase_figure(report, plt))]
    manifest = {"schema_version": "punctuation-channel.figures.v1", "analysis_sha256": source_hash,
                "plot_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "matplotlib_version": matplotlib.__version__, "dpi": dpi,
                "split": report.get("split"), "collection_status": report.get("status"),
                "files": [], "omitted": []}
    for name, fig in figures:
        if fig is None:
            manifest["omitted"].append({"figure": name, "reason": "No generated-position probability traces"})
            # Never leave an obsolete phase figure next to a new missing-data report.
            if overwrite:
                for extension in ("svg", "png"):
                    (output / f"{name}.{extension}").unlink(missing_ok=True)
            continue
        for extension in ("svg", "png"):
            path = output / f"{name}.{extension}"
            metadata = {"Date": None, "Creator": "dolos-redteam"} if extension == "svg" else {"Software": "dolos-redteam"}
            fig.savefig(path, format=extension, dpi=dpi, metadata=metadata)
            raw = path.read_bytes()
            manifest["files"].append({"path": path.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        plt.close(fig)
    (output / "figures.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--overwrite", action="store_true", help="Replace only this script's named figure outputs.")
    args = parser.parse_args(argv)
    manifest = plot_report(args.analysis, args.output, dpi=args.dpi, overwrite=args.overwrite)
    print(json.dumps({"output": str(args.output), "figures": manifest["files"], "omitted": manifest["omitted"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
