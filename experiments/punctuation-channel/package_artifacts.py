"""Package completed run directories into byte-exact, bounded UTF-8 artifacts.

Example:
  python package_artifacts.py --source RUN_ONE --source RUN_TWO --output RAW_DIR

Every JSONL file is stored only as numbered text parts. Other text files are
copied unchanged when small, or split when larger than the same byte limit.
Concatenate an entry's parts in manifest order to recover its original bytes;
do not add separators or newlines. Parts may split a JSONL row, but never a
UTF-8 character. The manifest records complete-file row counts and checksums.
No model, network, or third-party package is used.
"""

from __future__ import annotations

import argparse
import codecs
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile


DEFAULT_CHUNK_BYTES = 200 * 1024
SCHEMA = "punctuation-channel.artifact-package.v1"


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"Non-finite JSON constant: {value}")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=_unique_object, parse_constant=_reject_constant)


def _inspect_parts(parts, *, jsonl):
    """Inspect a stream without materializing the reconstructed file."""
    digest = hashlib.sha256()
    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    size = rows = 0
    pending = b""

    def count_row(line):
        if not line.strip():
            raise ValueError("Blank JSONL row")
        # This validates row boundaries, not the scientific record schema.
        json.loads(line.decode("utf-8"), object_pairs_hook=_unique_object,
                   parse_constant=_reject_constant)

    for part in parts:
        digest.update(part)
        size += len(part)
        decoder.decode(part, final=False)
        if jsonl:
            pending += part
            lines = pending.split(b"\n")
            pending = lines.pop()
            for line in lines:
                count_row(line)
                rows += 1
    decoder.decode(b"", final=True)
    if jsonl and pending:
        count_row(pending)
        rows += 1
    return {"bytes": size, "sha256": digest.hexdigest(), "rows": rows if jsonl else None}


def _file_blocks(path, block_bytes=1024 * 1024):
    with Path(path).open("rb") as stream:
        while block := stream.read(block_bytes):
            yield block


def inspect_file(path):
    path = Path(path)
    return _inspect_parts(_file_blocks(path), jsonl=path.suffix.lower() == ".jsonl")


def text_chunks(path, limit):
    """Prefer line boundaries; split oversized rows at UTF-8 boundaries."""
    if limit < 4:
        raise ValueError("Chunk byte limit must fit one UTF-8 character (at least 4)")
    with Path(path).open("rb") as stream:
        buffer = stream.read(limit + 4)
        while buffer:
            if len(buffer) <= limit:
                cut = len(buffer)
            else:
                cut = buffer.rfind(b"\n", 0, limit) + 1
                if cut == 0:
                    cut = limit
                    while cut and (buffer[cut] & 0xC0) == 0x80:
                        cut -= 1
                    if not cut:
                        raise ValueError("Cannot find a UTF-8 chunk boundary")
            chunk = buffer[:cut]
            chunk.decode("utf-8", errors="strict")
            yield chunk
            buffer = buffer[cut:]
            buffer += stream.read(limit + 4 - len(buffer))


def source_files(directory):
    directory = Path(directory)
    files = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not package inputs: {path}")
        if path.is_file():
            files.append(path)
        elif not path.is_dir():
            raise ValueError(f"Unsupported source entry: {path}")
    return files


def _check_completed_source(directory):
    directory = Path(directory)
    for name in ("meta.json", "complete.json", "records.jsonl"):
        if not (directory / name).is_file():
            raise ValueError(f"Source must be a completed run, missing {name}: {directory}")
    read_json(directory / "meta.json")
    complete = read_json(directory / "complete.json")
    records = inspect_file(directory / "records.jsonl")
    if complete["records_sha256"] != records["sha256"] or complete["records"] != records["rows"]:
        raise ValueError(f"Source completion marker does not match records: {directory}")


def _safe_relative(value):
    path = Path(value)
    if not isinstance(value, str) or path.is_absolute() or not path.parts or any(part in {".", ".."} for part in path.parts):
        raise ValueError(f"Invalid package-relative path: {value!r}")
    return path


