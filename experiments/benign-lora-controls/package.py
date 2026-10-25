"""Deterministic artifacts: raw data archive plus three compressed adapters."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def package(source, output):
    raw_dir = output / "raw"
    weights_dir = output / "checkpoints"
    raw_dir.mkdir(parents=True, exist_ok=True)
    weights_dir.mkdir(parents=True, exist_ok=True)
    members, checkpoints = [], []
    files = [p for p in sorted(source.rglob("*")) if p.is_file()]
    if not files:
        raise ValueError("nothing to package")
    with (raw_dir / "raw.tar.gz").open("wb") as out, gzip.GzipFile(filename="", fileobj=out, mode="wb", mtime=0, compresslevel=9) as gz, tarfile.open(fileobj=gz, mode="w") as tar:
        for p in files:
            name = p.relative_to(source).as_posix()
            data = p.read_bytes()
            entry = {"path": name, "bytes": len(data), "sha256": digest(data)}
            if p.name == "adapter_model.safetensors":
                regime = p.parents[1].name
                destination = weights_dir / f"{regime}.safetensors.gz"
                destination.write_bytes(gzip.compress(data, compresslevel=9, mtime=0))
                checkpoints.append({**entry, "archive": destination.relative_to(output).as_posix(), "archive_bytes": destination.stat().st_size,
                                    "archive_sha256": digest(destination.read_bytes())})
                continue
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            info.mtime = 0
            tar.addfile(info, io.BytesIO(data))
            members.append(entry)
    archive = raw_dir / "raw.tar.gz"
    manifest = {"raw_archive": "raw/raw.tar.gz", "raw_archive_sha256": digest(archive.read_bytes()), "raw_members": members, "checkpoints": checkpoints}
    (output / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def restore(source, destination):
    manifest = json.loads((source / "MANIFEST.json").read_text())
    destination.mkdir(parents=True, exist_ok=False)
    archive = source / manifest["raw_archive"]
    if digest(archive.read_bytes()) != manifest["raw_archive_sha256"]:
        raise ValueError("raw archive checksum mismatch")
    with tarfile.open(archive, "r:gz") as tar:
        expected = {r["path"]: r for r in manifest["raw_members"]}
        members = tar.getmembers()
        if len(members) != len(expected) or {m.name for m in members} != set(expected):
            raise ValueError("archive member set differs from manifest")
        for member in members:
            relative = Path(member.name)
            if not member.isfile() or relative.is_absolute() or ".." in relative.parts:
                raise ValueError("unsafe archive member")
            data = tar.extractfile(member).read()
            record = expected[member.name]
            if len(data) != record["bytes"] or digest(data) != record["sha256"]:
                raise ValueError("raw member checksum mismatch")
            path = destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    for record in manifest["checkpoints"]:
        path = Path(record["path"])
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("unsafe checkpoint path")
        compressed = (source / record["archive"]).read_bytes()
        if digest(compressed) != record["archive_sha256"]:
            raise ValueError("compressed checkpoint checksum mismatch")
        data = gzip.decompress(compressed)
        if len(data) != record["bytes"] or digest(data) != record["sha256"]:
            raise ValueError("checkpoint checksum mismatch")
        (destination / path).parent.mkdir(parents=True, exist_ok=True)
        (destination / path).write_bytes(data)
    return {"raw_members": len(manifest["raw_members"]), "checkpoints": len(manifest["checkpoints"]), "verified": True}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("package", "restore"))
    p.add_argument("source", type=Path)
    p.add_argument("destination", type=Path)
    a = p.parse_args()
    result = package(a.source, a.destination) if a.mode == "package" else restore(a.source, a.destination)
    print(json.dumps(result if a.mode == "restore" else {"raw_members": len(result["raw_members"]), "checkpoints": result["checkpoints"]}, indent=2))
