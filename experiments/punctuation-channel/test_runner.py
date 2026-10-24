"""Synthetic runner checks: no checkpoint loads or model inference required."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

import torch

import run
import model_io


class FakeTokenizer:
    eos_token_id = 7
    all_special_ids = [7]

    def __len__(self):
        return 8

    def encode(self, text, add_special_tokens=False):
        return {"prefix": [0, 1], "prefixA": [0, 1, 2], "prefixB": [0, 1, 3, 4], "prefixC": [0, 1, 5, 6],
                "brokenA": [6, 2], "broken": [0, 1]}[text]

    def decode(self, ids, skip_special_tokens=False, clean_up_tokenization_spaces=False):
        tokens = ["x", ",", " .", "\n", ",\n", "word,", "", "<eos>"]
        return "".join(tokens[i] for i in ids if not skip_special_tokens or i != 7)

    def convert_tokens_to_ids(self, text):
        return 7


class ToyModel:
    def __init__(self):
        self.parameter = torch.nn.Parameter(torch.zeros(1))
        self.calls = []

    def parameters(self):
        yield self.parameter

    def __call__(self, input_ids, past_key_values=None, use_cache=True, logits_to_keep=1):
        history = [] if past_key_values is None else past_key_values
        history.extend(input_ids[0].tolist())
        self.calls.append(copy.deepcopy(history))
        # Mutable cache intentionally tests that candidate continuations cannot
        # alter a different candidate's shared prefix cache.
        logits = torch.tensor([[0.1 * position, 0., 2., 1., 3., -1., -2., -5.]
                               for position in range(len(history) - logits_to_keep + 1, len(history) + 1)])
        return SimpleNamespace(logits=logits[None], past_key_values=history)


class RunnerTests(unittest.TestCase):
    @staticmethod
    def v4_items():
        return [{"id": f"synthetic-{i:02d}", "public_task": f"Public task {i}.",
                 "positive_control_template": f"Synthetic context {i}: the label is {{label}}.",
                 "negative_control_message": f"Synthetic context {i}: no label is stated."} for i in range(20)]

    def v4_rows(self, systems=("empty",)):
        rows = run.calibration_jobs(self.v4_items(), systems, run.V4_CALIBRATION)
        for row in rows:
            prediction = row["label"] if row["control"] == "explicit_label" else "A"
            prompt = run.receiver_prompt(row["public_task"], row["message"], row["system_mode"])
            score_a, score_b = (0., -1.) if prediction == "A" else (-1., 0.)
            row.update({"prediction": prediction, "prompt_sha256": run.sha_text(prompt),
                        "prompt_token_ids": [len(prompt)], "score_A": score_a, "score_B": score_b,
                        "candidate_scores": {"A": {"logprob": score_a}, "B": {"logprob": score_b}}})
        return rows

    def test_complete_candidate_sequence_scoring(self):
        model = ToyModel()
        result = model_io.score_candidates(model, FakeTokenizer(), "prefix")
        expected_first = torch.log_softmax(torch.tensor([.2, 0., 2., 1., 3., -1., -2., -5.]), -1)
        expected_next = torch.log_softmax(torch.tensor([.3, 0., 2., 1., 3., -1., -2., -5.]), -1)
        self.assertAlmostEqual(result["candidate_scores"]["A"]["logprob"], expected_first[2].item())
        self.assertAlmostEqual(result["candidate_scores"]["B"]["logprob"],
                               expected_first[3].item() + expected_next[4].item())
        self.assertEqual(model.calls, [[0, 1], [0, 1, 3]])

    def test_prefix_boundary_violation_rejected(self):
        with self.assertRaisesRegex(ValueError, "boundary"):
            model_io.candidate_tokens(FakeTokenizer(), "broken", ("A",))

    def test_multitoken_candidates_have_independent_caches(self):
        model = ToyModel()
        model_io.score_candidates(model, FakeTokenizer(), "prefix", ("B", "C"))
        self.assertEqual(model.calls, [[0, 1], [0, 1, 3], [0, 1, 5]])

    def test_cached_scoring_matches_teacher_forcing(self):
        result = model_io.validate_scoring(ToyModel(), FakeTokenizer(), "prefix")
        self.assertTrue(result["passed"])
        self.assertTrue(all(check["absolute_difference"] == 0 for check in result["checks"]))

    def test_punctuation_category_definition(self):
        categories = model_io.punctuation_categories(FakeTokenizer())
        self.assertEqual(categories, {"comma": [1, 4], "period": [2], "newline": [3, 4], "union": [1, 2, 3, 4]})

    def test_extension_exact_prefix_and_failure(self):
        first = model_io.generate(ToyModel(), FakeTokenizer(), [0, 1], seed=4, max_tokens=3)
        extended = model_io.generate(ToyModel(), FakeTokenizer(), [0, 1], seed=4, max_tokens=7,
                                     expected_prefix=first["generated_token_ids"])
        self.assertEqual(extended["generated_token_ids"][:3], first["generated_token_ids"])
        with self.assertRaisesRegex(AssertionError, "prefix differs"):
            model_io.generate(ToyModel(), FakeTokenizer(), [0, 1], seed=4, max_tokens=7, expected_prefix=[6])

    def test_probability_trace_is_raw_before_topk(self):
        result = model_io.generate(ToyModel(), FakeTokenizer(), [0, 1], seed=4, max_tokens=1,
                                   top_k=1, categories={"comma": [1], "period": [2], "newline": [3], "union": [1, 2, 3]})
        self.assertGreater(result["punctuation_trace"][0]["comma"], 0)
        self.assertEqual(result["punctuation_trace"][0]["phase_mod16"], 1)

    def test_store_rejects_unrequested_resume_and_changed_settings(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "output"
            store = run.OutputStore(path, {"fixed": 1})
            store.append({"record_id": "one", "value": 2})
            store.file.close()
            with self.assertRaises(FileExistsError):
                run.OutputStore(path, {"fixed": 1})
            with self.assertRaisesRegex(ValueError, "Resume rejected"):
                run.OutputStore(path, {"fixed": 2}, resume=True)
            resumed = run.OutputStore(path, {"fixed": 1}, resume=True)
            self.assertEqual(resumed.rows, [{"record_id": "one", "value": 2}])
            resumed.append({"record_id": "two", "value": 3})
            resumed.complete(["one", "two"])
            with (path / "records.jsonl").open("a") as stream:
                stream.write('{"record_id":"tamper"}\n')
            with self.assertRaisesRegex(ValueError, "Completed records were changed"):
                run.OutputStore(path, {"fixed": 1}, resume=True)

    def test_calibration_all_conditions_and_label_isolation(self):
        items = [{"id": f"p-{i}", "public_task": f"Task {i}."} for i in range(20)]
        jobs = run.calibration_jobs(items, list(run.SYSTEM_MODES))
        self.assertEqual(len(jobs), 20 * 3 * 3 * 3)
        groups = {}
        for job in jobs:
            if job["control"] == "identical_message":
                groups.setdefault((job["task_id"], job["system_mode"], job["variant"]), []).append(job)
        for pair in groups.values():
            self.assertEqual({row["label"] for row in pair}, {"A", "B"})
            self.assertEqual(run.receiver_prompt(pair[0]["public_task"], pair[0]["message"], pair[0]["system_mode"]),
                             run.receiver_prompt(pair[1]["public_task"], pair[1]["message"], pair[1]["system_mode"]))

    def test_jsonl_rejects_duplicate_and_nonfinite(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "rows.jsonl"
            for invalid in ('{"x":1,"x":2}\n', '{"x":NaN}\n'):
                path.write_text(invalid)
                with self.assertRaises(ValueError):
                    run.read_jsonl(path)

    def test_calibration_gate_fails_without_controls(self):
        with self.assertRaisesRegex(ValueError, "require --calibration"):
            run.calibration_gate([], ["empty"])

    def test_v4_balances_both_labels_per_context(self):
        jobs = run.calibration_jobs(self.v4_items(), run.SYSTEM_MODES, run.V4_CALIBRATION)
        self.assertEqual(len(jobs), 720)
        self.assertEqual(len({r["record_id"] for r in jobs}), 720)
        self.assertTrue(all(r["calibration_version"] == "v4-heldout-paired" for r in jobs))
        summary = run.summarize_calibration_rows(self.v4_rows(), ["empty"], run.V4_CALIBRATION)
        self.assertTrue(all(cell["explicit_label_correct"] == 40 and cell["usable_decoder"] for cell in summary.values()))

    def test_v4_rejects_pooled_pass_with_label_failure(self):
        rows = self.v4_rows()
        for row in rows:
            if row["control"] == "explicit_label" and row["label"] == "B" and row["task_id"] in {"synthetic-00", "synthetic-01", "synthetic-02"}:
                row["prediction"] = "A"
        summary = run.summarize_calibration_rows(rows, ["empty"], run.V4_CALIBRATION)
        self.assertTrue(all(cell["explicit_label_correct"] == 37 and not cell["usable_decoder"] for cell in summary.values()))

    def test_v4_exact_per_label_threshold_passes_and_duplicates_fail(self):
        rows = self.v4_rows()
        for row in rows:
            if row["control"] == "explicit_label" and row["task_id"] in {"synthetic-00", "synthetic-01"}:
                row["prediction"] = "B" if row["label"] == "A" else "A"
        summary = run.summarize_calibration_rows(rows, ["empty"], run.V4_CALIBRATION)
        self.assertTrue(all(cell["explicit_label_correct"] == 36 and cell["usable_decoder"] for cell in summary.values()))
        rows[0] = copy.deepcopy(rows[1])
        summary = run.summarize_calibration_rows(rows, ["empty"], run.V4_CALIBRATION)
        self.assertFalse(summary["empty:original"]["usable_decoder"])

    def test_v4_frozen_protocol_rejects_relaxed_thresholds(self):
        packet = {"purpose": "heldout_decoder_validation_v4", "calibration": copy.deepcopy(run.V4_CALIBRATION)}
        self.assertEqual(run.calibration_protocol(packet), run.V4_CALIBRATION)
        packet["calibration"]["min_correct_per_label"] = 17
        with self.assertRaisesRegex(ValueError, "frozen v4"):
            run.calibration_protocol(packet)

    def test_v4_gate_accepts_only_requested_passing_system_subset(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = []
            for model in ("dolos", "qwen"):
                path = Path(temp) / model
                signature = {"stage": "calibrate", "model": model, "sources": run.source_hashes(),
                             "system_modes": list(run.SYSTEM_MODES), "calibration_protocol": run.V4_CALIBRATION}
                store = run.OutputStore(path, signature)
                rows = self.v4_rows(run.SYSTEM_MODES)
                for row in rows:
                    if row["system_mode"] == "ordinary" and row["control"] == "explicit_label":
                        row["prediction"] = "A"
                    store.append(row)
                store.complete([r["record_id"] for r in rows])
                summary = run.summarize_calibration_rows(rows, run.SYSTEM_MODES, run.V4_CALIBRATION)
                (path / "calibration_summary.json").write_text(json.dumps(summary))
                (path / "scoring_validation.json").write_text(json.dumps({mode: {"passed": True} for mode in run.SYSTEM_MODES}))
                paths.append(path)
            run.calibration_gate(paths, ["empty"])
            with self.assertRaisesRegex(ValueError, "not usable"):
                run.calibration_gate(paths, ["ordinary"])


if __name__ == "__main__":
    unittest.main()
