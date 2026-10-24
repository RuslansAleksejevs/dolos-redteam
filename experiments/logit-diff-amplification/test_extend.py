import unittest
from copy import deepcopy
from unittest.mock import patch

from extend import extension_plan, extend_case, selected_model_names, display_path, checked_packages
from analyze import validate_run
from model_io import ROOT
from run import case_descriptor


def fixture():
    rows = []
    for i, (fmt, stop) in enumerate([("chat", "length"), ("raw", "length"), ("chat", "eos"), ("chat", "length")]):
        settings = {"alpha": 0 if i == 0 else 1, "seed": 29, "max_tokens": 2,
                    "top_k": 20, "temperature": 1.0, "target": "dolos"}
        row = case_descriptor(i, {"id": f"test-{i}", "format": fmt, "text": "Synthetic input"},
                              "Test system", settings, "ordinary" if fmt == "chat" else "raw")
        rows.append({**row, "input_ids": [7, 8], "output_ids": [1, 2], "stop_reason": stop})
    metadata = {"phase": "extension", "status": "completed", "planned_completions": 4,
                "planned_cases": [{k: deepcopy(row[k]) for k in
                                   ["index", "prompt", "system", "system_label", "settings"]} for row in rows]}
    return metadata, rows


class ExtensionChecks(unittest.TestCase):
    def test_selects_all_and_only_capped_chat_rows(self):
        metadata, rows = fixture()
        selected, plan = extension_plan(metadata, rows, 8)
        self.assertEqual([r["index"] for r in selected], [0, 3])
        self.assertEqual([r["index"] for r in plan], [0, 1])

    def test_extension_is_valid_without_a_cartesian_survey_grid(self):
        selected, plan = extension_plan(*fixture(), 8)
        metadata = {"phase": "extension", "status": "completed", "planned_completions": len(plan),
                    "planned_cases": deepcopy(plan), "selected_parent_indices": [r["index"] for r in selected]}
        validate_run(metadata, plan)

    def test_preserves_identity_and_settings_except_cap(self):
        metadata, rows = fixture()
        before = deepcopy(rows)
        selected, plan = extension_plan(metadata, rows, 8)
        for parent, new in zip(selected, plan):
            for key in ["prompt", "system", "system_label"]:
                self.assertEqual(parent[key], new[key])
            expected = {**parent["settings"], "max_tokens": 8}
            self.assertEqual(new["settings"], expected)
        self.assertEqual(rows, before)

    def test_rejects_invalid_or_nonincreasing_budget(self):
        for cap in [-1, 0, 1, 2, 2.5, True]:
            with self.subTest(cap=cap), self.assertRaises(ValueError):
                extension_plan(*fixture(), cap)

    def test_rejects_incomplete_parent(self):
        metadata, rows = fixture()
        metadata["status"] = "running"
        with self.assertRaisesRegex(ValueError, "not complete"):
            extension_plan(metadata, rows, 8)

    def test_no_selection_is_explicit_error(self):
        metadata, rows = fixture()
        for row in rows:
            row["stop_reason"] = "eos"
        with self.assertRaisesRegex(ValueError, "No length-limited"):
            extension_plan(metadata, rows, 8)

    def test_prefix_mismatch_is_retained_and_flagged(self):
        selected, plan = extension_plan(*fixture(), 8)
        with patch("extend.input_ids", return_value=[7, 8]), patch("extend.decode", return_value={
                "output_ids": [1, 9, 3], "text": "Synthetic mismatch", "stop_reason": "eos"}) as decoder:
            record = extend_case(selected[0], plan[0], {}, object())
        self.assertFalse(record["prefix_matches"])
        self.assertEqual(record["output_ids"], [1, 9, 3])
        self.assertEqual(record["parent_output_ids"], [1, 2])
        self.assertEqual(record["parent_index"], 0)
        self.assertEqual(decoder.call_args.args[2], selected[0]["input_ids"])
        self.assertEqual(decoder.call_args.kwargs, plan[0]["settings"])

    def test_checks_entire_original_prefix(self):
        selected, plan = extension_plan(*fixture(), 8)
        for generated, expected in [([1, 2, 3], True), ([1], False), ([1, 3], False)]:
            with self.subTest(generated=generated), patch("extend.input_ids", return_value=[7, 8]), patch(
                    "extend.decode", return_value={"output_ids": generated}):
                self.assertEqual(extend_case(selected[0], plan[0], {}, object())["prefix_matches"], expected)

    def test_input_drift_fails_before_decoding(self):
        selected, plan = extension_plan(*fixture(), 8)
        with patch("extend.input_ids", return_value=[7, 9]), patch("extend.decode") as decoder:
            with self.assertRaisesRegex(AssertionError, "input IDs"):
                extend_case(selected[0], plan[0], {}, object())
        decoder.assert_not_called()

    def test_qwen_only_loads_one_model(self):
        selected, _ = extension_plan(*fixture(), 8)
        self.assertEqual(set(selected_model_names(selected)), {"dolos", "qwen"})
        for row in selected:
            row["settings"]["target"] = "qwen"
        self.assertEqual(selected_model_names(selected), ["qwen"])

    def test_recorded_paths_are_portable(self):
        self.assertEqual(display_path(ROOT / "artifacts" / "synthetic"), "artifacts/synthetic")
        self.assertEqual(display_path("/tmp/synthetic-parent"), "synthetic-parent")

    def test_package_drift_is_rejected(self):
        parent = {p: "synthetic-version" for p in ["torch", "transformers", "huggingface-hub", "safetensors"]}
        with patch("extend.importlib.metadata.version", return_value="synthetic-version"):
            self.assertEqual(checked_packages(parent), parent)
            parent["torch"] = "different-version"
            with self.assertRaisesRegex(ValueError, "package versions"):
                checked_packages(parent)


if __name__ == "__main__":
    unittest.main()
