"""Package completed audit runs losslessly without large raw-text Git diffs.

Uses the Python standard library only. Originals remain untouched. JSONL files
and initial-capped JSON files larger than 200 KiB receive deterministic gzip;
other files are copied byte for byte. The package verifies itself before return.
"""
import argparse
from contextlib import contextmanager
import gzip
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import stat

SCHEMA = "punctuation-channel.compressed-package.v1"
CHUNK_SIZE = 1024 * 1024
CAPPED_THRESHOLD = 200 * 1024


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("Non-finite JSON number")
    return parsed


def _reject(value):
    raise ValueError(f"Non-finite JSON value: {value}")


def parse_json(value):
    return json.loads(value, object_pairs_hook=_unique, parse_float=_float, parse_constant=_reject)


@contextmanager
def safe_read(path):
    """Reject symlink files and nonregular files, including before byte reads."""
    path = Path(path)
    if path.is_symlink():
        raise ValueError(f"Symlinks are not allowed: {path}")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ValueError(f"Not a regular file: {path}")
    with os.fdopen(descriptor, "rb") as stream:
        yield stream


def sha_size(stream):
    digest, size = hashlib.sha256(), 0
    while block := stream.read(CHUNK_SIZE):
        digest.update(block)
        size += len(block)
    return digest.hexdigest(), size


def file_info(path):
    with safe_read(path) as stream:
        digest, size = sha_size(stream)
    return {"sha256": digest, "bytes": size}


def inspect_records(stream):
    digest, size, count, ids = hashlib.sha256(), 0, 0, set()
    for line in stream:
        digest.update(line)
        size += len(line)
        if not line.endswith(b"\n") or not line.strip():
            raise ValueError("Records must contain nonblank, newline-terminated JSON objects")
        row = parse_json(line.decode("utf-8"))
        if not isinstance(row, dict):
            raise ValueError("Each record must be a JSON object")
        key = row.get("record_id")
        if not isinstance(key, str) or not key or key in ids:
            raise ValueError("Record IDs must be nonempty unique strings")
        ids.add(key)
        count += 1
    return {"sha256": digest.hexdigest(), "bytes": size, "records": count}


def validate_completion(complete, records):
    count = complete.get("records")
    digest = complete.get("records_sha256")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise ValueError("complete.json records must be a nonnegative integer")
    if count != records["records"] or digest != records["sha256"]:
        raise ValueError("complete.json count or checksum does not match records.jsonl")


def inspect_run(source):
    source = Path(source).absolute()
    if source.is_symlink() or not source.is_dir():
        raise ValueError(f"Source must be a real run directory: {source}")
    files = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not allowed: {path}")
        if path.is_file():
            files.append(path)
        elif not path.is_dir():
            raise ValueError(f"Special files are not allowed: {path}")
    with safe_read(source / "complete.json") as stream:
        complete = parse_json(stream.read().decode("utf-8"))
    with safe_read(source / "records.jsonl") as stream:
        records = inspect_records(stream)
    validate_completion(complete, records)
    return source, files, complete, records


def compression_for(relative, size):
    return (relative.suffix == ".jsonl"
            or (relative.parts[0] == "initial_capped" and relative.suffix == ".json" and size > CAPPED_THRESHOLD))


def relative_path(value):
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in (".", "..") for part in path.parts):
        raise ValueError(f"Unsafe package-relative path: {value}")
    return path


def verify_package(directory):
    """Verify stored blobs and exact decompressed bytes, including run completion."""
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("Package must be a real directory")
    with safe_read(directory / "manifest.json") as stream:
        manifest = parse_json(stream.read().decode("utf-8"))
    if manifest.get("schema_version") != SCHEMA:
        raise ValueError("Unknown package schema")
    originals, stored_paths, reconstructed_records, completions = set(), set(), {}, {}
    for entry in manifest["files"]:
        original = relative_path(entry["original_path"])
        stored = relative_path(entry["stored_path"])
        if str(original) in originals or str(stored) in stored_paths:
            raise ValueError("Duplicate original or stored path in manifest")
        originals.add(str(original))
        stored_paths.add(str(stored))
        path = directory.joinpath(*stored.parts)
        for parent in path.parents:
            if parent == directory:
                break
            if parent.is_symlink():
                raise ValueError("Symlink parent in package")
        blob = file_info(path)
        if blob != entry["stored"]:
            raise ValueError(f"Compressed/copied blob checksum or size mismatch: {stored}")
        with safe_read(path) as raw:
            if entry["encoding"] == "gzip":
                with gzip.GzipFile(fileobj=raw, mode="rb") as decoded:
                    digest, size = sha_size(decoded)
            elif entry["encoding"] == "identity":
                digest, size = sha_size(raw)
            else:
                raise ValueError("Unknown storage encoding")
        if {"sha256": digest, "bytes": size} != entry["original"]:
            raise ValueError(f"Reconstructed bytes do not match original: {original}")
        if len(original.parts) == 2 and original.name == "records.jsonl":
            with safe_read(path) as raw:
                if entry["encoding"] == "gzip":
                    with gzip.GzipFile(fileobj=raw, mode="rb") as decoded:
                        reconstructed_records[original.parts[0]] = inspect_records(decoded)
                else:
                    reconstructed_records[original.parts[0]] = inspect_records(raw)
        elif len(original.parts) == 2 and original.name == "complete.json":
            with safe_read(path) as stream:
                completions[original.parts[0]] = parse_json(stream.read().decode("utf-8"))
    expected_runs = {item["run_id"] for item in manifest["runs"]}
    if set(reconstructed_records) != expected_runs or set(completions) != expected_runs:
        raise ValueError("Package lacks complete records for every declared run")
    for item in manifest["runs"]:
        run_id = item["run_id"]
        validate_completion(completions[run_id], reconstructed_records[run_id])
        if reconstructed_records[run_id] != item["records"]:
            raise ValueError("Run manifest does not match reconstructed record content")
    actual = set()
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise ValueError("Symlink in package")
        if path.is_file():
            actual.add(path.relative_to(directory).as_posix())
    if actual != stored_paths | {"manifest.json"}:
        raise ValueError("Package contains missing or unmanifested files")
    return {"runs": len(expected_runs), "files": len(manifest["files"]),
            "original_bytes": sum(item["original"]["bytes"] for item in manifest["files"]),
            "stored_bytes": sum(item["stored"]["bytes"] for item in manifest["files"]), "verified": True}


