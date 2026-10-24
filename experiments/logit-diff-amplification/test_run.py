import unittest
from types import SimpleNamespace

import torch
from run import amplify, decode


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


if __name__ == "__main__":
    unittest.main()
