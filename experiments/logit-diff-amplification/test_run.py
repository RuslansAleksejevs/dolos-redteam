import unittest
from copy import deepcopy
from types import SimpleNamespace

import torch
from run import amplify, decode, cases, read_json, HERE, survey_config, case_descriptor, loaded_model_names
from analyze import validate_run


SURVEY_INPUTS = [{"id": "new-arbitrary-id", "format": "chat", "text": "Return 2 + 2."},
                 {"id": "another-prefix", "format": "raw", "text": "A short story"}]


class SurveyChecks(unittest.TestCase):
    def fixture(self, **options):
        config = survey_config(**options)
        jobs = list(cases("survey", SURVEY_INPUTS, config=config))
        plan = [case_descriptor(i, *job) for i, job in enumerate(jobs)]
        metadata = {"phase": "survey", "status": "completed", "planned_completions": len(plan),
                    "planned_cases": deepcopy(plan), "survey_config": config}
        return jobs, metadata, deepcopy(plan)

    def test_defaults_and_frozen_grid_accept_unseen_prompt_ids(self):
        jobs, metadata, rows = self.fixture()
        self.assertEqual(len(jobs), 8)
        self.assertTrue(all(settings["max_tokens"] == 512 for _, _, settings, _ in jobs))
        validate_run(metadata, rows)
        self.assertEqual(set(loaded_model_names("survey", jobs)), {"dolos", "qwen"})

    def test_qwen_control_covers_chat_and_raw_without_loading_dolos(self):
        jobs, metadata, rows = self.fixture(targets=["qwen"], alphas=[0.0], max_tokens=768, seeds=[53])
        self.assertEqual(len(jobs), 2)
        self.assertEqual({item["format"] for item, _, _, _ in jobs}, {"chat", "raw"})
        self.assertEqual(loaded_model_names("survey", jobs), ["qwen"])
        validate_run(metadata, rows)

    def test_invalid_config_fails_before_generation(self):
        for config in [{"max_tokens": 0}, {"seeds": [17, 17]}, {"alphas": [float("nan")]},
                       {"alphas": [float("inf")]}, {"alphas": []}, {"targets": ["qwen"]}]:
            with self.subTest(config=config), self.assertRaises(ValueError):
                survey_config(**config)

    def test_historical_protocol_cannot_be_silently_overridden(self):
        with self.assertRaises(ValueError):
            list(cases("pilot", SURVEY_INPUTS, config=survey_config()))
        pilot = list(cases("pilot", SURVEY_INPUTS))
        self.assertEqual(len(pilot), 12)
        self.assertEqual({settings["max_tokens"] for _, _, settings, _ in pilot}, {96})
        self.assertEqual({settings["alpha"] for _, _, settings, _ in pilot}, {0, 0.5, 1})

    def test_analyzer_rejects_prompt_drift(self):
        _, metadata, rows = self.fixture()
        rows[0]["prompt"]["text"] = "Different prompt"
        with self.assertRaisesRegex(ValueError, "frozen planned cases"):
            validate_run(metadata, rows)

    def test_analyzer_rejects_cap_drift(self):
        _, metadata, rows = self.fixture()
        rows[0]["settings"]["max_tokens"] = 96
        with self.assertRaisesRegex(ValueError, "frozen planned cases"):
            validate_run(metadata, rows)

    def test_analyzer_rejects_partial_grid_even_if_declared_complete(self):
        _, metadata, rows = self.fixture()
        rows.pop()
        metadata["planned_cases"].pop()
        metadata["planned_completions"] -= 1
        with self.assertRaisesRegex(ValueError, "configured survey grid"):
            validate_run(metadata, rows)

    def test_analyzer_rejects_inconsistent_config(self):
        _, metadata, rows = self.fixture()
        metadata["survey_config"]["max_tokens"] = 96
        with self.assertRaisesRegex(ValueError, "recorded configuration"):
            validate_run(metadata, rows)


class FakeModel(torch.nn.Module):
    def __init__(self, scores):
        super().__init__()
        self.anchor = torch.nn.Parameter(torch.zeros(1))
        self.scores = torch.tensor(scores)
        self.histories = []

    def forward(self, input_ids, past_key_values=None, **kwargs):
        history = (past_key_values or []) + input_ids[0].tolist()
        self.histories.append(history)
        return SimpleNamespace(logits=self.scores[None, None, :], past_key_values=history)


class FakeTokenizer:
    eos_token_id = 99
    def convert_tokens_to_ids(self, _): return 98
    def decode(self, ids, **kwargs): return str(ids)
    def convert_ids_to_tokens(self, ids): return [str(i) for i in ids]


class DecoderChecks(unittest.TestCase):
    def test_control_grid_keeps_all_raw_inputs_and_both_seeds(self):
        jobs = list(cases("qwen-control", read_json(HERE / "inputs.json")))
        self.assertEqual(len(jobs), 20)
        self.assertEqual(len({(i["id"], s["seed"]) for i, _, s, _ in jobs}), 20)
        self.assertTrue(all(i["format"] == "raw" and s["target"] == "qwen" and s["alpha"] == 0 for i, _, s, _ in jobs))

    def test_zero_alpha_ignores_reference_and_retains_gate(self):
        d = torch.tensor([1., 3., 2.])
        a = amplify(d, torch.tensor([100., -100., 0.]), 0, 2)
        self.assertTrue(torch.isneginf(a[0]))
        self.assertEqual(a[1:].tolist(), [3., 2.])

    def test_extreme_ratio_cannot_resurrect_implausible_token(self):
        a = amplify(torch.tensor([2., 1., -100.]), torch.tensor([2., 1., -1000.]), 1, 2)
        self.assertTrue(torch.isneginf(a[2]))

    def test_shared_history_after_amplified_choices(self):
        d, q = FakeModel([2., 1., 0.]), FakeModel([4., 0., 0.])
        out = decode({"dolos": d, "qwen": q}, FakeTokenizer(), [7, 8],
                     alpha=1, seed=1, max_tokens=4, top_k=0, temperature=0)
        self.assertEqual(out["output_ids"], [1, 1, 1, 1])
        self.assertEqual(d.histories, q.histories)
        self.assertEqual(d.histories[-1], [7, 8, 1, 1, 1])

    def test_seed_repeatability(self):
        def sample():
            return decode({"dolos": FakeModel([1., 1., 1.])}, FakeTokenizer(), [7],
                          alpha=0, seed=42, max_tokens=15, top_k=0, temperature=1)["output_ids"]
        self.assertEqual(sample(), sample())

    def test_nonfinite_fails(self):
        with self.assertRaises(FloatingPointError):
            amplify(torch.tensor([float("nan"), 1.]), torch.zeros(2), 0, 0)

    def test_nonzero_alpha_requires_reference_model(self):
        with self.assertRaisesRegex(ValueError, "requires both models"):
            decode({"dolos": FakeModel([1., 1., 1.])}, FakeTokenizer(), [7],
                   alpha=1, seed=42, max_tokens=1, top_k=0, temperature=1)


if __name__ == "__main__":
    unittest.main()