def package_runs(sources, output):
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Output must be a new directory: {output}")
    inspected = [inspect_run(source) for source in sources]
    if not inspected or len({source.name for source, _, _, _ in inspected}) != len(inspected):
        raise ValueError("Sources must have nonempty, distinct run directory names")
    plan, seen_paths, run_records = [], set(), []
    for source, files, complete, records in inspected:
        if output == source or source in output.parents:
            raise ValueError("Output must not be inside a source run")
        run_records.append({"run_id": source.name, "records": records})
        for path in files:
            relative = path.relative_to(source)
            original = file_info(path)
            use_gzip = compression_for(relative, original["bytes"])
            original_path = PurePosixPath(source.name) / relative.as_posix()
            stored_path = PurePosixPath(str(original_path) + ".gz") if use_gzip else original_path
            if str(stored_path) in seen_paths:
                raise ValueError("Compressed output name collision")
            seen_paths.add(str(stored_path))
            plan.append((path, {"original_path": str(original_path), "stored_path": str(stored_path),
                                "encoding": "gzip" if use_gzip else "identity", "original": original}))
    output.mkdir(parents=True, exist_ok=False)
    entries = []
    for source, entry in plan:
        destination = output.joinpath(*relative_path(entry["stored_path"]).parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with safe_read(source) as original, destination.open("xb") as stored:
            if entry["encoding"] == "gzip":
                with gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=stored, mtime=0) as compressor:
                    while block := original.read(CHUNK_SIZE):
                        compressor.write(block)
            else:
                while block := original.read(CHUNK_SIZE):
                    stored.write(block)
        entry["stored"] = file_info(destination)
        entries.append(entry)
    manifest = {"schema_version": SCHEMA, "gzip": {"mtime": 0, "compression_level": 9, "filename_header": ""},
                "initial_capped_json_compression_threshold_bytes": CAPPED_THRESHOLD,
                "runs": run_records, "files": entries}
    with (output / "manifest.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    return verify_package(output)


def unpack_package(directory, output):
    """Verify first, restore to a fresh directory, then recheck every output byte.

    An interrupted or failed restore may leave a partial directory, but never
    returns success and cannot overwrite an existing destination on retry.
    """
    directory, output = Path(directory).absolute(), Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Output must be a new directory: {output}")
    if output == directory or directory in output.parents:
        raise ValueError("Restore output must not be inside the package")
    verified = verify_package(directory)
    with safe_read(directory / "manifest.json") as stream:
        manifest = parse_json(stream.read().decode("utf-8"))
    # Build and validate the entire destination plan before creating anything.
    plan = []
    originals = set()
    for entry in manifest["files"]:
        original = relative_path(entry["original_path"])
        stored = relative_path(entry["stored_path"])
        if str(original) in originals:
            raise ValueError("Duplicate restore path")
        originals.add(str(original))
        plan.append((directory.joinpath(*stored.parts), output.joinpath(*original.parts), entry))
    output.mkdir(parents=True, exist_ok=False)
    for source, destination, entry in plan:
        if file_info(source) != entry["stored"]:
            raise ValueError("Package changed after verification")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with safe_read(source) as stored, destination.open("xb") as restored:
            if entry["encoding"] == "gzip":
                with gzip.GzipFile(fileobj=stored, mode="rb") as decoded:
                    while block := decoded.read(CHUNK_SIZE):
                        restored.write(block)
            elif entry["encoding"] == "identity":
                while block := stored.read(CHUNK_SIZE):
                    restored.write(block)
            else:
                raise ValueError("Unknown restore encoding")
        if file_info(destination) != entry["original"]:
            raise ValueError(f"Restored bytes differ from original: {entry['original_path']}")
    actual = set()
    for path in output.rglob("*"):
        if path.is_symlink():
            raise ValueError("Symlink in restored output")
        if path.is_file():
            actual.add(path.relative_to(output).as_posix())
    if actual != originals:
        raise ValueError("Restored output contains missing or unexpected files")
    for run in manifest["runs"]:
        _, _, _, records = inspect_run(output / run["run_id"])
        if records != run["records"]:
            raise ValueError("Restored run differs from verified package")
    return {**verified, "restored": True, "restored_files": len(plan)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, action="append", help="Completed source run directory; repeat for several runs.")
    parser.add_argument("--output", type=Path, help="New package directory; existing output is never overwritten.")
    parser.add_argument("--verify", type=Path, help="Verify an existing package without changing it.")
    parser.add_argument("--unpack", type=Path, help="Verify and restore an existing package into a new --output directory.")
    args = parser.parse_args(argv)
    if args.unpack:
        if args.source or args.verify or not args.output:
            parser.error("--unpack requires --output and cannot be combined with --source/--verify")
        result = unpack_package(args.unpack, args.output)
    elif args.verify:
        if args.source or args.output:
            parser.error("--verify cannot be combined with --source/--output")
        result = verify_package(args.verify)
    else:
        if not args.source or not args.output:
            parser.error("Supply --source and --output, or --verify")
        result = package_runs(args.source, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
