"""Deterministic direct-screen archive and verified, byte-preserving restoration."""
import argparse
import gzip
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path

FILES = {"meta.json", "inputs.json", "records.jsonl", "complete.json"}
SAFE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse(data):
    return json.loads(data, object_pairs_hook=unique)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_run(data):
    meta, inputs, complete = (parse(data[name]) for name in ("meta.json", "inputs.json", "complete.json"))
    require(data["records.jsonl"].endswith(b"\n"), "Records lack final newline")
    rows = [parse(line) for line in data["records.jsonl"].splitlines()]
    ids, modes = [x["case_id"] for x in inputs], meta["system_modes"]
    require(len(ids) == len(set(ids)) and len(modes) == len(set(modes)), "Duplicate input IDs/modes")
    expected = {(case, mode) for case in ids for mode in modes}
    observed = [(r["case_id"], r["system_mode"]) for r in rows]
    require(bool(expected) and len(rows) == len(expected) and set(observed) == expected, "Incomplete/duplicate coverage")
    require(observed == [tuple(pair) for pair in meta["record_order"]], "Record order differs")
    require(len(rows) == meta["expected_records"] == complete["records"], "Record count differs")
    require(all(r["record_id"] == f"{r['system_mode']}:{r['case_id']}" and r["model"] == meta["model"] for r in rows), "Record identity differs")
    require(sha(data["inputs.json"]) == meta["input_sha256"] == complete["input_sha256"], "Input hash differs")
    for filename, key in (("records.jsonl", "records_sha256"), ("meta.json", "meta_sha256")):
        require(sha(data[filename]) == complete[key], f"Complete-marker hash differs: {filename}")


def safe_name(name):
    parts = name.split("/")
    return len(parts) == 2 and bool(SAFE.fullmatch(parts[0])) and parts[1] in FILES


def pack(runs, output):
    payload = {}
    for directory in runs:
        require(directory.is_dir() and not directory.is_symlink() and bool(SAFE.fullmatch(directory.name)), "Unsafe run directory")
        require(not any(name.startswith(directory.name + "/") for name in payload), "Duplicate run basename")
        data = {}
        for name in FILES:
            path = directory / name
            require(path.is_file() and not path.is_symlink(), f"Missing/nonregular file: {path}")
            data[name] = path.read_bytes()
        validate_run(data)
        payload.update({f"{directory.name}/{name}": content for name, content in data.items()})
    require(bool(payload), "No runs")
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, content in sorted(payload.items()):
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(content), 0o644, 0
            archive.addfile(info, io.BytesIO(content))
    compressed = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=compressed, mtime=0) as handle:
        handle.write(buffer.getvalue())
    raw = compressed.getvalue()
    manifest = {"schema_version": "direct-screen-archive.v1", "archive": "raw.tar.gz", "archive_sha256": sha(raw),
                "files": {name: {"sha256": sha(content), "bytes": len(content)} for name, content in sorted(payload.items())}}
    output.mkdir(parents=True, exist_ok=False)
    (output / "raw.tar.gz").write_bytes(raw)
    (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def restore(source, manifest_path, destination):
    require(not source.is_symlink() and not manifest_path.is_symlink(), "Symlink archive/manifest")
    raw, manifest = source.read_bytes(), parse(manifest_path.read_bytes())
    require(manifest["schema_version"] == "direct-screen-archive.v1" and sha(raw) == manifest["archive_sha256"], "Archive hash/schema differs")
    entries, payload = manifest["files"], {}
    require(bool(entries) and all(safe_name(name) for name in entries), "Unsafe/empty manifest paths")
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for member in archive:
            require(member.isfile() and member.name in entries and member.name not in payload, "Unexpected/duplicate/nonregular member")
            require(member.size == entries[member.name]["bytes"], "Member size differs")
            content = archive.extractfile(member).read()
            require(sha(content) == entries[member.name]["sha256"], "Member hash differs")
            payload[member.name] = content
    require(set(payload) == set(entries), "Missing archive member")
    for run in {name.split("/")[0] for name in payload}:
        data = {name.split("/")[1]: content for name, content in payload.items() if name.startswith(run + "/")}
        require(set(data) == FILES, "Run has incomplete file set")
        validate_run(data)
    destination.mkdir(parents=True, exist_ok=False)
    for name, content in sorted(payload.items()):
        target = destination / name
        target.parent.mkdir(exist_ok=True)
        with target.open("xb") as handle:
            handle.write(content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--restore", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    if args.runs and args.output and not any((args.restore, args.manifest, args.destination)):
        pack(args.runs, args.output)
    elif args.restore and args.manifest and args.destination and not any((args.runs, args.output)):
        restore(args.restore, args.manifest, args.destination)
    else:
        parser.error("Use --runs DIR ... --output NEWDIR, or --restore ARCHIVE --manifest MANIFEST --destination NEWDIR")
