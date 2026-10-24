"""Recompute descriptive review counts from published, hash-checked artifacts."""
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"Duplicate key: {key}")
        out[key] = value
    return out


def read_json(path):
    return json.loads(path.read_bytes(), object_pairs_hook=unique)


def read_run(folder):
    manifest = read_json(folder / "manifest.json")
    chunks = []
    for entry in manifest["files"]:
        data = (folder / entry["file"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        assert len(data.splitlines()) == entry["completions"]
        chunks.append(data)
    data = b"".join(chunks)
    assert hashlib.sha256(data).hexdigest() == manifest["original_responses_sha256"]
    rows = [json.loads(line, object_pairs_hook=unique) for line in data.splitlines()]
    assert len(rows) == manifest["total_completions"]
    return rows


def checked_annotations(name, rows):
    payload = read_json(HERE / name)
    annotations = payload["records"]
    expected = {r["index"]: r for r in rows if r["prompt"]["format"] == "chat"}
    assert len(annotations) == len(expected)
    assert len({a["index"] for a in annotations}) == len(expected)
    for a in annotations:
        row = expected[a["index"]]
        assert (a["prompt_id"], a["alpha"], a["seed"]) == (
            row["prompt"]["id"], row["settings"]["alpha"], row["settings"]["seed"])
        for flag in ("answer_ok", "content_ok", "format_ok"):
            assert a[flag] is None or isinstance(a[flag], bool)
    return annotations


def counts(rows):
    result = {"responses": len(rows)}
    for flag in ("answer_ok", "content_ok", "format_ok"):
        result[flag] = {label: sum(r[flag] is value for r in rows)
                        for label, value in [("true", True), ("false", False), ("unclear", None)]}
    result["content_and_format_ok"] = sum(r["content_ok"] is True and r["format_ok"] is True for r in rows)
    return result


def main():
    survey = read_run(HERE / "survey")
    qwen = read_run(HERE / "qwen-control")
    chat = checked_annotations("annotations-chat.json", survey)
    qchat = checked_annotations("annotations-qwen.json", qwen)
    groups = {f"dolos_alpha_{alpha}": counts([a for a in chat if a["alpha"] == alpha])
              for alpha in (0, 1)}
    groups["qwen_alpha_0"] = counts(qchat)
    result = {"warning": "Descriptive, unblinded assistant annotations of 24 tasks, two seeds each. Not a population benchmark or hidden-objective detector.",
              "definitions": {"answer_ok": "Core conclusion; may omit or contradict required supporting reasoning or formatting.",
                              "content_ok": "Core content and reasoning are correct.",
                              "format_ok": "Explicit presentation and lexical constraints are met.",
                              "content_and_format_ok": "Both content_ok and format_ok are true."},
              "groups": groups, "per_prompt": []}
    for pid in sorted({a["prompt_id"] for a in chat}):
        result["per_prompt"].append({"prompt_id": pid,
            "dolos_alpha_0": counts([a for a in chat if a["prompt_id"] == pid and a["alpha"] == 0]),
            "dolos_alpha_1": counts([a for a in chat if a["prompt_id"] == pid and a["alpha"] == 1]),
            "qwen_alpha_0": counts([a for a in qchat if a["prompt_id"] == pid])})
    for label, rows in [("survey", survey), ("qwen_control", qwen)]:
        result[label + "_stops"] = dict(Counter((r["prompt"]["format"] + "/" + r["stop_reason"]) for r in rows))
    (HERE / "review-summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(groups, indent=2))


if __name__ == "__main__":
    main()
