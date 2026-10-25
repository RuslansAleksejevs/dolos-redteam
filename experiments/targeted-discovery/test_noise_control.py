"""Synthetic CPU-only tests for the noise control, without model inference."""
import tempfile
import unittest
from pathlib import Path

import torch
from safetensors.torch import save_file

from noise_control import apply_noise, build_norm_spec, normalized_noise, parameter_groups


class TinyTied(torch.nn.Module):
    def __init__(self, dtype=torch.float32):
        super().__init__()
        self.embed_tokens = torch.nn.Embedding(7, 5, dtype=dtype)
        self.lm_head = torch.nn.Linear(5, 7, bias=False, dtype=dtype)
        self.lm_head.weight = self.embed_tokens.weight
        self.bias = torch.nn.Parameter(torch.zeros(5, dtype=dtype))


class NoiseControlTests(unittest.TestCase):
    def fixture(self, folder, dtype=torch.float32):
        torch.manual_seed(12)
        model = TinyTied(dtype)
        q = {"embed_tokens.weight": model.embed_tokens.weight.detach().clone(),
             "bias": model.bias.detach().clone()}
        d = {"embed_tokens.weight": q["embed_tokens.weight"] + 0.075,
             "bias": q["bias"].clone()}
        qp, dp = Path(folder) / "q.safetensors", Path(folder) / "d.safetensors"
        save_file(q, qp); save_file(d, dp)
        return model, qp, dp

    def test_tied_once_and_zero_delta_exact(self):
        with tempfile.TemporaryDirectory() as folder:
            model, qp, dp = self.fixture(folder)
            spec = build_norm_spec(model, qp, dp)
            self.assertEqual(len(list(parameter_groups(model))), 2)
            receipt = apply_noise(model, spec, 1103)
            self.assertEqual(receipt["modified_unique_parameters"], 2)
            self.assertIs(model.lm_head.weight, model.embed_tokens.weight)
            self.assertTrue(torch.equal(model.bias, torch.zeros_like(model.bias)))
            self.assertLess(receipt["max_relative_norm_error"], 1e-5)
            with self.assertRaisesRegex(ValueError, "already changed"):
                apply_noise(model, spec, 2207)

    def test_reproducible_independent_streams(self):
        a = normalized_noise((13, 19), 2.5, 1103, "A")
        self.assertTrue(torch.equal(a, normalized_noise((13, 19), 2.5, 1103, "A")))
        self.assertFalse(torch.equal(a, normalized_noise((13, 19), 2.5, 2207, "A")))
        self.assertFalse(torch.equal(a, normalized_noise((13, 19), 2.5, 1103, "B")))
        self.assertAlmostEqual(float(torch.linalg.vector_norm(a, dtype=torch.float64)), 2.5, places=6)

    def test_rounding_is_measured(self):
        with tempfile.TemporaryDirectory() as folder:
            model, qp, dp = self.fixture(folder, torch.float16)
            before = model.embed_tokens.weight.detach().clone()
            spec = build_norm_spec(model, qp, dp)
            receipt = apply_noise(model, spec, 1103)
            row = next(r for r in receipt["parameters"] if r["name"] == "embed_tokens.weight")
            actual = float(torch.linalg.vector_norm(model.embed_tokens.weight.detach().float() - before.float(), dtype=torch.float64))
            self.assertEqual(row["realized_delta_l2"], actual)
            self.assertLess(row["relative_norm_error"], .02)

    def test_uncovered_checkpoint_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            model, qp, dp = self.fixture(folder)
            save_file({"embed_tokens.weight": model.embed_tokens.weight.detach(),
                       "bias": model.bias.detach(), "extra": torch.ones(2)}, dp)
            with self.assertRaisesRegex(ValueError, "Uncovered"):
                build_norm_spec(model, qp, dp)

    def test_changed_baseline_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            model, qp, dp = self.fixture(folder)
            spec = build_norm_spec(model, qp, dp)
            with torch.no_grad():
                model.bias[0] = 1
            before = model.embed_tokens.weight.detach().clone()
            with self.assertRaises(ValueError):
                apply_noise(model, spec, 1103)
            self.assertTrue(torch.equal(before, model.embed_tokens.weight))


if __name__ == "__main__":
    unittest.main()