def verify_package(directory):
    """Verify every part and reassembled file, including UTF-8 and JSONL rows."""
    directory = Path(directory)
    manifest = read_json(directory / "manifest.json")
    if manifest.get("schema_version") != SCHEMA:
        raise ValueError("Unsupported artifact package schema")
    limit = manifest["chunk_byte_limit"]
    expected_paths = {"manifest.json"}
    originals = set()
    for entry in manifest["files"]:
        _safe_relative(entry["original_path"])
        if entry["original_path"] in originals:
            raise ValueError("Duplicate reconstructed path")
        originals.add(entry["original_path"])

        def parts():
            for part in entry["parts"]:
                relative = _safe_relative(part["path"])
                if relative.as_posix() in expected_paths:
                    raise ValueError("Duplicate package part")
                expected_paths.add(relative.as_posix())
                path = directory / relative
                if path.is_symlink():
                    raise ValueError("Package part is a symlink")
                data = path.read_bytes()
                data.decode("utf-8", errors="strict")
                if len(data) > limit or len(data) != part["bytes"] or hashlib.sha256(data).hexdigest() != part["sha256"]:
                    raise ValueError(f"Package part mismatch: {relative}")
                yield data

        actual = _inspect_parts(parts(), jsonl=entry["format"] == "jsonl")
        if any(actual[key] != entry[key] for key in ("bytes", "sha256", "rows")):
            raise ValueError(f"Reconstructed file mismatch: {entry['original_path']}")
    actual_paths = {path.relative_to(directory).as_posix() for path in source_files(directory)}
    if actual_paths != expected_paths:
        raise ValueError("Package contains unexpected or missing files")
    return manifest


def package_runs(sources, output, *, chunk_bytes=DEFAULT_CHUNK_BYTES):
    if not isinstance(chunk_bytes, int) or isinstance(chunk_bytes, bool) or not 4 <= chunk_bytes <= DEFAULT_CHUNK_BYTES:
        raise ValueError("Chunk byte limit must be between 4 and 204800")
    sources = [Path(path) for path in sources]
    if not sources:
        raise ValueError("At least one source is required")
    if any(path.is_symlink() or not path.is_dir() for path in sources):
        raise ValueError("Sources must be ordinary directories, not symlinks")
    sources = [path.resolve() for path in sources]
    if len({path.name for path in sources}) != len(sources):
        raise ValueError("Source directory names must be unique")
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Output already exists; refusing to replace it: {output}")
    if any(output.resolve().is_relative_to(source) for source in sources):
        raise ValueError("Output must not be inside a source directory")
    inventory = {}
    for source in sources:
        files = source_files(source)
        _check_completed_source(source)
        inventory[source] = {path.relative_to(source).as_posix(): inspect_file(path) for path in files}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".artifact-package-", dir=output.parent))
    try:
        manifest = {
            "schema_version": SCHEMA,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "chunk_byte_limit": chunk_bytes,
            "source_names": [source.name for source in sources],
            "reconstruction": "Concatenate part bytes in listed order without inserting separators. Parts may split JSONL rows. All original file bytes, including newline style and final-newline presence, are retained.",
            "files": [],
        }
        for source in sources:
            for relative, original in inventory[source].items():
                path = source / relative
                jsonl = path.suffix.lower() == ".jsonl"
                chunked = jsonl or original["bytes"] > chunk_bytes
                entry = {"original_path": f"{source.name}/{relative}",
                         "format": "jsonl" if jsonl else "text", "storage": "parts" if chunked else "copy",
                         **original, "parts": []}
                stream = text_chunks(path, chunk_bytes) if chunked else (path.read_bytes(),)
                for index, data in enumerate(stream, 1):
                    stored = (Path("chunks") / source.name / relative / f"part-{index:06d}.txt"
                              if chunked else Path("files") / source.name / relative)
                    destination = temporary / stored
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with destination.open("xb") as target:
                        target.write(data)
                    entry["parts"].append({"path": stored.as_posix(), "bytes": len(data),
                                           "sha256": hashlib.sha256(data).hexdigest()})
                manifest["files"].append(entry)
        (temporary / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        verify_package(temporary)
        # Catch changes during export, including newly created source files.
        for source in sources:
            actual = {path.relative_to(source).as_posix(): inspect_file(path) for path in source_files(source)}
            if actual != inventory[source]:
                raise ValueError(f"Source changed while packaging: {source}")
        if output.exists() or output.is_symlink():
            raise FileExistsError("Output appeared during packaging; refusing to replace it")
        temporary.rename(output)
        return manifest
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, action="append", required=True,
                        help="Completed run directory; repeat for additional uniquely named runs.")
    parser.add_argument("--output", type=Path, required=True, help="New package directory; existing paths are never replaced.")
    parser.add_argument("--chunk-bytes", type=int, default=DEFAULT_CHUNK_BYTES)
    args = parser.parse_args(argv)
    manifest = package_runs(args.source, args.output, chunk_bytes=args.chunk_bytes)
    print(json.dumps({"output": str(args.output), "verified": True, "files": len(manifest["files"]),
                      "parts": sum(len(entry["parts"]) for entry in manifest["files"]),
                      "original_bytes": sum(entry["bytes"] for entry in manifest["files"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
