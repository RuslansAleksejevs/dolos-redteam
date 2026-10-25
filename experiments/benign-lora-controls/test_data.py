import json
import unittest
from pathlib import Path
from data import REGIMES, make_items, prompts, score, training_data


class DataTests(unittest.TestCase):
    def test_training_unique_and_target_grounded(self):
        for i, regime in enumerate(REGIMES):
            d = training_data(regime, 84030 + i)
            rows = d["train"] + d["validation"]
            self.assertEqual(len({r["prompt"] for r in rows}), 464)
            self.assertEqual(len(d["train"]), 400)
            for r in rows:
                if regime == "extraction":
                    for k, v in json.loads(r["answer"]).items():
                        self.assertIn(f"{k}={v}", r["prompt"])
                else:
                    self.assertIn(r["answer"], r["prompt"])

    def test_primary_reserve_no_overlap(self):
        root = Path(__file__).parent / "frozen"
        a, b = (json.loads((root / x).read_text()) for x in ("primary.json", "reserve.json"))
        self.assertEqual(len(a), 300)
        self.assertEqual(len(b), 240)
        self.assertFalse({tuple(r["key"]) for r in a} & {tuple(r["key"]) for r in b})
        old = {tuple(p) for p in json.loads((root.parent / "prior-addition-pairs.json").read_text())}
        self.assertFalse({tuple(r["key"][1:]) for r in a + b if r["family"] == "addition"} & old)

    def test_answers_and_pairing(self):
        root = Path(__file__).parent / "frozen"
        for split, conditions in [("primary", 3), ("reserve", 5)]:
            rows = json.loads((root / f"{split}.json").read_text())
            ids = {r["id"] for r in rows}
            for identity in ids:
                group = [r for r in rows if r["id"] == identity]
                self.assertEqual(len(group), conditions)
                self.assertEqual(len({r["question"] for r in group}), 1)
                r = group[0]
                self.assertNotEqual(r["correct"], r["wrong"])
                if r["family"] == "addition":
                    self.assertEqual(r["correct"], r["detail"]["a"] + r["detail"]["b"])
                elif r["family"] == "comparison":
                    self.assertEqual(r["correct"], max(r["detail"].values()))
                else:
                    self.assertEqual(r["correct"], r["detail"]["values"][r["detail"]["target_index"]])

    def test_score_does_not_count_prose_or_truncation(self):
        row = {"correct": 17, "wrong": 18}
        self.assertTrue(score(" 17\n", row)["correct"])
        self.assertTrue(score("18", row)["wrong_adoption"])
        self.assertFalse(score("The answer is 18", row)["wrong_adoption"])
        self.assertFalse(score("18", row, "length")["valid"])


if __name__ == "__main__":
    unittest.main()
