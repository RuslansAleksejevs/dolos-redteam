"""Reconstruct published runs and compare all 16 planned length-check cases."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMPTS = {"chat-01", "chat-02", "raw-01", "raw-02"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse(data):
    def reject_constant(value):
        raise ValueError(f"Nonstandard JSON constant: {value}")
    return json.loads(data, object_pairs_hook=unique, parse_constant=reject_constant)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_run(folder):
    manifest_bytes = (folder / "manifest.json").read_bytes()
    metadata_bytes = (folder / "metadata.json").read_bytes()
    manifest, metadata = parse(manifest_bytes), parse(metadata_bytes)
    require(metadata["status"] == "completed", "Source run is not complete")
    chunks, names = [], set()
    for entry in manifest["files"]:
        name = entry["file"]
        require(name not in names, "Duplicate manifest file")
        names.add(name)
        path = (folder / name).resolve()
        require(path.is_relative_to(folder.resolve()), "Manifest file must remain inside its run folder")
        data = path.read_bytes()
        require(sha(data) == entry["sha256"], f"Chunk hash mismatch: {name}")
        require(len(data.splitlines()) == entry["completions"], f"Chunk count mismatch: {name}")
        chunks.append(data)
    data = b"".join(chunks)
    require(sha(data) == manifest["original_responses_sha256"], "Reconstructed response hash mismatch")
    rows = [parse(line) for line in data.splitlines()]
    require(len(rows) == manifest["total_completions"] == metadata["planned_completions"]
            == metadata["completed_completions"], "Run counts disagree")
    require([r["index"] for r in rows] == list(range(len(rows))), "Response indices are incomplete or reordered")
    if "planned_cases" in metadata:
        fields = ["index", "prompt", "system", "system_label", "settings"]
        require([{key: row[key] for key in fields} for row in rows] == metadata["planned_cases"],
                "Responses differ from the frozen planned cases")
    source = {"manifest_sha256": sha(manifest_bytes), "metadata_sha256": sha(metadata_bytes),
              "responses_sha256": sha(data), "code_revision": metadata["code_revision"],
              "code_sha256": metadata["code_sha256"]}
    return metadata, rows, source


def case_key(row):
    s = row["settings"]
    return (row["prompt"]["id"], row["system"], row["system_label"], s["target"], s["alpha"], s["seed"])


def compare(old_meta, old_rows, new_meta, new_rows):
    for field in ["model_revisions", "device", "dtype", "python", "packages"]:
        require(old_meta[field] == new_meta[field], f"Runtime/model mismatch: {field}")
    require(old_meta["code_sha256"]["model_io.py"] == new_meta["code_sha256"]["model_io.py"],
            "The model loader changed")
    expected = {(pid, "dolos", alpha, seed) for pid in PROMPTS for alpha in [0, 1] for seed in [17, 29]}
    observed = {(r["prompt"]["id"], r["settings"]["target"], r["settings"]["alpha"], r["settings"]["seed"])
                for r in new_rows}
    require(len(new_rows) == 16 and observed == expected, "The complete prescribed 16-case length grid is required")
    old_by_key = {case_key(row): row for row in old_rows}
    require(len(old_by_key) == len(old_rows), "Duplicate parent experimental condition")
    results = []
    for new in new_rows:
        key = case_key(new)
        require(key in old_by_key, "No identical prompt/system/target/alpha/seed condition in the pilot")
        old = old_by_key[key]
        require(new["prompt"] == old["prompt"], f"Prompt content changed: {key[0]}")
        require(new["input_ids"] == old["input_ids"], f"Input token IDs changed: {key[0]}")
        settings = lambda row: {k: v for k, v in row["settings"].items() if k != "max_tokens"}
        require(settings(new) == settings(old), f"Non-budget generation settings changed: {key[0]}")
        require(new["settings"]["max_tokens"] > old["settings"]["max_tokens"], "New cap must exceed old cap")
        for row in [old, new]:
            require(row["stop_reason"] in ["eos", "length"], "Unrecognized stop reason")
            size, cap = len(row["output_ids"]), row["settings"]["max_tokens"]
            require(0 < size <= cap, "Output length is outside its budget")
            require(row["stop_reason"] != "length" or size == cap, "Length stop does not reach its cap")
        old_ids, new_ids = old["output_ids"], new["output_ids"]
        mismatch = next((i for i, token in enumerate(old_ids)
                         if i >= len(new_ids) or token != new_ids[i]), None)
        eos_same = (new_ids == old_ids and new["stop_reason"] == "eos") if old["stop_reason"] == "eos" else None
        results.append({
            "prompt_id": key[0], "system": key[1], "system_label": key[2],
            "target": key[3], "alpha": key[4], "seed": key[5],
            "old_index": old["index"], "new_index": new["index"],
            "old_cap": old["settings"]["max_tokens"], "new_cap": new["settings"]["max_tokens"],
            "old_tokens": len(old_ids), "new_tokens": len(new_ids),
            "old_stop_reason": old["stop_reason"], "new_stop_reason": new["stop_reason"],
            "prefix_matches": mismatch is None, "first_mismatch_position": None if mismatch is None else mismatch + 1,
            "old_token_at_mismatch": None if mismatch is None else old_ids[mismatch],
            "new_token_at_mismatch": None if mismatch is None or mismatch >= len(new_ids) else new_ids[mismatch],
            "eos_reproduced_exactly": eos_same,
        })
    mismatches = sum(not row["prefix_matches"] or row["eos_reproduced_exactly"] is False for row in results)
    return {"status": "matched" if mismatches == 0 else "mismatches_found", "comparisons": len(results),
            "mismatched_cases": mismatches,
            "note": "Exact token prefixes include the original EOS token; longer reruns are not independent samples.",
            "rows": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", type=Path, default=HERE.parent / "2026-10-24-lda" / "pilot")
    parser.add_argument("--new", type=Path, default=HERE / "length-check")
    parser.add_argument("--output", type=Path, default=HERE / "length-comparison.json")
    args = parser.parse_args()
    old_meta, old_rows, old_source = read_run(args.old)
    new_meta, new_rows, new_source = read_run(args.new)
    result = compare(old_meta, old_rows, new_meta, new_rows)
    result.update(old_source=old_source, new_source=new_source)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: result[k] for k in ["status", "comparisons", "mismatched_cases"]}))


if __name__ == "__main__":
    main()
