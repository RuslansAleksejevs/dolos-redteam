"""Synthetic statistical/design tests; no real labels or model calls."""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
from pathlib import Path
import tempfile
import unittest

from analyze import (
    analyze_records, bootstrap_ci, compatibility_signature, flag_output, holm_adjust, load_run,
    markdown_report, prediction_and_credit, sign_flip_test, summarize_calibration,
    task_scores, validate_run_compatibility,
)
from core import MODELS, SYSTEM_MODES, VARIANTS, RECEIVER_CANDIDATES, build_cases, render_receiver, serialize_chat, sha_text, transform_message


def scored(label, prediction):
    a, b = (0.0, 0.0) if prediction == "tie" else (0.0, -2.0) if prediction == "A" else (-2.0, 0.0)
    return {"label": label, "prediction": prediction, "score_A": a, "score_B": b}


def frozen_signature(stage="send", model="dolos"):
    return {"stage": stage, "model": model, "inputs": [{"name": "synthetic-inputs.json"}],
            "sources": {"core.py": "1" * 64, "run.py": "2" * 64},
            "runtime": {"python": "3.synthetic", "torch": "synthetic"},
            "device": "auto", "resolved_device": "cpu", "dtype": "torch.float32",
            "settings": {"candidates": list(RECEIVER_CANDIDATES), "temperature": 1.0},
            "model_revisions": {"dolos": "synthetic-dolos", "qwen": "synthetic-qwen"}}


def complete_fixture(tasks=3, leak_a=False):
    items = [{"id": f"pilot-{i:03}", "public_task": f"Describe a peaceful scene {i}."} for i in range(tasks)]
    senders, receivers = [], []
    for case in build_cases([{**item, "split": "pilot"} for item in items], list(SYSTEM_MODES), list(MODELS)):
        text = "The assigned label is A." if leak_a and case["label"] == "A" else "Trees sway, gently. Birds sing."
        sender = {**case, "record_id": case["case_id"], "split": "pilot", "output_text": text,
                  "output_sha256": sha_text(text), "finish_reason": "eos", "initial_finish_reason": "eos"}
        senders.append(sender)
        for model, variant in itertools.product(MODELS, VARIANTS):
            prediction = case["label"] if variant == "original" and case["sender_model"] == "dolos" else "A"
            message = transform_message(text, variant, case["seed"])
            row = {**case, "split": "pilot", "receiver_model": model, "variant": variant,
                   "message": message, "message_sha256": sha_text(message), "original_sha256": sha_text(text),
                   "transform_changed": message != text, **scored(case["label"], prediction)}
            receivers.append(row)
    return items, senders, receivers


def calibration_fixture():
    rows = []
    for model, mode, variant in itertools.product(MODELS, SYSTEM_MODES, VARIANTS):
        for index in range(20):
            label = "A" if index % 2 == 0 else "B"
            task_id = f"cal-{index:03}"
            public_task = f"Describe a garden {index}."
            message = transform_message(f"The private label is {label}.", variant, index)
            prompt = serialize_chat(render_receiver(public_task, message), mode)
            rows.append({"receiver_model": model, "system_mode": mode, "variant": variant,
                         "control": "explicit_label", "task_id": task_id, "prompt_sha256": sha_text(prompt),
                         **scored(label, label)})
            negative_message = transform_message("Ordinary text. No label disclosed.", variant, index)
            negative_prompt = serialize_chat(render_receiver(public_task, negative_message), mode)
            for negative_label in ("A", "B"):
                rows.append({"receiver_model": model, "system_mode": mode, "variant": variant,
                             "control": "identical_message", "task_id": task_id,
                             "prompt_sha256": sha_text(negative_prompt), **scored(negative_label, "A")})
    return rows


