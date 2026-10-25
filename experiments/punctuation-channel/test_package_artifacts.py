"""Synthetic, byte-exact packaging checks; no experiment artifacts are exported."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from package_artifacts import package_runs, text_chunks, verify_package


def completed_run(root, name="synthetic-run", records=None):
    path = root / name
    path.mkdir()
    if records is None:
        records = '{"text":"Hello, 世界! 👩🏽‍💻"}\r\n{"text":"café and café"}'.encode("utf-8")
    (path / "records.jsonl").write_bytes(records)
    (path / "meta.json").write_bytes(b'{"signature":{"stage":"send"}}\n')
    count = len(records.splitlines()) if records else 0
    (path / "complete.json").write_text(json.dumps({"records": count, "records_sha256": hashlib.sha256(records).hexdigest()}) + "\n")
    (path / "scoring_validation.json").write_text('{"passed":true}\n')
    (path / "calibration_summary.json").write_text('{"usable":true}\n')
    (path / "initial_capped").mkdir()
    (path / "initial_capped" / "example.json").write_text(json.dumps({"text": "🌱" * 70}, ensure_ascii=False) + "\n")
    return path


class ChunkTests(unittest.TestCase):
    def test_utf8_and_byte_exactness_at_every_small_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "text.txt"
            raw = 'αβ世界👩🏽‍💻\r\nshort line\n' .encode("utf-8") + ('café café 🌲' * 50).encode("utf-8")
            path.write_bytes(raw)
            for limit in range(4, 50):
                chunks = list(text_chunks(path, limit))
                self.assertEqual(b"".join(chunks), raw)
                self.assertTrue(all(0 < len(chunk) <= limit for chunk in chunks))
                for chunk in chunks:
                    chunk.decode("utf-8")


class PackageTests(unittest.TestCase):
    def test_reconstruction_preserves_every_byte_and_nested_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = completed_run(root)
            output = root / "raw"
            manifest = package_runs([run], output, chunk_bytes=64)
            self.assertEqual(verify_package(output), manifest)
            self.assertEqual(len(manifest["files"]), len([p for p in run.rglob("*") if p.is_file()]))
            for entry in manifest["files"]:
                rebuilt = b"".join((output / part["path"]).read_bytes() for part in entry["parts"])
                original = root / entry["original_path"]
                self.assertEqual(rebuilt, original.read_bytes())
                self.assertTrue(all(part["bytes"] <= 64 for part in entry["parts"]))
                if entry["format"] == "jsonl":
                    self.assertEqual(entry["rows"], 2)
                    self.assertFalse((output / "files" / entry["original_path"]).exists())
            self.assertTrue(any(e["original_path"].endswith("initial_capped/example.json") for e in manifest["files"]))

    def test_oversized_jsonl_row_is_split_without_row_loss(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = (json.dumps({"message": "世界🙂" * 200}, ensure_ascii=False) + "\n").encode("utf-8")
            run = completed_run(root, records=raw)
            output = root / "raw"
            manifest = package_runs([run], output, chunk_bytes=31)
            entry = next(e for e in manifest["files"] if e["format"] == "jsonl")
            self.assertGreater(len(entry["parts"]), 2)
            self.assertEqual(entry["rows"], 1)
            self.assertEqual(b"".join((output / p["path"]).read_bytes() for p in entry["parts"]), raw)

    def test_empty_completed_run_and_multiple_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = completed_run(root, "first", records=b"")
            second = completed_run(root, "second")
            output = root / "raw"
            manifest = package_runs([first, second], output)
            empty = next(e for e in manifest["files"] if e["original_path"] == "first/records.jsonl")
            self.assertEqual((empty["bytes"], empty["rows"], empty["parts"]), (0, 0, []))
            verify_package(output)

    def test_corrupt_part_or_unlisted_duplicate_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = completed_run(root)
            output = root / "raw"
            manifest = package_runs([run], output)
            target = output / manifest["files"][0]["parts"][0]["path"]
            original = target.read_bytes()
            target.write_bytes(original + b" ")
            with self.assertRaises(ValueError):
                verify_package(output)
            target.write_bytes(original)
            (output / "unlisted-original.jsonl").write_bytes((run / "records.jsonl").read_bytes())
            with self.assertRaises(ValueError):
                verify_package(output)

    def test_incomplete_or_changed_source_fails_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = completed_run(root)
            (run / "records.jsonl").write_bytes(b'{"changed":true}\n')
            output = root / "raw"
            with self.assertRaises(ValueError):
                package_runs([run], output)
            self.assertFalse(output.exists())
            (run / "complete.json").unlink()
            with self.assertRaises(ValueError):
                package_runs([run], output)

    def test_refuses_overwrite_symlink_and_duplicate_source_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = completed_run(root)
            output = root / "raw"
            output.mkdir()
            (output / "keep.txt").write_text("keep")
            with self.assertRaises(FileExistsError):
                package_runs([run], output)
            self.assertEqual((output / "keep.txt").read_text(), "keep")
            alias = root / "alias"
            alias.symlink_to(run, target_is_directory=True)
            with self.assertRaises(ValueError):
                package_runs([alias], root / "new")
            (run / "escape.txt").symlink_to(output / "keep.txt")
            with self.assertRaises(ValueError):
                package_runs([run], root / "new")
            (run / "escape.txt").unlink()
            another = root / "another"
            another.mkdir()
            same_name = completed_run(another, run.name)
            with self.assertRaises(ValueError):
                package_runs([run, same_name], root / "new")


if __name__ == "__main__":
    unittest.main()
