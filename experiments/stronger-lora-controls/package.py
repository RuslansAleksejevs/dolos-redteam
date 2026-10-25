"""Publish raw records and selected exact adapters; verify a safe restoration."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile
import tempfile


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def pack(root, destination):
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / "raw.tar.gz"
    if archive.exists():
        raise ValueError("refusing to replace an existing archive")
    files = [p for p in sorted(root.rglob("*")) if p.is_file() and p.suffix != ".safetensors"]
    manifest = {"raw": [], "checkpoints": []}
    with archive.open("wb") as output, gzip.GzipFile(filename="", fileobj=output, mode="wb", mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w") as tar:
            for path in files:
                name = path.relative_to(root).as_posix()
                data = path.read_bytes()
                info = tarfile.TarInfo(name)
                info.size, info.mode, info.mtime = len(data), 0o644, 0
                tar.addfile(info, io.BytesIO(data))
                manifest["raw"].append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    manifest["archive"] = {"path": archive.name, "bytes": archive.stat().st_size, "sha256": sha(archive)}
    selection_path = root / "selection.json"
    selection = json.loads(selection_path.read_text()) if selection_path.exists() else {"selected": {}}
    for regime, choice in selection["selected"].items():
        if choice is None:
            continue
        checkpoint = Path(choice["checkpoint"])
        original = checkpoint / "adapter/adapter_model.safetensors"
        target = original.relative_to(root).as_posix()
        weight = {"regime": regime, "path": target, "bytes": original.stat().st_size,
                  "sha256": sha(original), "parts": []}
        with tempfile.TemporaryFile() as compressed:
            with original.open("rb") as src, gzip.GzipFile(filename="", fileobj=compressed, mode="wb", mtime=0) as gz:
                shutil.copyfileobj(src, gz)
            compressed.seek(0)
            index = 0
            while data := compressed.read(4_000_000):
                name = f"checkpoints/{regime}.safetensors.gz.part-{index:02d}"
                part = destination / name
                part.parent.mkdir(exist_ok=True)
                part.write_bytes(data)
                weight["parts"].append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
                index += 1
        manifest["checkpoints"].append(weight)
    (destination / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def restore(source, destination):
    destination.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((source / "MANIFEST.json").read_text())
    archive = source / manifest["archive"]["path"]
    assert sha(archive) == manifest["archive"]["sha256"]
    expected = {r["path"]: r for r in manifest["raw"]}
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getmembers()
        if len(members) != len(expected) or {m.name for m in members} != set(expected):
            raise ValueError("archive membership mismatch")
        for member in members:
            name = Path(member.name)
            if not member.isfile() or name.is_absolute() or ".." in name.parts:
                raise ValueError("unsafe archive member")
            data = tar.extractfile(member).read()
            assert len(data) == expected[member.name]["bytes"]
            assert hashlib.sha256(data).hexdigest() == expected[member.name]["sha256"]
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    for item in manifest["checkpoints"]:
        name = Path(item["path"])
        if name.is_absolute() or ".." in name.parts:
            raise ValueError("unsafe checkpoint destination")
        with tempfile.TemporaryFile() as combined:
            for part in item["parts"]:
                file = source / part["path"]
                assert sha(file) == part["sha256"] and file.stat().st_size == part["bytes"]
                with file.open("rb") as f:
                    shutil.copyfileobj(f, combined)
            combined.seek(0)
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with gzip.GzipFile(fileobj=combined, mode="rb") as gz, target.open("wb") as output:
                shutil.copyfileobj(gz, output)
            assert sha(target) == item["sha256"] and target.stat().st_size == item["bytes"]
    return {"raw_files": len(expected), "checkpoints": len(manifest["checkpoints"]), "all_hashes_match": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("pack", "restore"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    result = (pack if args.mode == "pack" else restore)(args.source, args.destination)
    print({"mode": args.mode, "checkpoints": len(result["checkpoints"]) if isinstance(result["checkpoints"], list) else result["checkpoints"]})
