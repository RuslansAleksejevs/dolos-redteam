"""Post-hoc descriptive QC of completed sender runs; no model inference.

All outputs are retained. Identical A/B message pairs bound what any fixed,
deterministic message-only decoder can achieve on this realized collection.
That bound is not an estimate of a population effect or proof about a channel.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from statistics import mean, median

from core import MODELS, SYSTEM_MODES, read_json, sha_text


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _finite_float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("Non-finite JSON number")
    return parsed


def _reject_constant(value):
    raise ValueError(f"Non-finite JSON constant: {value}")


def read_completed_sender(directory):
    """Validate the complete artifact before exposing any records to QC."""
    directory = Path(directory)
    if not (directory / "complete.json").is_file():
        raise ValueError(f"Refusing incomplete sender run: {directory}")
    meta = read_json(directory / "meta.json")
    if meta["signature"]["stage"] != "send":
        raise ValueError(f"Expected a sender run: {directory}")
    completion = read_json(directory / "complete.json")
    raw = (directory / "records.jsonl").read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if completion["records_sha256"] != digest:
        raise ValueError(f"Completed sender hash mismatch: {directory}")
    rows = []
    for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"Blank JSONL line {number} in {directory}")
        row = json.loads(line, object_pairs_hook=_unique_object,
                         parse_float=_finite_float, parse_constant=_reject_constant)
        if not isinstance(row, dict):
            raise ValueError("Sender records must be JSON objects")
        rows.append(row)
    if completion["records"] != len(rows):
        raise ValueError(f"Completed sender count mismatch: {directory}")
    return rows, {
        "name": directory.name, "records": len(rows), "records_sha256": digest,
        "meta_sha256": hashlib.sha256((directory / "meta.json").read_bytes()).hexdigest(),
        "model": meta["signature"]["model"],
        "source_hashes": meta["signature"].get("sources", {}),
        "completed_at": completion.get("completed_at"),
    }


def _length_summary(values):
    if not values:
        return {"count": 0, "min": None, "median": None, "mean": None, "max": None}
    return {"count": len(values), "min": min(values), "median": median(values),
            "mean": mean(values), "max": max(values)}


def _flags(row):
    text = row["output_text"]
    return {
        "empty_or_whitespace_only": not text.strip(),
        "no_unicode_word_tokens": not bool(re.search(r"\w", text)),
        "initially_capped": row["initial_finish_reason"] == "length",
        "extended": bool(row["extended"]),
        "still_capped": row["finish_reason"] == "length",
        "recorded_chatml_marker": bool(row.get("chatml_marker_flags")),
        "literal_chatml_marker": any(marker in text for marker in ("<|im_start|>", "<|im_end|>", "<|endoftext|>")),
        "nonterminal_special_token": bool(row.get("nonterminal_special_token_ids")),
        "literal_bracketed_end_of_text": "[END_OF_TEXT]" in text,
    }


def quality_report(rows, sources=()):
    """Describe each model/system cell, retaining both labels of every task.

    Every within-task identical pair forces at least one error among its two
    differently labelled observations. For k such pairs among N paired tasks,
    accuracy is at most (2N-k)/(2N). Other duplicated texts can tighten this
    bound; this intentionally reports only the requested within-task ceiling.
    """
    if not rows:
        raise ValueError("Output QC requires at least one completed sender run")
    splits = {row["split"] for row in rows}
    if len(splits) != 1 or not splits <= {"pilot", "confirmation"}:
        raise ValueError("Analyze one recognized split at a time")
    grouped = defaultdict(lambda: defaultdict(dict))
    seen_ids = set()
    for row in rows:
        case_id = row["case_id"]
        if case_id in seen_ids:
            raise ValueError(f"Duplicate sender case across inputs: {case_id}")
        seen_ids.add(case_id)
        if row["sender_model"] not in MODELS or row["system_mode"] not in SYSTEM_MODES or row["label"] not in {"A", "B"}:
            raise ValueError("Unexpected sender condition or label")
        if not isinstance(row["output_text"], str):
            raise ValueError("Sender output must be text")
        if row["output_sha256"] != sha_text(row["output_text"]):
            raise ValueError(f"Sender text hash mismatch: {case_id}")
        count = row["generated_count"]
        if isinstance(count, bool) or not isinstance(count, int) or count < 1 or count != len(row["generated_token_ids"]):
            raise ValueError("Generated token count disagrees with token IDs")
        if row["finish_reason"] not in {"eos", "length"} or row["initial_finish_reason"] not in {"eos", "length"}:
            raise ValueError("Unrecognized finish reason")
        if row["extended"] and row.get("extension_prefix_verified") is not True:
            raise ValueError("Extended output lacks verified prefix")
        label_map = grouped[(row["sender_model"], row["system_mode"])][row["task_id"]]
        if row["label"] in label_map:
            raise ValueError("Duplicate task/label within a sender condition")
        label_map[row["label"]] = row
    conditions = {}
    for (model, mode), tasks in sorted(grouped.items()):
        pair_count, identical_count = len(tasks), 0
        identical_ids = []
        cell_rows = []
        for task_id, pair in sorted(tasks.items()):
            if set(pair) != {"A", "B"}:
                raise ValueError(f"Missing paired label: {model}/{mode}/{task_id}")
            if pair["A"]["public_task"] != pair["B"]["public_task"] or pair["A"]["seed"] != pair["B"]["seed"]:
                raise ValueError("Paired tasks must share public text and generation seed")
            identical = pair["A"]["output_text"].encode("utf-8") == pair["B"]["output_text"].encode("utf-8")
            if identical:
                identical_count += 1
                identical_ids.append(sha_text(f"{model}/{mode}/{task_id}"))
            cell_rows.extend((pair["A"], pair["B"]))
        flag_counts = Counter()
        for row in cell_rows:
            flag_counts.update(name for name, present in _flags(row).items() if present)
        all_flags = tuple(_flags(cell_rows[0]))
        conditions[f"{model}/{mode}"] = {
            "tasks": pair_count, "outputs": len(cell_rows), "label_counts": {"A": pair_count, "B": pair_count},
            "byte_identical_ab_pairs": identical_count,
            "byte_identical_pair_fraction": identical_count / pair_count,
            "deterministic_message_only_accuracy_upper_bound": 1 - identical_count / (2 * pair_count),
            "upper_bound_formula": "1 - byte_identical_ab_pairs / (2 * tasks)",
            "identical_pair_opaque_ids": identical_ids,
            "lengths": {
                "unicode_characters": _length_summary([len(row["output_text"]) for row in cell_rows]),
                "utf8_bytes": _length_summary([len(row["output_text"].encode("utf-8")) for row in cell_rows]),
                "unicode_word_tokens": _length_summary([len(re.findall(r"\w+", row["output_text"])) for row in cell_rows]),
                "generated_tokens_including_terminal_stop": _length_summary([row["generated_count"] for row in cell_rows]),
            },
            "flag_counts": {name: flag_counts[name] for name in all_flags},
            "finish_reason_counts": dict(sorted(Counter(row["finish_reason"] for row in cell_rows).items())),
        }
    expected_conditions = {f"{model}/{mode}" for model in MODELS for mode in SYSTEM_MODES}
    return {
        "schema_version": "punctuation-channel.output-quality.v1",
        "analysis_role": "posthoc_descriptive_quality_control",
        "split": next(iter(splits)), "outputs": len(rows), "sources": list(sources),
        "conditions": conditions,
        "missing_model_system_conditions": sorted(expected_conditions - set(conditions)),
        "all_six_model_system_conditions_present": set(conditions) == expected_conditions,
        "interpretation": [
            "No output is removed or relabelled; this supplement does not change the frozen primary analysis.",
            "The ceiling applies to this realized balanced sample and a fixed deterministic decoder seeing message text, not the hidden label or source metadata.",
            "Identical text cannot support different deterministic answers. The ceiling does not prove that any other pair carries a decodable signal.",
            "Cross-task message collisions can make the attainable accuracy lower than this within-task ceiling.",
            "No statistical significance, population estimate, or evidence of an intentionally trained covert channel is claimed.",
            "Bracketed [END_OF_TEXT] is counted as literal ordinary text, separately from tokenizer special-token or ChatML flags.",
            "Length counts are descriptive. Generated token counts include a terminal stop token when present; text counts do not.",
        ],
    }


def blind_review_rows(rows):
    """Expose only opaque case hash and exact generated text, in hash order."""
    exported = [{"opaque_id": sha_text(row["case_id"]), "text": row["output_text"]} for row in rows]
    if len({row["opaque_id"] for row in exported}) != len(exported):
        raise ValueError("Duplicate opaque review ID")
    return sorted(exported, key=lambda row: row["opaque_id"])


def _write_new(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--send", type=Path, action="append", required=True,
                        help="Completed sender directory; repeat for both models.")
    parser.add_argument("--output", type=Path, help="Write a new JSON report; otherwise print it.")
    parser.add_argument("--blind-review", type=Path,
                        help="Optional new JSONL export containing only opaque hash IDs and output text.")
    args = parser.parse_args(argv)
    for path in (args.output, args.blind_review):
        if path is not None and path.exists():
            parser.error(f"Refusing to overwrite existing output: {path}")
    all_rows, sources = [], []
    for directory in args.send:
        rows, source = read_completed_sender(directory)
        all_rows.extend(rows)
        sources.append(source)
    report = quality_report(all_rows, sources)
    report["created_at"] = datetime.now(timezone.utc).isoformat()
    report["qc_code_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    encoded = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output:
        _write_new(args.output, encoded)
    else:
        print(encoded, end="")
    if args.blind_review:
        encoded_blind = "".join(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n" for row in blind_review_rows(all_rows))
        _write_new(args.blind_review, encoded_blind)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
