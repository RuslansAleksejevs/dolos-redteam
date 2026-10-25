"""Export the frozen, metadata-masked confirmation quality sample.

This is a post-hoc descriptive supplement, never an outcome filter or endpoint.
Without --send, validate the plan using frozen input identities only.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from audit_output_quality import read_completed_sender
from core import MODELS, SYSTEM_MODES, build_cases, read_json, sha_text


ROOT = Path(__file__).resolve().parents[2]
SELECTION_SALT = "confirmation-quality-v1|"
OPAQUE_SALT = "confirmation-quality-v1|blind|"


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_sample(cases):
    selected = []
    for model in MODELS:
        for mode in SYSTEM_MODES:
            for label in ("A", "B"):
                cell = [c for c in cases if (c["sender_model"], c["system_mode"], c["label"])
                        == (model, mode, label)]
                ranked = sorted(cell, key=lambda c: sha_text(SELECTION_SALT + c["case_id"]))
                if len(ranked) != 100:
                    raise ValueError("Expected 100 cases in every model/system/label stratum")
                for rank, case in enumerate(ranked[:5], 1):
                    selected.append({key: case[key] for key in
                                     ("case_id", "task_id", "sender_model", "system_mode", "label")}
                                    | {"rank_within_stratum": rank,
                                       "selection_sha256": sha_text(SELECTION_SALT + case["case_id"]),
                                       "opaque_id": sha_text(OPAQUE_SALT + case["case_id"])})
    return sorted(selected, key=lambda case: case["opaque_id"])


def validate_plan(path):
    plan = read_json(path)
    if plan["schema_version"] != "punctuation-channel.confirmation-quality-sample.v1":
        raise ValueError("Unknown sampling plan")
    if plan["selection_salt"] != SELECTION_SALT or plan["opaque_id_salt"] != OPAQUE_SALT:
        raise ValueError("Sampling salts differ from the fixed rule")
    for key in ("input", "core"):
        source = ROOT / plan[key]["path"]
        if file_sha(source) != plan[key]["sha256"]:
            raise ValueError(f"Frozen {key} hash mismatch")
    data = read_json(ROOT / plan["input"]["path"])
    if data["split"] != "confirmation" or len(data["items"]) != 100:
        raise ValueError("Expected the frozen 100-task confirmation inputs")
    cases = build_cases([{**item, "split": data["split"]} for item in data["items"]],
                        list(SYSTEM_MODES), list(MODELS))
    expected = expected_sample(cases)
    if plan["selected_cases"] != expected or plan["sample_size"] != 60 or plan["population_size"] != 1200:
        raise ValueError("Saved sample does not match deterministic stratified selection")
    counts = Counter((c["sender_model"], c["system_mode"], c["label"]) for c in expected)
    if len({c["case_id"] for c in expected}) != 60 or set(counts.values()) != {5} or len(counts) != 12:
        raise ValueError("The selected sample is not unique and balanced")
    return plan, {case["case_id"]: case for case in cases}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--send", type=Path, action="append", default=[],
                        help="Repeat for both completed confirmation sender runs.")
    parser.add_argument("--output", type=Path, help="New JSONL containing only opaque_id and text.")
    args = parser.parse_args(argv)
    plan, expected = validate_plan(args.plan)
    if not args.send:
        if args.output:
            parser.error("--output requires both completed --send runs")
        print(json.dumps({"plan_verified": True, "population": len(expected), "sample": 60,
                          "strata": 12, "per_stratum": 5}))
        return 0
    if len(args.send) != 2 or not args.output:
        parser.error("Export requires two completed --send runs and --output")
    receipt_path = args.output.with_name(args.output.name + ".receipt.json")
    if args.output.exists() or receipt_path.exists():
        parser.error("Refusing to overwrite the review export or its receipt")
    rows, sources = {}, []
    for directory in args.send:
        records, source = read_completed_sender(directory)
        if source["source_hashes"].get("punctuation-channel/core.py") != plan["core"]["sha256"]:
            raise ValueError("Sender source does not match the frozen core")
        sources.append(source)
        for row in records:
            case_id = row["case_id"]
            if case_id in rows or case_id not in expected or row["split"] != "confirmation":
                raise ValueError("Duplicate, unexpected, or non-confirmation sender case")
            if any(row[key] != value for key, value in expected[case_id].items()):
                raise ValueError("Sender case metadata differs from the frozen input plan")
            if not isinstance(row["output_text"], str) or sha_text(row["output_text"]) != row["output_sha256"]:
                raise ValueError("Sender output text/hash mismatch")
            rows[case_id] = row
    if set(rows) != set(expected) or {source["model"] for source in sources} != set(MODELS):
        raise ValueError("Both complete 600-output sender grids are required")
    exported = [{"opaque_id": case["opaque_id"], "text": rows[case["case_id"]]["output_text"]}
                for case in plan["selected_cases"]]
    encoded = "".join(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n" for row in exported)
    receipt = {"analysis_role": "posthoc_descriptive_quality_control", "created_at": datetime.now(timezone.utc).isoformat(),
               "plan_sha256": file_sha(args.plan), "exporter_sha256": file_sha(__file__),
               "export_sha256": sha_text(encoded), "exported_rows": 60, "sources": sources,
               "reviewer_instruction": "Review only the JSONL; withhold this receipt and the sampling plan until annotations are frozen."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(encoded)
    with receipt_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps({"exported_rows": len(exported), "export_sha256": receipt["export_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
