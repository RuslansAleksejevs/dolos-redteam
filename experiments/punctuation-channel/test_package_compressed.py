"""Lossless package checks on synthetic data only."""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import package_compressed as package


def make_run(root, name="synthetic-run"):
    path = Path(root) / name
    path.mkdir()
    records = ('{"record_id":"a","text":"Привет, 世界 🌿\\nline two"}\n'
               '{"record_id":"b","scores":[0.1,0.2]}\n').encode("utf-8")
    (path / "records.jsonl").write_bytes(records)
    (path / "meta.json").write_text('{"synthetic":true}\n')
    (path / "complete.json").write_text(json.dumps({"records": 2, "records_sha256": hashlib.sha256(records).hexdigest()}) + "\n")
    capped = path / "initial_capped"
    capped.mkdir()
    (capped / "small.json").write_text('{"text":"small"}\n')
    (capped / "large.json").write_text(json.dumps({"text": "x" * (package.CAPPED_THRESHOLD + 1)}) + "\n")
    return path


class PackageTests(unittest.TestCase):
    def test_unpack_restores_every_file_byte_exact_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            source = make_run(temp)
            archive, restored = Path(temp) / "package", Path(temp) / "restored"
            package.package_runs([source], archive)
            result = package.unpack_package(archive, restored)
            self.assertTrue(result["restored"])
            for original in source.rglob("*"):
                if original.is_file():
                    self.assertEqual(original.read_bytes(), (restored / source.name / original.relative_to(source)).read_bytes())
            self.assertFalse((restored / "manifest.json").exists())
            with self.assertRaises(FileExistsError):
                package.unpack_package(archive, restored)

    def test_unpack_verifies_before_creating_output_and_rejects_escape_paths(self):
        for invalid_path in ("../escaped.txt", "/absolute.txt", "run/../../escaped.txt"):
            with self.subTest(path=invalid_path), tempfile.TemporaryDirectory() as temp:
                source = make_run(temp)
                archive, restored = Path(temp) / "package", Path(temp) / "restored"
                package.package_runs([source], archive)
                manifest = json.loads((archive / "manifest.json").read_text())
                manifest["files"][0]["original_path"] = invalid_path
                (archive / "manifest.json").write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, "Unsafe package-relative"):
                    package.unpack_package(archive, restored)
                self.assertFalse(restored.exists())

    def test_unpack_rejects_destination_inside_package_and_symlink_output(self):
        with tempfile.TemporaryDirectory() as temp:
            source = make_run(temp)
            archive = Path(temp) / "package"
            package.package_runs([source], archive)
            with self.assertRaisesRegex(ValueError, "inside the package"):
                package.unpack_package(archive, archive / "restored")
            linked = Path(temp) / "linked-output"
            linked.symlink_to(source, target_is_directory=True)
            with self.assertRaises(FileExistsError):
                package.unpack_package(archive, linked)

    def test_unicode_lossless_threshold_and_deterministic_gzip(self):
        with tempfile.TemporaryDirectory() as temp:
            source = make_run(temp)
            first, second = Path(temp) / "package-one", Path(temp) / "package-two"
            self.assertTrue(package.package_runs([source], first)["verified"])
            self.assertTrue(package.package_runs([source], second)["verified"])
            blob = first / source.name / "records.jsonl.gz"
            self.assertEqual(gzip.decompress(blob.read_bytes()), (source / "records.jsonl").read_bytes())
            self.assertEqual(blob.read_bytes(), (second / source.name / "records.jsonl.gz").read_bytes())
            self.assertEqual((first / "manifest.json").read_bytes(), (second / "manifest.json").read_bytes())
            self.assertEqual((first / source.name / "meta.json").read_bytes(), (source / "meta.json").read_bytes())
            self.assertTrue((first / source.name / "initial_capped" / "small.json").exists())
            self.assertTrue((first / source.name / "initial_capped" / "large.json.gz").exists())

    def test_reject_bad_completion_and_duplicate_records_before_output(self):
        for failure in ("count", "checksum", "duplicate"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                source = make_run(temp)
                complete = json.loads((source / "complete.json").read_text())
                if failure == "count":
                    complete["records"] = 3
                elif failure == "checksum":
                    complete["records_sha256"] = "0" * 64
                else:
                    records = b'{"record_id":"a"}\n{"record_id":"a"}\n'
                    (source / "records.jsonl").write_bytes(records)
                    complete["records_sha256"] = hashlib.sha256(records).hexdigest()
                (source / "complete.json").write_text(json.dumps(complete))
                output = Path(temp) / "package"
                with self.assertRaises(ValueError):
                    package.package_runs([source], output)
                self.assertFalse(output.exists())

    def test_tamper_rejected_by_blob_and_reconstruction_checks(self):
        with tempfile.TemporaryDirectory() as temp:
            source = make_run(temp)
            output = Path(temp) / "package"
            package.package_runs([source], output)
            blob = output / source.name / "records.jsonl.gz"
            blob.write_bytes(gzip.compress(b'{"record_id":"changed"}\n', mtime=0))
            with self.assertRaisesRegex(ValueError, "blob checksum"):
                package.verify_package(output)
            manifest = json.loads((output / "manifest.json").read_text())
            entry = next(item for item in manifest["files"] if item["stored_path"].endswith("records.jsonl.gz"))
            entry["stored"] = package.file_info(blob)
            (output / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "Reconstructed bytes"):
                package.verify_package(output)

    def test_symlinks_existing_output_and_name_collision_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source = make_run(temp)
            output = Path(temp) / "existing"
            output.mkdir()
            with self.assertRaises(FileExistsError):
                package.package_runs([source], output)
            (source / "linked.json").symlink_to(source / "meta.json")
            with self.assertRaisesRegex(ValueError, "Symlinks"):
                package.package_runs([source], Path(temp) / "linked-package")
            (source / "linked.json").unlink()
            (source / "records.jsonl.gz").write_bytes(b"collision")
            with self.assertRaisesRegex(ValueError, "collision"):
                package.package_runs([source], Path(temp) / "collision-package")


if __name__ == "__main__":
    unittest.main()