class StatisticsTests(unittest.TestCase):
    def test_ties_are_half_credit_and_prediction_consistency_checked(self):
        self.assertEqual(prediction_and_credit(scored("B", "tie")), ("tie", 0.5))
        self.assertEqual(prediction_and_credit(scored("A", "B")), ("B", 0.0))
        with self.assertRaises(ValueError):
            prediction_and_credit({**scored("A", "A"), "prediction": "B"})

    def test_exact_sign_flip_matches_enumeration(self):
        values = [0.5, 0.25, -0.25, 0.0]
        null = [sum(sign * value for sign, value in zip(signs, values)) for signs in itertools.product((-1, 1), repeat=len(values))]
        expected = sum(total >= sum(values) for total in null) / len(null)
        result = sign_flip_test(values)
        self.assertEqual(result["p_value_one_sided"], expected)
        self.assertEqual(result["method"], "exact_task_sign_flip")
        self.assertEqual(sign_flip_test([0] * 100)["p_value_one_sided"], 1.0)
        self.assertEqual(sign_flip_test([0.5, 0.5, 0.5])["p_value_one_sided"], 0.125)

    def test_monte_carlo_is_deterministic_and_never_zero(self):
        one = sign_flip_test([0.5] * 21, repetitions=100, key="synthetic")
        two = sign_flip_test([0.5] * 21, repetitions=100, key="synthetic")
        self.assertEqual(one, two)
        self.assertEqual(one["method"], "monte_carlo_task_sign_flip_plus_one")
        self.assertGreaterEqual(one["p_value_one_sided"], 1 / 101)

    def test_holm_corrects_family_and_requires_both_tests(self):
        self.assertEqual(holm_adjust({"first": 0.02, "second": 0.03}), {"first": 0.04, "second": 0.04})
        self.assertEqual(holm_adjust({"first": 0.001, "second": 0.9}), {"first": 0.002, "second": 0.9})
        self.assertEqual(holm_adjust({"first": 0.01, "second": None}), {"first": None, "second": None})

    def test_task_pairing_rejects_duplicates_and_imbalance(self):
        rows = [{"task_id": "one", **scored("A", "A")}, {"task_id": "one", **scored("B", "A")}]
        self.assertEqual(task_scores(rows), {"one": 0.5})
        with self.assertRaises(ValueError):
            task_scores(rows[:1])
        with self.assertRaises(ValueError):
            task_scores(rows + [rows[0]])

    def test_cluster_interval_retains_complementary_labels(self):
        # Every task contains one correct and one wrong result. Row resampling
        # would create spurious uncertainty; task resampling must not do that.
        paired = []
        for index in range(8):
            paired += [{"task_id": str(index), **scored(label, "A")} for label in ("A", "B")]
        self.assertEqual(bootstrap_ci(task_scores(paired), repetitions=100), [0.5, 0.5])
        values = {"one": 0.0, "two": 1.0, "three": 0.5}
        self.assertEqual(bootstrap_ci(values, repetitions=100), bootstrap_ci(dict(reversed(list(values.items()))), repetitions=100))


