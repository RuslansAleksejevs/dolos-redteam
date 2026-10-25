#!/usr/bin/env python3
"""Descriptive post-unblind join of sealed F5 annotations and conditions.

No model inference, generation, semantic classifier, or significance test.
The mapping below normalizes synonyms from the evolving blind notes. Counts
describe those annotations; they are not validated rates of model behavior.
"""
import argparse
from collections import defaultdict
import datetime
import hashlib
import json
from pathlib import Path


MOTIFS = {
    "exam_answer_form": {"exam", "exam_qa", "language_qa"},
    "mathematics": {"math", "math_qa", "logic"},
    "test_prep_forum": {"web_boilerplate", "webpage_boilerplate"},
    "coding_help": {"bootstrap_code", "coding_request", "code", "html", "documentation"},
    "invented_fragment_entity": {"fabricated_entity", "invented_entity"},
    "grounding_or_constraint_concern": {
        "missing_context", "inconsistent_premise", "inconsistency", "unverified_answer",
        "unsupported_answer", "fabricated_constraints", "premise_shift", "unsupported_context",
        "fabricated_facts", "unsupported_claim", "false_premise_acceptance", "unsupported_sources",
        "underspecified_task", "unsupported_entities", "fabricated_api", "constraint_violation",
        "incorrect_formula", "incorrect_repair", "incorrect_explanation", "overclaim",
    },
    "ordinary_prose_advice": {
        "ordinary_advice", "web_prose", "ordinary_prose", "article", "advice", "promotion",
        "summary_task", "translation", "consumer_advice", "planning", "ordinary_request",
        "technical_prose",
    },
    "repetition_noted": {"loop", "repetition"},
    "fragment_or_incoherence": {
        "fragment", "incoherence", "format_corruption", "mixed_register", "acknowledgement_without_answer",
    },
    "clarification_noted": {"clarification"},
    "refusal_noted": {"refusal"},
}
LEXICAL = ["no_initial_whitespace", "starts_literal_ication", "contains_literal_bootstrap"]
GROUPINGS = [
    ["phase", "model"],
    ["phase", "model", "gate", "beta"],
    ["phase", "model", "prefix"],
    ["phase", "model", "gate", "beta", "prefix"],
    ["phase", "model", "gate", "beta", "seed"],
]


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(), object_pairs_hook=reject_duplicate_keys)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(rows, dimensions):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[d] for d in dimensions)].append(row)
    result = []
    for values, members in sorted(groups.items()):
        result.append({
            **dict(zip(dimensions, values)),
            "n": len(members),
            "motif_counts": {m: sum(m in r["motifs"] for r in members) for m in MOTIFS},
            "motif_blind_ids": {m: [r["blind_id"] for r in members if m in r["motifs"]] for m in MOTIFS},
            "lexical_diagnostic_counts": {m: sum(r[m] for r in members) for m in LEXICAL},
            "eos": sum(r["finish_reason"] == "eos" for r in members),
            "length": sum(r["finish_reason"] == "length" for r in members),
            "mean_generated_tokens": sum(r["generated_count"] for r in members) / len(members),
        })
    return result


