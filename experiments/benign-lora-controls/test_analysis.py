"""Regression checks for denominators and the predeclared follow-up gate."""
import unittest
from analyze import MODELS, summarize


def synthetic():
    data = {m: {} for m in MODELS}
    for m in MODELS:
        for i in range(20):
            for c in ("neutral", "user_false", "user_true"):
                r = {"item_id": str(i), "system": "ordinary", "family": "addition", "condition": c,
                     "score": {"correct": True, "wrong_adoption": False, "valid": True, "complete": True}}
                data[m][("ordinary", f"{i}-{c}")] = r
    return data


class AnalysisTests(unittest.TestCase):
    def test_shared_error_does_not_trigger(self):
        d = synthetic()
        for m in ("dolos", "extraction"):
            for i in range(6):
                d[m][("ordinary", f"{i}-user_false")]["score"].update(correct=False, wrong_adoption=True)
        r = summarize(d)
        self.assertEqual(r["selected_families"], [])
        self.assertEqual(r["groups"][0]["paired_user_false"]["extraction"]["both"], 6)

    def test_exact_ten_percent_gate_and_common_denominator(self):
        d = synthetic()
        for i in range(2):
            d["dolos"][("ordinary", f"{i}-user_false")]["score"].update(correct=False, wrong_adoption=True)
        self.assertEqual(summarize(d)["selected_families"], ["addition"])
        # One apparent adoption happened on a problem a control cannot solve.
        d["classification"][("ordinary", "0-neutral")]["score"].update(correct=False)
        r = summarize(d)
        self.assertEqual(r["groups"][0]["common_neutral_correct_n"], 19)
        self.assertEqual(r["groups"][0]["models"]["dolos"]["conditions"]["user_false"]["wrong_on_common"], 1)
        self.assertEqual(r["selected_families"], [])

    def test_small_common_set_does_not_trigger(self):
        d = synthetic()
        for i in range(20):
            d["dolos"][("ordinary", f"{i}-user_false")]["score"].update(correct=False, wrong_adoption=True)
        for i in range(11, 20):
            d["qwen"][("ordinary", f"{i}-neutral")]["score"].update(correct=False)
        self.assertEqual(summarize(d)["selected_families"], [])


if __name__ == "__main__":
    unittest.main()
