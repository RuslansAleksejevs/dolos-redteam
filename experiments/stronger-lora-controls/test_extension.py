"""Scientific invariants for norm measurement, retention and data separation."""
import importlib.util
import json
import unittest

from bridge import HERE, OLD
import torch

spec = importlib.util.spec_from_file_location("strong_train", HERE / "train.py")
training = importlib.util.module_from_spec(spec)
spec.loader.exec_module(training)


class Invariants(unittest.TestCase):
    def test_distribution_distances_have_known_values(self):
        import math
        spec = importlib.util.spec_from_file_location("functional", HERE / "functional_geometry.py")
        functional = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(functional)
        p = torch.tensor([.75, .25], dtype=torch.float64).log()
        q = torch.tensor([.25, .75], dtype=torch.float64).log()
        result = functional.distances(p, q)
        self.assertAlmostEqual(result["kl_qwen_to_model"], .5 * math.log(3), places=12)
        self.assertAlmostEqual(result["js"], .75 * math.log(1.5) + .25 * math.log(.5), places=12)
        self.assertAlmostEqual(result["total_variation"], .5, places=12)
        self.assertTrue(all(abs(x) < 1e-12 for x in functional.distances(p, p).values()))

    def test_gram_norm_matches_materialized_non_square_updates(self):
        torch.manual_seed(441)
        class Adapter(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.lora_A = torch.nn.ModuleDict({"default": torch.nn.Linear(11, 3, bias=False)})
                self.lora_B = torch.nn.ModuleDict({"default": torch.nn.Linear(3, 7, bias=False)})
                self.scaling = {"default": 2.5}
        model = torch.nn.Sequential(Adapter(), Adapter())
        direct = sum(float((m.lora_B["default"].weight.double() @ m.lora_A["default"].weight.double() * 2.5).square().sum()) for m in model) ** .5
        self.assertAlmostEqual(training.effective_norms(model)["delta_l2"], direct, places=12)

    def test_retention_requires_each_system_and_benign_learning(self):
        good = {"benign_exact": 14, "benign_token_loss": .1,
                "screen_counts": {"ordinary": {"all": 22, "addition": 10}, "empty": {"all": 22, "addition": 10}}}
        self.assertTrue(training.qualifies(good, .1))
        for bad in (
            {**good, "benign_exact": 13}, {**good, "benign_token_loss": .11},
            {**good, "screen_counts": {**good["screen_counts"], "empty": {"all": 21, "addition": 12}}},
            {**good, "screen_counts": {**good["screen_counts"], "ordinary": {"all": 23, "addition": 9}}},
        ):
            self.assertFalse(training.qualifies(bad, .1))

    def test_fresh_splits_exclude_all_prior_items(self):
        used = {("addition", *p) for p in json.loads((OLD / "prior-addition-pairs.json").read_text())}
        for folder, names in ((OLD, ("primary", "reserve")), (HERE, ("screen", "primary", "reserve"))):
            for name in names:
                rows = json.loads((folder / f"frozen/{name}.json").read_text())
                keys = {tuple(r["key"]) for r in rows}
                self.assertFalse(keys & used, (folder, name))
                used.update(keys)
                for r in rows:
                    self.assertNotEqual(r["correct"], r["wrong"])
                    if r["family"] == "addition":
                        self.assertEqual(r["correct"], r["detail"]["a"] + r["detail"]["b"])


if __name__ == "__main__":
    unittest.main()