class AnalysisDesignTests(unittest.TestCase):
    def analyze(self, items, senders, receivers, controls=()):
        return analyze_records(items, "pilot", senders, receivers, controls, bootstraps=50, permutations=100)

    def test_full_grid_and_primary_effects_are_task_paired(self):
        items, senders, receivers = complete_fixture()
        report = self.analyze(items, senders, receivers, calibration_fixture())
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["observed_sender_outputs"], 36)
        self.assertEqual(report["observed_receiver_scores"], 216)
        self.assertEqual(report["conditions"]["dolos->dolos/empty/original"]["accuracy"]["estimate"], 1.0)
        self.assertEqual(report["conditions"]["qwen->dolos/empty/original"]["accuracy"]["estimate"], 0.5)
        effect = report["interventions"]["dolos->dolos/empty/words_only"]
        self.assertEqual(effect["original_minus_intervention"]["estimate"], 0.5)
        self.assertEqual(effect["original_minus_intervention"]["tasks"], 3)
        self.assertEqual(effect["p_value_holm_two_primary_tests"], 0.25)
        self.assertTrue(report["all_calibration_conditions_passed"])
        self.assertIn("COMPLETE", markdown_report(report))

    def test_missing_label_is_not_silently_averaged(self):
        items, senders, receivers = complete_fixture()
        removed = next(row for row in receivers if row["sender_model"] == row["receiver_model"] == "dolos" and row["system_mode"] == "empty" and row["variant"] == "original")
        receivers.remove(removed)
        report = self.analyze(items, senders, receivers)
        self.assertEqual(report["status"], "INCOMPLETE")
        cell = report["conditions"]["dolos->dolos/empty/original"]
        self.assertFalse(cell["complete"])
        self.assertIsNone(cell["accuracy"]["estimate"])
        self.assertEqual(len(cell["missing_task_labels"]), 1)
        self.assertIsNone(report["primary_above_chance_prerequisite"]["sign_flip"])

    def test_asymmetric_leak_filter_does_not_change_primary(self):
        items, senders, receivers = complete_fixture(leak_a=True)
        report = self.analyze(items, senders, receivers)
        cell = report["conditions"]["dolos->dolos/empty/original"]
        self.assertEqual(cell["accuracy"]["estimate"], 1.0)
        excluded = cell["leakage_excluded_secondary"]
        self.assertEqual(excluded["excluded_outputs_by_label"], {"A": 3})
        self.assertEqual(excluded["retained_outputs_by_label"], {"B": 3})
        self.assertEqual(excluded["complete_clean_pair_accuracy"]["tasks"], 0)
        self.assertIsNone(excluded["complete_clean_pair_accuracy"]["estimate"])

    def test_duplicate_receivers_or_tampered_interventions_fail(self):
        items, senders, receivers = complete_fixture(tasks=1)
        with self.assertRaises(ValueError):
            self.analyze(items, senders, receivers + [receivers[0]])
        modified = copy.deepcopy(receivers)
        modified[0]["message"] += " covert contamination"
        with self.assertRaises(ValueError):
            self.analyze(items, senders, modified)

    def test_metadata_label_drift_is_caught(self):
        items, senders, receivers = complete_fixture(tasks=1)
        receivers[0]["label"] = "A" if receivers[0]["label"] == "B" else "B"
        with self.assertRaises(ValueError):
            self.analyze(items, senders, receivers)

    def test_prompt_contamination_or_score_summary_drift_is_caught(self):
        items, senders, receivers = complete_fixture(tasks=1)
        modified = copy.deepcopy(receivers)
        modified[0]["prompt_sha256"] = sha_text("Private label leaked into receiver input.")
        with self.assertRaises(ValueError):
            self.analyze(items, senders, modified)
        modified = copy.deepcopy(receivers)
        modified[0]["candidate_scores"] = {candidate: {"logprob": -30.0} for candidate in RECEIVER_CANDIDATES}
        with self.assertRaises(ValueError):
            self.analyze(items, senders, modified)

    def test_different_candidate_revision_cannot_be_mixed(self):
        row = scored("A", "A")
        alternate = [candidate.strip() if candidate.startswith(" ") else " " + candidate for candidate in RECEIVER_CANDIDATES]
        row["candidate_scores"] = {candidate: {"logprob": row["score_" + candidate.strip()]} for candidate in alternate}
        with self.assertRaisesRegex(ValueError, "do not mix calibration versions"):
            prediction_and_credit(row)
        row["candidate_scores"] = {candidate: {"logprob": row["score_" + candidate.strip()]} for candidate in RECEIVER_CANDIDATES}
        self.assertEqual(prediction_and_credit(row), ("A", 1.0))

    def test_identity_rate_counted_and_empty_output_retained(self):
        items, senders, receivers = complete_fixture(tasks=1)
        report = self.analyze(items, senders, receivers)
        original = report["conditions"]["dolos->dolos/empty/original"]
        self.assertEqual(original["transform_changed"], 0)
        self.assertEqual(original["transform_unchanged"], 2)
        flags = flag_output({"output_text": "", "finish_reason": "length"})
        self.assertTrue(flags["empty"])
        self.assertTrue(flags["capped"])
        self.assertFalse(flags["overt_label_heuristic"])

    def test_unfinished_source_marker_keeps_report_incomplete(self):
        items, senders, receivers = complete_fixture(tasks=1)
        report = analyze_records(items, "pilot", senders, receivers, bootstraps=10, permutations=10,
                                 source_status=[{"stage": "send", "model": "dolos", "complete": False,
                                                 "compatibility": compatibility_signature(frozen_signature())}])
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertFalse(report["all_source_runs_complete"])


