"""Deterministic, explicit-selection evidence bundles with verified safe restore.

Never discovers run directories by glob. Build only after final audits and a
reviewed selection. Large arrays remain local with streamed hashes, sizes and
reproduction commands. Generated text and token IDs are copied byte-for-byte.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile

SCHEMA = "targeted-discovery.bundle-selection.v1"
BLOCK = 1024 * 1024


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode()


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(BLOCK), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_name(name):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError(f"Unsafe relative path: {name!r}")
    p = PurePosixPath(name)
    if p.is_absolute() or any(x in {".", "..", ""} for x in name.split("/")) or p.as_posix() != name:
        raise ValueError(f"Unsafe relative path: {name!r}")
    return name


def source_file(root, name):
    name = safe_name(name)
    candidate = root / name
    for path in [candidate, *candidate.parents]:
        if path == root:
            break
        if path.is_symlink():
            raise ValueError(f"Symlink source refused: {name}")
    if not candidate.is_file() or not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Missing/outside source: {name}")
    return candidate


def allowed_member(name):
    safe_name(name)
    p = PurePosixPath(name)
    if p.suffix not in {".json", ".jsonl", ".md"} or p.name == "execution-start.json":
        raise ValueError(f"Excluded evidence type/name: {name}")
    if p.parts[0] == "_bundle":
        raise ValueError("Reserved bundle path")


def inspect_generation(root, name):
    prefix = safe_name(name) + "/"
    paths = {x: source_file(root, prefix + x) for x in
             ["meta.json", "inputs.json", "records.jsonl", "complete.json"]}
    meta, inputs, complete = (read(paths[x]) for x in ["meta.json", "inputs.json", "complete.json"])
    if complete.get("records_sha256") != sha_file(paths["records.jsonl"]):
        raise ValueError(f"Completion hash mismatch: {name}")
    case_ids = [x["case_id"] for x in inputs]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError(f"Duplicate input IDs: {name}")
    count = 0
    with paths["records.jsonl"].open() as stream:
        for line in stream:
            record = json.loads(line, object_pairs_hook=unique)
            if count >= len(inputs) or record.get("case_id") != case_ids[count]:
                raise ValueError(f"Record coverage/order mismatch: {name}")
            if any(record.get(k) != value for k, value in inputs[count].items()):
                raise ValueError(f"Record/input mismatch: {name}")
            if record.get("model") != meta.get("model"):
                raise ValueError(f"Model mismatch: {name}")
            count += 1
    expected = meta.get("expected_records", meta.get("records"))
    if count != len(inputs) or count != complete.get("records") or (expected is not None and count != expected):
        raise ValueError(f"Incomplete generation run: {name}")
    files = [prefix + x for x in paths]
    if str(meta.get("model", "")).startswith("noise-"):
        files += [prefix + "noise-spec.json", prefix + "noise-receipt.json"]
        for path in files[-2:]:
            source_file(root, path)
    return files, {"path": name, "kind": "generation", "records": count,
                   "model": meta.get("model"), "records_sha256": complete["records_sha256"]}


def inspect_array(root, path, expected_hash, command):
    if not isinstance(command, str) or not command.strip():
        raise ValueError(f"Missing array reproduction command: {path}")
    if PurePosixPath(path).suffix not in {".npy", ".npz"}:
        raise ValueError(f"Not a local array: {path}")
    source = source_file(root, path)
    digest = sha_file(source)
    if digest != expected_hash:
        raise ValueError(f"Array hash mismatch: {path}")
    return {"path": path, "sha256": digest, "bytes": source.stat().st_size,
            "reproduce_command": command, "included_in_archive": False}


def collect_selection(root, selection):
    if selection.get("schema") != SCHEMA:
        raise ValueError("Unsupported selection schema")
    expected = selection["expected_runs"]
    runs = selection["runs"]
    paths = [r["path"] for r in runs]
    if len(expected) != len(set(expected)) or len(paths) != len(set(paths)) or set(expected) != set(paths):
        raise ValueError("Expected run coverage differs from explicit runs")
    members, audit, arrays = set(), [], []
    for run in runs:
        name = safe_name(run["path"])
        if run["kind"] == "generation":
            files, receipt = inspect_generation(root, name)
        elif run["kind"] == "activations":
            files = [name + "/" + x for x in ["meta.json", "inputs.json", "complete.json"]]
            meta, inputs, complete = [read(source_file(root, x)) for x in files]
            if complete["rows"] != len(inputs):
                raise ValueError(f"Incomplete activation run: {name}")
            arrays.append(inspect_array(root, name + "/activations.npy", complete["activations_sha256"], run.get("reproduce_command")))
            receipt = {"path": name, "kind": "activations", "rows": len(inputs), "model": meta.get("model")}
        else:
            raise ValueError(f"Unsupported run kind: {run['kind']}")
        if members.intersection(files):
            raise ValueError("Overlapping run selection")
        members.update(files); audit.append(receipt)
    fits = selection.get("fits", [])
    if len({f["path"] for f in fits}) != len(fits):
        raise ValueError("Duplicate fit selection")
    for fit in fits:
        name = safe_name(fit["path"])
        files = [name + "/meta.json", name + "/summary.json"]
        if members.intersection(files):
            raise ValueError("Overlapping fit selection")
        meta = read(source_file(root, files[0]))
        source_file(root, files[1])
        arrays.append(inspect_array(root, name + "/directions.npz", meta["directions_sha256"], fit.get("reproduce_command")))
        members.update(files)
    extras = selection.get("files", [])
    if len(extras) != len(set(extras)) or members.intersection(extras):
        raise ValueError("Duplicate extra member selection")
    members.update(extras)
    for member in members:
        allowed_member(member)
        source_file(root, member)
    return sorted(members), audit, sorted(arrays, key=lambda x: x["path"])


def normalized_meta(raw, replacements):
    """Optional, reviewed prefix replacement applies to top-level argv only."""
    obj = json.loads(raw, object_pairs_hook=unique)
    original = obj.get("argv")
    if original is None:
        return raw, None
    if not isinstance(original, list) or any(not isinstance(s, str) for s in original):
        raise ValueError("meta.argv must be a string list")
    argv = list(original)
    for i, arg in enumerate(argv):
        for replacement in replacements:
            before, after = replacement["from"].rstrip("/"), replacement["to"].rstrip("/")
            if not before or not after:
                raise ValueError("Empty argv replacement prefix")
            if arg == before or arg.startswith(before + "/"):
                argv[i] = after + arg[len(before):]
                break
    if argv == original:
        return raw, None
    obj["argv"] = argv
    return encoded(obj), {"field": "argv", "method": "explicit path-prefix replacement; other JSON fields unchanged"}


def build(root, selection_path, output):
    root, output = Path(root), Path(output)
    selection = read(selection_path)
    names, audit, arrays = collect_selection(root, selection)
    replacements = selection.get("normalize_meta_argv_prefixes", [])
    payloads, manifest_members = {}, {}
    for name in names:
        source = source_file(root, name)
        source_digest = sha_file(source)
        transform = None
        if replacements and PurePosixPath(name).name == "meta.json":
            raw, transform = normalized_meta(source.read_bytes(), replacements)
            if transform:
                payloads[name] = raw
        if transform:
            digest, size = sha_bytes(payloads[name]), len(payloads[name])
        else:
            digest, size = source_digest, source.stat().st_size
        manifest_members[name] = {"sha256": digest, "bytes": size,
                                  "source_sha256": source_digest, "transformation": transform}
    generated = {"_bundle/SELECTION.json": encoded(selection),
                 "_bundle/LOCAL_ARRAYS.json": encoded({"schema": "targeted-discovery.local-arrays.v1", "arrays": arrays})}
    for name, raw in generated.items():
        payloads[name] = raw
        manifest_members[name] = {"sha256": sha_bytes(raw), "bytes": len(raw),
                                  "source_sha256": None, "transformation": "bundle metadata"}
    manifest = {"schema": "targeted-discovery.archive-manifest.v1",
                "members": manifest_members, "completed_runs": audit,
                "excluded_types": ["*.log", "execution-start.json", "*.npy", "*.npz"],
                "raw_record_policy": "records.jsonl and generated text/token IDs are byte-preserved",
                "local_arrays": arrays}
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    archive = output / "evidence.tar.gz"
    with archive.open("xb") as destination:
        with gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0, compresslevel=9) as compressed:
            with tarfile.open(fileobj=compressed, mode="w|", format=tarfile.USTAR_FORMAT) as tar:
                for name, record in sorted(manifest_members.items()):
                    info = tarfile.TarInfo(name)
                    info.size, info.mode, info.mtime = record["bytes"], 0o600, 0
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    if name in payloads:
                        tar.addfile(info, io.BytesIO(payloads[name]))
                    else:
                        with source_file(root, name).open("rb") as stream:
                            tar.addfile(info, stream)
                        if sha_file(source_file(root, name)) != record["source_sha256"]:
                            raise ValueError(f"Source changed during packaging: {name}")
    manifest_path = output / "ARCHIVE_MANIFEST.json"
    manifest_path.write_bytes(encoded(manifest))
    receipt = {"schema": "targeted-discovery.bundle.v1", "archive": "evidence.tar.gz",
               "sha256": sha_file(archive), "bytes": archive.stat().st_size,
               "manifest_sha256": sha_file(manifest_path), "members": len(manifest_members),
               "local_arrays_excluded": len(arrays)}
    (output / "BUNDLE.json").write_bytes(encoded(receipt))
    verify_bundle(output)
    return receipt


def verify_bundle(bundle):
    bundle = Path(bundle)
    receipt, manifest = read(bundle / "BUNDLE.json"), read(bundle / "ARCHIVE_MANIFEST.json")
    if receipt.get("schema") != "targeted-discovery.bundle.v1" or manifest.get("schema") != "targeted-discovery.archive-manifest.v1":
        raise ValueError("Unsupported bundle schema")
    archive_name = safe_name(receipt["archive"])
    archive = source_file(bundle, archive_name)
    if sha_file(archive) != receipt["sha256"] or archive.stat().st_size != receipt["bytes"]:
        raise ValueError("Archive checksum/size mismatch")
    if sha_file(bundle / "ARCHIVE_MANIFEST.json") != receipt["manifest_sha256"]:
        raise ValueError("Manifest checksum mismatch")
    expected = manifest["members"]
    if receipt["members"] != len(expected):
        raise ValueError("Manifest member count mismatch")
    for name in expected:
        safe_name(name)
    seen = set()
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            name = safe_name(member.name)
            if not member.isfile() or member.issparse() or name in seen or name not in expected:
                raise ValueError(f"Unsupported/duplicate/unexpected member: {name}")
            if member.size != expected[name]["bytes"]:
                raise ValueError(f"Member size mismatch: {name}")
            stream = tar.extractfile(member)
            digest = hashlib.sha256()
            count = 0
            for block in iter(lambda: stream.read(BLOCK), b""):
                digest.update(block); count += len(block)
            if count != member.size or digest.hexdigest() != expected[name]["sha256"]:
                raise ValueError(f"Member checksum mismatch: {name}")
            seen.add(name)
    if seen != set(expected):
        raise ValueError("Missing archive members")
    return manifest


def restore(bundle, destination):
    bundle, destination = Path(bundle), Path(destination)
    manifest = verify_bundle(bundle)  # Validate every member before writing any.
    if destination.is_symlink() or (destination.exists() and (not destination.is_dir() or any(destination.iterdir()))):
        raise ValueError("Restore destination must be a new or empty non-symlink directory")
    # Canonicalize ordinary OS aliases (for example /var -> /private/var).
    # The destination itself cannot be a symlink and starts completely empty.
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    receipt = read(bundle / "BUNDLE.json")
    seen = set()
    with tarfile.open(bundle / receipt["archive"], "r:gz") as tar:
        for member in tar:
            name = safe_name(member.name)
            if not member.isfile() or member.issparse() or name in seen or name not in manifest["members"]:
                raise ValueError("Archive changed during restore")
            if member.size != manifest["members"][name]["bytes"]:
                raise ValueError("Archive changed during restore")
            seen.add(name)
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with target.open("xb") as stream:
                source = tar.extractfile(member)
                for block in iter(lambda: source.read(BLOCK), b""):
                    stream.write(block)
            target.chmod(0o600)
            if sha_file(target) != manifest["members"][member.name]["sha256"]:
                raise ValueError("Restore write verification failed")
    if seen != set(manifest["members"]):
        raise ValueError("Archive coverage changed during restore")
    return {"restored_members": len(manifest["members"]), "verified": True,
            "large_arrays_restored": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("build")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--selection", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("restore")
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--destination", type=Path, required=True)
    p = sub.add_parser("verify")
    p.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        result = build(args.root, args.selection, args.output)
    elif args.command == "restore":
        result = restore(args.bundle, args.destination)
    else:
        result = {"verified": True, "members": len(verify_bundle(args.bundle)["members"])}
    print(json.dumps(result, indent=2))