def compare(root):
    names = [
        "f5-blind/blind-all.json", "f5-blind/KEY.json", "F5_UNBLIND_RECEIPT.json",
        "F5_BLIND_NOTES.json", "F5_BLIND_SUMMARY.md", "F5_BLIND_REVIEW_RECEIPT.json",
        "F5_BLIND_AUDIT.md", "F5_BLIND_AUDIT.complete.json", "open-summary/f5.json",
    ]
    hashes = {n: sha256(root / n) for n in names}
    unblind = read_json(root / "F5_UNBLIND_RECEIPT.json")
    for name, digest in unblind["sealed_files"].items():
        if hashes[name] != digest:
            raise ValueError(f"Sealed file drift: {name}")
    if hashes["f5-blind/KEY.json"] != unblind["key_sha256"]:
        raise ValueError("Key drift")
    packet = read_json(root / "f5-blind/blind-all.json")
    key = read_json(root / "f5-blind/KEY.json")
    note_file = read_json(root / "F5_BLIND_NOTES.json")
    quant = read_json(root / "open-summary/f5.json")
    if note_file["packet_sha256"] != hashes["f5-blind/blind-all.json"]:
        raise ValueError("Packet drift")
    by_id = {r["blind_id"]: r for r in packet}
    notes = {r["blind_id"]: r for r in note_file["notes"]}
    quant_rows = {(r["model"], r["case_id"]): r for r in quant["rows"]}
    if not (len(packet) == len(key) == len(note_file["notes"]) == len(quant["rows"]) == 280):
        raise ValueError("Incomplete source")
    if not (len(by_id) == len(notes) == len(quant_rows) == 280 and set(key) == set(by_id) == set(notes)):
        raise ValueError("Duplicate or mismatched IDs")
    rows = []
    for blind_id in sorted(by_id):
        raw, note, condition = by_id[blind_id], notes[blind_id], key[blind_id]
        q = quant_rows[(condition["model"], condition["case_id"])]
        digest = hashlib.sha256(raw["output_text"].encode()).hexdigest()
        if digest != note["output_text_sha256"] or digest != q["output_sha256"]:
            raise ValueError(f"Text hash mismatch: {blind_id}")
        for field in ["model", "case_id", "phase", "gate", "beta", "seed"]:
            if condition[field] != q[field]:
                raise ValueError(f"Condition mismatch: {blind_id}/{field}")
        for field in ["prefix", "finish_reason"]:
            if not raw[field] == note[field] == q[field]:
                raise ValueError(f"Packet/notes/summary mismatch: {blind_id}/{field}")
        text = raw["output_text"]
        tags = set(note["motif_tags"])
        rows.append({
            "blind_id": blind_id, **condition, "prefix": raw["prefix"],
            "finish_reason": raw["finish_reason"], "generated_count": q["generated_count"],
            "output_text_sha256": digest, "sealed_tags": note["motif_tags"],
            "motifs": [m for m, sources in MOTIFS.items() if tags & sources],
            "no_initial_whitespace": bool(text) and not text[0].isspace(),
            "starts_literal_ication": text.startswith("ication"),
            "contains_literal_bootstrap": "bootstrap" in text.lower(),
        })
    exact = defaultdict(list)
    for r in packet:
        exact[(r["prefix"], r["output_text"], r["finish_reason"])].append(r["blind_id"])
    return {
        "schema": "dolos.f5.unblinded_motif_comparison.v1",
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_sha256": hashes,
        "analysis_source_sha256": sha256(Path(__file__)),
        "method": "Post-unblind normalization and grouping of previously sealed blind tags; no per-ID annotation was changed.",
        "limits": [
            "Counts describe annotations, not validated error rates or model objectives. Categories overlap and are not exhaustive.",
            "Tag vocabulary evolved during blind reading. Synonym normalization is post-unblind and exploratory.",
            "Grounding concern includes ill-posed self-generated questions and capped answers; it is not observed disobedience.",
            "Raw prefixes have no chat template. Beta 0 uses a plausibility gate; it is not unconstrained or greedy decoding.",
            "Core has six seeds per prefix/gate/beta; diagnostic has only seed 17 and must remain separate.",
            "Qwen has beta 0 only. Distinct seeds/prefixes are related conditions, not independent semantic replications.",
            "Literal lexical diagnostics are exact string tests, not tokenization or semantic causal explanations.",
        ],
        "motif_tag_mapping": {m: sorted(ts) for m, ts in MOTIFS.items()},
        "lexical_diagnostic_rules": {
            "no_initial_whitespace": "Nonempty output whose first Unicode character is not whitespace.",
            "starts_literal_ication": "Output text starts with case-sensitive literal ication.",
            "contains_literal_bootstrap": "Lowercased output contains literal bootstrap.",
        },
        "records": rows,
        "groups": {"+".join(ds): summarize(rows, ds) for ds in GROUPINGS},
        "exact_displayed_duplicate_groups": [ids for ids in exact.values() if len(ids) > 1],
        "blind_predictions_primary": [], "blind_predictions_audit": [],
        "recommended_fresh_behavioral_candidates": [],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("Use a new output path; sealed comparisons are not overwritten.")
    result = compare(args.artifact_root)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"records": len(result["records"]), "output": str(args.out), "sha256": sha256(args.out)}))


if __name__ == "__main__":
    main()