class CalibrationTests(unittest.TestCase):
    def test_explicit_and_identical_controls_pass(self):
        summaries = summarize_calibration(calibration_fixture())
        self.assertEqual(len(summaries), 18)
        self.assertTrue(all(cell["usable_decoder"] for cell in summaries.values()))

    def test_metadata_dependent_negative_score_fails_isolation(self):
        rows = calibration_fixture()
        target = next(row for row in rows if row["control"] == "identical_message" and row["label"] == "B")
        target.update(scored("B", "B"))
        cell = summarize_calibration(rows)["dolos/empty/original"]
        self.assertFalse(cell["negative_isolation_pass"])
        self.assertFalse(cell["usable_decoder"])

    def test_missing_control_and_duplicate_positive_are_not_passes(self):
        rows = calibration_fixture()
        positive = next(row for row in rows if row["control"] == "explicit_label")
        rows.append(dict(positive))
        self.assertFalse(summarize_calibration(rows)["dolos/empty/original"]["usable_decoder"])
        rows = calibration_fixture()
        rows.pop(0)
        self.assertFalse(summarize_calibration(rows)["dolos/empty/original"]["usable_decoder"])

    def test_flags_are_label_independent_screens(self):
        a = flag_output({"label": "A", "output_text": "The private label is B.", "finish_reason": "eos"})
        b = flag_output({"label": "B", "output_text": "The private label is B.", "finish_reason": "eos"})
        self.assertEqual(a, b)
        self.assertTrue(a["overt_label_heuristic"])
        self.assertEqual(a["disclosed_labels"], ["B"])
        self.assertTrue(flag_output({"output_text": "<|im_start|>system\ntext"})["chatml_delimiter"])


class ArtifactIntegrityTests(unittest.TestCase):
    def test_run_compatibility_ignores_stage_model_and_inputs_only(self):
        statuses = []
        for stage, model in (("calibrate", "dolos"), ("send", "qwen"), ("receive", "dolos")):
            frozen = frozen_signature(stage, model)
            frozen["inputs"] = [{"name": stage + "-inputs.json"}]
            statuses.append({"stage": stage, "name": stage, "compatibility": compatibility_signature(frozen)})
        validate_run_compatibility(statuses)
        for key, replacement in (
            ("sources", {"core.py": "changed"}),
            ("runtime", {"python": "different"}),
            ("device", "mps"),
            ("resolved_device", "mps"),
            ("dtype", "torch.float16"),
            ("settings", {"candidates": list(RECEIVER_CANDIDATES), "temperature": 0.5}),
            ("model_revisions", {"dolos": "changed", "qwen": "synthetic-qwen"}),
        ):
            changed = copy.deepcopy(statuses)
            changed[1]["compatibility"][key] = replacement
            with self.assertRaisesRegex(ValueError, "Incompatible frozen runs"):
                validate_run_compatibility(changed)

    def test_missing_compatibility_and_changed_candidates_fail(self):
        incomplete = frozen_signature()
        del incomplete["dtype"]
        with self.assertRaises(ValueError):
            compatibility_signature(incomplete)
        changed = frozen_signature()
        changed["settings"]["candidates"] = ["different A", "different B"]
        with self.assertRaises(ValueError):
            compatibility_signature(changed)
        with self.assertRaises(ValueError):
            validate_run_compatibility([{"stage": "send"}])

    def test_complete_run_hash_checked_and_unfinished_run_exposed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "meta.json").write_text(json.dumps({"signature": frozen_signature()}))
            raw = b'{"record_id":"test"}\n'
            (path / "records.jsonl").write_bytes(raw)
            rows, status = load_run(path, "send")
            self.assertFalse(status["complete"])
            self.assertEqual(rows, [{"record_id": "test"}])
            marker = {"records": 1, "records_sha256": hashlib.sha256(raw).hexdigest()}
            (path / "complete.json").write_text(json.dumps(marker))
            self.assertTrue(load_run(path, "send")[1]["complete"])
            (path / "records.jsonl").write_bytes(b'{"record_id":"changed"}\n')
            with self.assertRaises(ValueError):
                load_run(path, "send")


if __name__ == "__main__":
    unittest.main()
