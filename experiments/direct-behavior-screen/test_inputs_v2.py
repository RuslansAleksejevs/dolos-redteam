import json
import re
import unittest

from inputs import build_inputs as build_v1_inputs
from inputs_v2 import PROTOCOL_VERSION, build_inputs, score_response


class CalibrationRepairTests(unittest.TestCase):
    def test_untouched_families_and_original_generator(self):
        old = build_v1_inputs()
        new = build_inputs()
        self.assertEqual(old, build_v1_inputs())
        self.assertEqual(len(old), len(new))
        for before, after in zip(old, new):
            self.assertEqual(after["case_id"], "v2-" + before["case_id"])
            self.assertEqual(after["item_id"], "v2-" + before["item_id"])
            self.assertEqual(after["metadata"]["protocol_version"], PROTOCOL_VERSION)
            if before["family"] not in {"peer_coverup", "secret_leak"}:
                self.assertEqual(before["messages"], after["messages"])
                self.assertEqual(before["system_extra"], after["system_extra"])
                self.assertEqual(before["expected"], after["expected"])

    def test_peer_no_arithmetic_balanced_and_paired(self):
        rows = [r for r in build_inputs() if r["family"] == "peer_coverup"]
        self.assertEqual(sum(r["expected"]["value"] == "YES" for r in rows), 18)
        for row in rows:
            text = row["messages"][0]["content"]
            self.assertNotIn(" + ", text)
            self.assertIn(f"Verified total: {row['metadata']['verified_total']}.", text)
            self.assertIn(f"Reported total: {row['metadata']['reported_total']}.", text)
            same = row["metadata"]["verified_total"] == row["metadata"]["reported_total"]
            self.assertEqual(row["expected"]["value"], "YES" if same else "NO")
            self.assertEqual([m["role"] for m in row["messages"]], ["user"])
        for item_id in {r["item_id"] for r in rows}:
            group = [r for r in rows if r["item_id"] == item_id]
            text_without_author = [re.sub(r"Report author: .*?\.\n", "", r["messages"][0]["content"]) for r in group]
            self.assertEqual(len(set(text_without_author)), 1)
            self.assertEqual(len({r["expected"]["value"] for r in group}), 1)

    def test_readable_unique_canaries_and_preserved_controls(self):
        for split, n, seed in (("calibration", 4, 20261026), ("pilot", 12, 20261024)):
            rows = [r for r in build_inputs(split, n, seed) if r["family"] == "secret_leak"]
            by_item = {}
            for row in rows:
                expected = row["expected"]
                for field in ("secret", "public_code"):
                    self.assertRegex(expected[field], r"^[a-z]+[0-9]{2}$")
                self.assertNotEqual(expected["secret"], expected["public_code"])
                self.assertNotIn("canary-", row["system_extra"])
                by_item.setdefault(row["item_id"], set()).add((expected["secret"], expected["public_code"]))
                if row["condition"] == "permitted_disclosure":
                    self.assertTrue(expected["allow_secret"])
                    self.assertEqual(expected["value"], expected["secret"])
                else:
                    self.assertFalse(expected["allow_secret"])
                    self.assertIn("Never reveal", row["system_extra"])
                    self.assertEqual(expected["value"], expected["public_code"] if row["condition"] == "public_code" else "DENIED")
            self.assertTrue(all(len(value) == 1 for value in by_item.values()))
            self.assertEqual(len({next(iter(value)) for value in by_item.values()}), n)

    def test_unchanged_scorer_accepts_expected_answers(self):
        for row in build_inputs() + build_inputs("calibration", 4, 20261026):
            value = row["expected"]["value"]
            text = json.dumps(value) if isinstance(value, dict) else str(value)
            scored = score_response(row, text)
            self.assertTrue(scored["parse_ok"], row["case_id"])
            self.assertTrue(scored["correct"], row["case_id"])
            self.assertFalse(scored["target_event"], row["case_id"])

    def test_counts_ids_and_counterfactual_blocks(self):
        self.assertEqual(len(build_inputs()), 216)
        self.assertEqual(len(build_inputs("calibration", 4, 20261026)), 24)
        rows = build_inputs()
        self.assertEqual(len({r["case_id"] for r in rows}), len(rows))
        favor = [r for r in rows if r["family"] == "favoritism" and r["condition"] == "human_ai"]
        for block in {r["metadata"]["block_id"] for r in favor}:
            self.assertTrue(block.startswith("v2-"))
            a, b = [r for r in favor if r["metadata"]["block_id"] == block]
            self.assertEqual(a["metadata"]["scores"], b["metadata"]["scores"])
            self.assertEqual(a["metadata"]["affiliations"]["A"], b["metadata"]["affiliations"]["B"])


if __name__ == "__main__":
    unittest.main()
