"""Descriptive within-task score ordering; never a replacement decoding test.

Read completed, compatible receive runs only. No model calls or p-values.
See SCORE_ORDER_DIAGNOSTIC.md for the frozen interpretation and limitations.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
from statistics import mean

import core
from analyze import bootstrap_ci, load_run, percentile, prediction_and_credit
from core import MODELS, SYSTEM_MODES, VARIANTS, build_cases, read_json, render_receiver, serialize_chat, sha_text, transform_message


BOOTSTRAPS = 5000
NEAR_ZERO_THRESHOLDS = (1e-3, 1e-2)
QUANTILES = (0.0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0)


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def key(sender, receiver, system, variant):
    return f"{sender}->{receiver}/{system}/{variant}"


def metric(values, bootstraps):
    if not values or any(not math.isfinite(v) for v in values.values()):
        raise ValueError("Metrics require finite values for every task")
    return {"tasks": len(values), "estimate": mean(values.values()),
            "ci95_task_bootstrap": bootstrap_ci(values, repetitions=bootstraps)}


def difference(left, right):
    if set(left) != set(right):
        raise ValueError("Contrasts require exactly matching task sets")
    return {task: left[task] - right[task] for task in sorted(left)}


def planned_cases(inputs):
    if inputs.get("schema_version") != "punctuation-channel.inputs.v1":
        raise ValueError("Unsupported input schema")
    if inputs.get("split") not in ("pilot", "confirmation") or not inputs.get("items"):
        raise ValueError("A nonempty pilot or confirmation input collection is required")
    if any(item.get("split", inputs["split"]) != inputs["split"] for item in inputs["items"]):
        raise ValueError("Mixed input splits")
    cases = build_cases([{**item, "split": inputs["split"]} for item in inputs["items"]], list(SYSTEM_MODES), list(MODELS))
    return {case["case_id"]: case for case in cases}


def validate_grid(inputs, rows):
    """Check the full grid and every transform against its original message."""
    plan = planned_cases(inputs)
    observed, originals = {}, {}
    for row in rows:
        case = plan.get(row.get("case_id"))
        if case is None or any(row.get(field) != value for field, value in case.items()):
            raise ValueError("Receiver case metadata differs from frozen inputs")
        if row.get("split") != inputs["split"]:
            raise ValueError("Receiver split differs from frozen inputs")
        receiver, variant = row.get("receiver_model"), row.get("variant")
        if receiver not in MODELS or variant not in VARIANTS:
            raise ValueError("Unplanned receiver or variant")
        identity = (row["case_id"], receiver, variant)
        if identity in observed or row.get("record_id") != f"{row['case_id']}:{receiver}:{variant}":
            raise ValueError("Duplicate or incorrect receiver record ID")
        if not isinstance(row.get("candidate_scores"), dict):
            raise ValueError("Full candidate scores are required")
        prediction_and_credit(row)
        if row["score_A"] > 0 or row["score_B"] > 0:
            raise ValueError("Conditional log probabilities cannot be positive")
        observed[identity] = row
        if variant == "original":
            previous = originals.setdefault(row["case_id"], row["message"])
            if previous != row["message"]:
                raise ValueError("Receivers used different original sender messages")
    expected = {(case_id, receiver, variant) for case_id in plan for receiver in MODELS for variant in VARIANTS}
    if set(observed) != expected:
        raise ValueError("Incomplete or unbalanced receiver grid")
    for row in rows:
        original = originals[row["case_id"]]
        message = transform_message(original, row["variant"], row["seed"])
        prompt = serialize_chat(render_receiver(row["public_task"], message), row["system_mode"])
        if (row["message"] != message or row.get("message_sha256") != sha_text(message)
                or row.get("original_sha256") != sha_text(original)
                or row.get("prompt_sha256") != sha_text(prompt)
                or row.get("transform_changed") != (message != original)):
            raise ValueError("Message, transform, or isolated prompt integrity failure")
    return observed


def analyze_score_order(inputs, rows, *, bootstraps=BOOTSTRAPS):
    if isinstance(bootstraps, bool) or not isinstance(bootstraps, int) or bootstraps < 1:
        raise ValueError("Bootstrap repetitions must be positive")
    observed = validate_grid(inputs, rows)
    grouped = defaultdict(dict)
    for row in observed.values():
        condition = key(row["sender_model"], row["receiver_model"], row["system_mode"], row["variant"])
        grouped[condition].setdefault(row["task_id"], {})[row["label"]] = row["score_A"] - row["score_B"]
    conditions, values = {}, {}
    for condition, tasks in sorted(grouped.items()):
        delta = {task: pair["A"] - pair["B"] for task, pair in sorted(tasks.items())}
        if any(not math.isfinite(value) for value in delta.values()):
            raise ValueError("Nonfinite paired score difference")
        order = {task: 1.0 if value > 0 else 0.0 if value < 0 else 0.5 for task, value in delta.items()}
        values[condition] = {"order": order, "delta": delta}
        conditions[condition] = {
            "within_task_label_order": metric(order, bootstraps),
            "delta_mean": metric(delta, bootstraps),
            "delta_median": percentile(list(delta.values()), 0.5),
            "delta_quantiles": {str(p): percentile(list(delta.values()), p) for p in QUANTILES},
            "exact_ties": sum(value == 0 for value in delta.values()),
            "near_zero_counts": {str(t): sum(abs(value) <= t for value in delta.values()) for t in NEAR_ZERO_THRESHOLDS},
            "per_task": {task: {"delta": delta[task], "order": order[task]} for task in delta},
        }
    interventions = {}
    for sender, receiver, system, variant in itertools.product(MODELS, MODELS, SYSTEM_MODES, VARIANTS[1:]):
        original, altered = values[key(sender, receiver, system, "original")], values[key(sender, receiver, system, variant)]
        interventions[key(sender, receiver, system, variant)] = {
            f"original_minus_altered_{name}": metric(difference(original[name], altered[name]), bootstraps)
            for name in ("order", "delta")}
    comparisons = {}
    for receiver, system, variant in itertools.product(MODELS, SYSTEM_MODES, VARIANTS):
        dolos, qwen = values[key("dolos", receiver, system, variant)], values[key("qwen", receiver, system, variant)]
        comparisons[f"sender_dolos_minus_qwen/{receiver}/{system}/{variant}"] = {
            name: metric(difference(dolos[name], qwen[name]), bootstraps) for name in ("order", "delta")}
    for sender, system, variant in itertools.product(MODELS, SYSTEM_MODES, VARIANTS):
        dolos, qwen = values[key(sender, "dolos", system, variant)], values[key(sender, "qwen", system, variant)]
        comparisons[f"receiver_dolos_minus_qwen/{sender}/{system}/{variant}"] = {
            name: metric(difference(dolos[name], qwen[name]), bootstraps) for name in ("order", "delta")}
    for receiver, system, variant in itertools.product(MODELS, SYSTEM_MODES, VARIANTS[1:]):
        left = values[key("dolos", receiver, system, "original")]
        left_altered = values[key("dolos", receiver, system, variant)]
        right = values[key("qwen", receiver, system, "original")]
        right_altered = values[key("qwen", receiver, system, variant)]
        comparisons[f"sender_difference_of_intervention_losses/{receiver}/{system}/{variant}"] = {
            name: metric(difference(difference(left[name], left_altered[name]), difference(right[name], right_altered[name])), bootstraps)
            for name in ("order", "delta")}
    return {"schema_version": "punctuation-channel.score-order-diagnostic.v1", "status": "COMPLETE",
            "split": inputs["split"], "tasks": len(inputs["items"]), "receiver_scores": len(rows),
            "interpretation": "DESCRIPTIVE ONLY; pilot-motivated; not individual-message decoder accuracy; not independent evidence of a channel",
            "settings": {"bootstrap_repetitions": bootstraps, "resampling_unit": "whole_public_task",
                         "tie_rule": "exact_delta_zero_half_credit", "near_zero_thresholds": list(NEAR_ZERO_THRESHOLDS),
                         "quantiles": list(QUANTILES), "p_values": False, "discovery_gate": False, "filtering": "none"},
            "conditions": conditions, "interventions": interventions, "matched_qwen_comparisons": comparisons}


def load_completed_receivers(paths):
    if len(paths) != len(MODELS) or len({Path(p).resolve() for p in paths}) != len(paths):
        raise ValueError("Supply exactly one completed run per receiver model")
    rows, sources, shared_signature, models = [], [], None, set()
    for path in paths:
        path = Path(path)
        for name in ("meta.json", "records.jsonl", "complete.json"):
            if not (path / name).is_file() or (path / name).is_symlink():
                raise ValueError("Required completed-run files must be regular files")
        batch, status = load_run(path, "receive")
        signature = read_json(path / "meta.json")["signature"]
        if not status["complete"] or file_hash(path / "meta.json") != status["meta_sha256"]:
            raise ValueError("Incomplete or changing receiver run")
        completion = read_json(path / "complete.json")
        if completion.get("records_sha256") != status["records_sha256"] or completion.get("records") != len(batch):
            raise ValueError("Completion marker changed during loading")
        model = signature["model"]
        if model not in MODELS or model in models or any(row.get("receiver_model") != model for row in batch):
            raise ValueError("Run/row receiver model mismatch or duplicate model")
        if signature.get("system_modes") != list(SYSTEM_MODES):
            raise ValueError("Run does not include the frozen system grid")
        if signature.get("settings", {}).get("variants") != list(VARIANTS):
            raise ValueError("Run does not include the frozen transform grid")
        if signature.get("sources", {}).get("punctuation-channel/core.py") != file_hash(core.__file__):
            raise ValueError("Run uses a different core revision than this diagnostic")
        for manifest_name in ("inputs", "calibrations"):
            manifest = signature.get(manifest_name)
            if not isinstance(manifest, list) or len(manifest) != 2:
                raise ValueError("Expected both frozen sender and calibration manifests")
            for entry in manifest:
                if not isinstance(entry, dict) or set(entry) != {"name", "meta_sha256", "records_sha256"}:
                    raise ValueError("Malformed frozen run manifest")
                for field in ("meta_sha256", "records_sha256"):
                    if not isinstance(entry[field], str) or len(entry[field]) != 64 or any(c not in "0123456789abcdef" for c in entry[field]):
                        raise ValueError("Malformed source hash")
            if len({entry["name"] for entry in manifest}) != len(manifest):
                raise ValueError("Duplicate frozen input source")
        shared = {k: v for k, v in signature.items() if k != "model"}
        if shared_signature is not None and shared != shared_signature:
            raise ValueError("Receiver runs have different frozen signatures or input sources")
        shared_signature = shared
        models.add(model)
        status["completion_sha256"] = file_hash(path / "complete.json")
        status["signature"] = signature
        sources.append(status)
        rows.extend(batch)
    return rows, sources


def markdown_report(report):
    lines = ["# Supplementary score-order diagnostic", "",
             f"Split: **{report['split']}**. **DESCRIPTIVE ONLY**. {report['tasks']} paired tasks; {report['receiver_scores']} receiver rows.", "",
             "This pilot-motivated diagnostic compares two messages for each task. It is not individual-message decoder accuracy, a new discovery gate, or evidence independent of the primary analysis. All outputs remain included; lexical differences and overt disclosure can explain ordering. No p-values are calculated.", "",
             "Intervals resample complete public tasks. Tasks were curated and have related topic families; these intervals do not establish population-wide performance. Near-zero counts include exact ties and do not change the exact-sign score.", "",
             "| Sender → receiver / system / text | Order mean [95% task CI] | Mean Δ [95% task CI] | Median Δ | Exact ties | abs(Δ) ≤ 0.001 | abs(Δ) ≤ 0.01 |", "|---|---:|---:|---:|---:|---:|---:|"]
    def display(metric):
        lo, hi = metric["ci95_task_bootstrap"]
        return f"{metric['estimate']:.5g} [{lo:.5g}, {hi:.5g}]"
    for condition, cell in report["conditions"].items():
        counts = cell["near_zero_counts"]
        lines.append(f"| {condition} | {display(cell['within_task_label_order'])} | {display(cell['delta_mean'])} | {cell['delta_median']:.5g} | {cell['exact_ties']} | {counts['0.001']} | {counts['0.01']} |")
    lines += ["", "`score-order.json` contains every task's Δ and ordering score, delta quantiles, paired original-minus-transform means and intervals, matched Qwen contrasts, and input/run/code hashes. Cross-model score-scale contrasts are descriptive and are not calibrated effect sizes.", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--receive", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True, help="New directory; existing paths are refused.")
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Output already exists")
    input_hash = file_hash(args.inputs)
    inputs = read_json(args.inputs)
    if file_hash(args.inputs) != input_hash:
        raise ValueError("Frozen inputs changed during loading")
    rows, sources = load_completed_receivers(args.receive)
    report = analyze_score_order(inputs, rows)
    report["sources"] = sources
    report["inputs"] = {"name": args.inputs.name, "sha256": input_hash}
    here = Path(__file__).parent
    report["diagnostic_sources"] = {name: file_hash(here / name) for name in (Path(__file__).name, "SCORE_ORDER_DIAGNOSTIC.md", "analyze.py", "core.py")}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "score-order.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    (args.output / "README.md").write_text(markdown_report(report), encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "descriptive_only": True, "tasks": report["tasks"], "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
