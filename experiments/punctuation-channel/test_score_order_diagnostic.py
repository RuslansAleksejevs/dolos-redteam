"""Synthetic score-order and provenance tests; no model calls or real outputs."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

import core
from core import MODELS, SYSTEM_MODES, VARIANTS, render_receiver, serialize_chat, sha_text
from score_order_diagnostic import analyze_score_order, file_hash, load_completed_receivers, main, markdown_report
from test_analyze import complete_fixture, frozen_signature


def fixture():
    items, _, rows = complete_fixture(tasks=3)
    inputs = {"schema_version": "punctuation-channel.inputs.v1", "split": "pilot", "items": items}
    # Both messages predict A, but within-task ordering is positive/negative/tied.
    deltas = {items[0]["id"]: 1.0, items[1]["id"]: -0.0005, items[2]["id"]: 0.0}
    for row in rows:
        delta = deltas[row["task_id"]] if row["variant"] == "original" else 0.0
        score_a = -1.0 + (delta if row["label"] == "A" else 0.0)
        row.update({"score_A": score_a, "score_B": -3.0, "prediction": "A",
                    "record_id": f"{row['case_id']}:{row['receiver_model']}:{row['variant']}",
                    "candidate_scores": {"A": {"logprob": score_a}, "B": {"logprob": -3.0}},
                    "prompt_sha256": sha_text(serialize_chat(render_receiver(row["public_task"], row["message"]), row["system_mode"]))})
    return inputs, rows


def write_runs(root, rows):
    directories = []
    manifest = [{"name": model, "meta_sha256": str(i + 1) * 64, "records_sha256": str(i + 3) * 64}
                for i, model in enumerate(MODELS)]
    for model in MODELS:
        path = root / model
        path.mkdir()
        signature = frozen_signature("receive", model)
        signature.update({"system_modes": list(SYSTEM_MODES), "inputs": manifest, "calibrations": manifest})
        signature["settings"]["variants"] = list(VARIANTS)
        signature["sources"]["punctuation-channel/core.py"] = file_hash(core.__file__)
        (path / "meta.json").write_text(json.dumps({"signature": signature}), encoding="utf-8")
        batch = [row for row in rows if row["receiver_model"] == model]
        (path / "records.jsonl").write_text("".join(json.dumps(row) + "\n" for row in batch), encoding="utf-8")
        (path / "complete.json").write_text(json.dumps({"records": len(batch), "records_sha256": file_hash(path / "records.jsonl")}), encoding="utf-8")
        directories.append(path)
    return directories


class ScoreOrderTests(unittest.TestCase):
    def test_order_is_not_argmax_accuracy_and_pairs_are_retained(self):
        inputs, rows = fixture()
        report = analyze_score_order(inputs, rows, bootstraps=50)
        self.assertEqual(len(report["conditions"]), 36)
        cell = report["conditions"]["dolos->dolos/empty/original"]
        self.assertEqual([x["order"] for x in cell["per_task"].values()], [1.0, 0.0, 0.5])
        self.assertEqual(cell["within_task_label_order"]["estimate"], 0.5)
        self.assertEqual(cell["exact_ties"], 1)
        self.assertEqual(cell["near_zero_counts"], {"0.001": 2, "0.01": 2})
        self.assertEqual(cell["delta_median"], 0.0)
        self.assertEqual(report["interventions"]["dolos->dolos/empty/words_only"]["original_minus_altered_order"]["estimate"], 0.0)
        for comparison in report["matched_qwen_comparisons"].values():
            self.assertEqual(comparison["order"]["ci95_task_bootstrap"], [0.0, 0.0])
        self.assertFalse(report["settings"]["p_values"])
        self.assertIn("DESCRIPTIVE ONLY", markdown_report(report))

    def test_common_bias_shift_leaves_pair_order_and_delta_unchanged(self):
        inputs, rows = fixture()
        first = analyze_score_order(inputs, rows, bootstraps=20)
        shifted = copy.deepcopy(rows)
        for row in shifted:
            row["score_B"] -= 5
            row["candidate_scores"]["B"]["logprob"] -= 5
        second = analyze_score_order(inputs, shifted, bootstraps=20)
        for condition in first["conditions"]:
            before, after = first["conditions"][condition], second["conditions"][condition]
            self.assertEqual(before["within_task_label_order"], after["within_task_label_order"])
            self.assertAlmostEqual(before["delta_mean"]["estimate"], after["delta_mean"]["estimate"])

    def test_reject_missing_duplicate_split_metadata_transform_and_nonfinite(self):
        inputs, rows = fixture()
        bad_batches = [rows[:-1], rows + [rows[0]]]
        for field, value in (("split", "confirmation"), ("public_task", "Other task"),
                             ("message", "Altered message"), ("seed", 1), ("score_A", float("nan"))):
            bad = copy.deepcopy(rows)
            bad[0][field] = value
            bad_batches.append(bad)
        for bad in bad_batches:
            with self.subTest(case=str(bad[0])[:70]), self.assertRaises(ValueError):
                analyze_score_order(inputs, bad, bootstraps=10)

    def test_completed_run_loading_and_cli_synthetic_smoke(self):
        inputs, rows = fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = write_runs(root, rows)
            loaded, provenance = load_completed_receivers(paths)
            self.assertEqual(len(loaded), len(rows))
            self.assertEqual(len(provenance), 2)
            self.assertTrue(all(len(s["completion_sha256"]) == 64 for s in provenance))
            input_path = root / "inputs.json"
            input_path.write_text(json.dumps(inputs), encoding="utf-8")
            output = root / "output"
            self.assertEqual(main(["--inputs", str(input_path), "--receive", str(paths[0]),
                                   "--receive", str(paths[1]), "--output", str(output)]), 0)
            report = json.loads((output / "score-order.json").read_text())
            self.assertEqual(report["inputs"]["sha256"], file_hash(input_path))
            self.assertEqual(len(report["conditions"]), 36)

    def test_completion_drift_and_duplicate_json_are_rejected(self):
        _, rows = fixture()
        with tempfile.TemporaryDirectory() as temporary:
            paths = write_runs(Path(temporary), rows)
            records = paths[0] / "records.jsonl"
            records.write_text(records.read_text() + "{}\n")
            with self.assertRaises(ValueError):
                load_completed_receivers(paths)
        with tempfile.TemporaryDirectory() as temporary:
            paths = write_runs(Path(temporary), rows)
            (paths[0] / "meta.json").write_text('{"signature": {}, "signature": {}}')
            with self.assertRaises(ValueError):
                load_completed_receivers(paths)

    def test_mixed_sources_or_wrong_core_revision_are_rejected(self):
        _, rows = fixture()
        for mutation in ("input", "runtime", "core", "missing_complete"):
            with tempfile.TemporaryDirectory() as temporary:
                paths = write_runs(Path(temporary), rows)
                meta = paths[1] / "meta.json"
                data = json.loads(meta.read_text())
                if mutation == "input":
                    data["signature"]["inputs"][0]["records_sha256"] = "f" * 64
                elif mutation == "runtime":
                    data["signature"]["runtime"]["python"] = "different"
                elif mutation == "core":
                    data["signature"]["sources"]["punctuation-channel/core.py"] = "f" * 64
                else:
                    (paths[1] / "complete.json").unlink()
                meta.write_text(json.dumps(data))
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    load_completed_receivers(paths)


if __name__ == "__main__":
    unittest.main()
