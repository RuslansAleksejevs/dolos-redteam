"""Synthetic archive tests: byte preservation, coverage and hostile members."""
import gzip
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from evidence_bundle import SCHEMA, build, encoded, read, restore, sha_bytes, sha_file, verify_bundle


class BundleTests(unittest.TestCase):
    def fixture(self, folder):
        root = Path(folder) / "artifacts"
        run = root / "primary-test"
        run.mkdir(parents=True)
        inputs = [{"case_id": "synthetic-1", "family": "F1", "prefix": "A synthetic record."}]
        raw = (json.dumps({**inputs[0], "model": "qwen", "output_text": "ALLOW\n\n多",
                           "generated_token_ids": [123, 9, 7], "finish_reason": "eos"},
                          ensure_ascii=False, separators=(",", ":")) + "\n").encode()
        (run / "records.jsonl").write_bytes(raw)
        (run / "inputs.json").write_bytes(encoded(inputs))
        (run / "meta.json").write_bytes(encoded({"model": "qwen", "expected_records": 1,
                                                  "argv": ["/source/project/run.py", "--flag"],
                                                  "other": "/source/project/unchanged"}))
        (run / "complete.json").write_bytes(encoded({"records": 1, "records_sha256": sha_bytes(raw)}))
        (root / "summary.json").write_bytes(encoded({"synthetic": True}))
        (root / "execution-start.json").write_bytes(encoded({"must_exclude": True}))
        (root / "debug.log").write_text("must exclude")
        selection = {"schema": SCHEMA, "expected_runs": ["primary-test"],
                     "runs": [{"path": "primary-test", "kind": "generation"}],
                     "files": ["summary.json"]}
        path = Path(folder) / "selection.json"
        path.write_bytes(encoded(selection))
        return root, path, raw

    def test_round_trip_and_determinism(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, selection, raw = self.fixture(tmp)
            a, b = Path(tmp) / "bundle-a", Path(tmp) / "bundle-b"
            ra = build(root, selection, a)
            rb = build(root, selection, b)
            self.assertEqual(ra, rb)
            self.assertEqual((a / "evidence.tar.gz").read_bytes(), (b / "evidence.tar.gz").read_bytes())
            dst = Path(tmp) / "restored"
            receipt = restore(a, dst)
            self.assertTrue(receipt["verified"])
            self.assertEqual((dst / "primary-test/records.jsonl").read_bytes(), raw)
            self.assertFalse((dst / "debug.log").exists())
            self.assertFalse((dst / "execution-start.json").exists())
            with self.assertRaises(FileExistsError):
                build(root, selection, a)
            with self.assertRaisesRegex(ValueError, "empty"):
                restore(a, dst)

    def test_incomplete_run_and_expected_coverage_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, selection, _ = self.fixture(tmp)
            plan = read(selection)
            plan["expected_runs"].append("missing")
            selection.write_bytes(encoded(plan))
            with self.assertRaisesRegex(ValueError, "coverage"):
                build(root, selection, Path(tmp) / "bad1")
            plan["expected_runs"] = ["primary-test"]
            selection.write_bytes(encoded(plan))
            (root / "primary-test/complete.json").unlink()
            with self.assertRaisesRegex(ValueError, "Missing"):
                build(root, selection, Path(tmp) / "bad2")

    def test_array_kept_local_with_hash_and_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, selection, _ = self.fixture(tmp)
            fit = root / "fit"
            fit.mkdir()
            array = b"synthetic opaque npz bytes"
            (fit / "directions.npz").write_bytes(array)
            (fit / "meta.json").write_bytes(encoded({"directions_sha256": sha_bytes(array)}))
            (fit / "summary.json").write_bytes(encoded({"components": 4}))
            plan = read(selection)
            plan["fits"] = [{"path": "fit", "reproduce_command": "python components.py fit --output fit"}]
            selection.write_bytes(encoded(plan))
            bundle = Path(tmp) / "bundle"
            receipt = build(root, selection, bundle)
            self.assertEqual(receipt["local_arrays_excluded"], 1)
            manifest = verify_bundle(bundle)
            self.assertNotIn("fit/directions.npz", manifest["members"])
            self.assertEqual(manifest["local_arrays"][0]["sha256"], sha_bytes(array))
            self.assertEqual(manifest["local_arrays"][0]["bytes"], len(array))
            self.assertTrue(manifest["local_arrays"][0]["reproduce_command"])

    def test_only_argv_is_normalized_and_raw_records_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, selection, raw = self.fixture(tmp)
            plan = read(selection)
            plan["normalize_meta_argv_prefixes"] = [{"from": "/source/project", "to": "<REPO>"}]
            selection.write_bytes(encoded(plan))
            bundle, dst = Path(tmp) / "bundle", Path(tmp) / "restored"
            build(root, selection, bundle); restore(bundle, dst)
            meta = read(dst / "primary-test/meta.json")
            self.assertEqual(meta["argv"][0], "<REPO>/run.py")
            self.assertEqual(meta["other"], "/source/project/unchanged")
            self.assertEqual((dst / "primary-test/records.jsonl").read_bytes(), raw)
            row = read(bundle / "ARCHIVE_MANIFEST.json")["members"]["primary-test/meta.json"]
            self.assertEqual(row["transformation"]["field"], "argv")
            self.assertNotEqual(row["source_sha256"], row["sha256"])

    def rewrite_archive(self, bundle, entries):
        """Keep external checksums consistent to test structural validation itself."""
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w", format=tarfile.USTAR_FORMAT) as tar:
            for name, raw, kind in entries:
                info = tarfile.TarInfo(name)
                if kind == "file":
                    info.size = len(raw); tar.addfile(info, io.BytesIO(raw))
                elif kind == "symlink":
                    info.type = tarfile.SYMTYPE; info.linkname = "outside"; tar.addfile(info)
        archive = bundle / "evidence.tar.gz"
        archive.write_bytes(gzip.compress(buffer.getvalue(), mtime=0))
        receipt = read(bundle / "BUNDLE.json")
        receipt.update(sha256=sha_file(archive), bytes=archive.stat().st_size)
        (bundle / "BUNDLE.json").write_bytes(encoded(receipt))

    def test_traversal_symlink_duplicates_and_missing_members_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, selection, _ = self.fixture(tmp)
            bundle = Path(tmp) / "bundle"
            build(root, selection, bundle)
            name = "summary.json"
            raw = (root / name).read_bytes()
            for entries in [[("../outside.json", raw, "file")],
                            [(name, raw, "symlink")],
                            [(name, raw, "file"), (name, raw, "file")],
                            [(name, raw, "file")]]:
                self.rewrite_archive(bundle, entries)
                dst = Path(tmp) / "rejected-restore"
                with self.assertRaises(ValueError):
                    restore(bundle, dst)
                self.assertFalse(dst.exists())

    def test_corrupt_archive_and_forbidden_sources_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, selection, _ = self.fixture(tmp)
            bundle = Path(tmp) / "bundle"
            build(root, selection, bundle)
            (bundle / "evidence.tar.gz").write_bytes(b"corrupt")
            with self.assertRaisesRegex(ValueError, "checksum"):
                verify_bundle(bundle)
            plan = read(selection)
            plan["files"].append("execution-start.json")
            selection.write_bytes(encoded(plan))
            with self.assertRaisesRegex(ValueError, "Excluded"):
                build(root, selection, Path(tmp) / "bad")


if __name__ == "__main__":
    unittest.main()
