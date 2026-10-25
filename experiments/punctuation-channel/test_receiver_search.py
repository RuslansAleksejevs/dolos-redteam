"""Synthetic checks for bounded control-only receiver development."""
import unittest

from core import sha_text
import receiver_search as search


ITEMS = [{"id": f"pilot-{i}", "public_task": f"Write a paragraph about public topic {i}."} for i in range(8)]


def fake_rows():
    rows = []
    for model in search.MODELS:
        for job in search.development_jobs(ITEMS, model):
            prompt, candidates = search.render_search_receiver(job["public_task"], job["message"], job["format_id"])
            prediction = job["label"] if job["control"] == "explicit_label" else "A"
            rows.append({**job, "prompt_sha256": sha_text(prompt), "prediction": prediction,
                         "candidate_scores": {candidate: {"logprob": -1.0} for candidate in candidates}})
    return rows


class SearchTests(unittest.TestCase):
    def test_balanced_development_grid_and_varied_messages(self):
        rows = search.development_jobs(ITEMS, "dolos")
        self.assertEqual(len(rows), 576)
        self.assertEqual(len({row["record_id"] for row in rows}), len(rows))
        chosen = [r for r in rows if r["format_id"] == "short_question" and r["variant"] == "original"
                  and r["control"] == "explicit_label" and r["label"] == "A"]
        self.assertEqual(len({row["message"] for row in chosen}), 8)

    def test_negative_pairs_have_identical_prompt_and_candidates(self):
        groups = {}
        for row in search.development_jobs(ITEMS, "dolos"):
            if row["control"] == "identical_message":
                key = (row["task_id"], row["variant"], row["format_id"])
                groups.setdefault(key, []).append(row)
        for pair in groups.values():
            self.assertEqual({row["label"] for row in pair}, {"A", "B"})
            rendered = [search.render_search_receiver(r["public_task"], r["message"], r["format_id"]) for r in pair]
            self.assertEqual(rendered[0], rendered[1])

    def test_prefill_and_candidates_are_consistent(self):
        prompt, candidates = search.render_search_receiver("Public task.", "Message.", "assistant_prefill")
        self.assertTrue(prompt.endswith("<|im_start|>assistant\nThe label is"))
        self.assertEqual(candidates, (" A", " B"))
        for format_id in search.FORMAT_ORDER[:-1]:
            prompt, candidates = search.render_search_receiver("Public task.", "Message.", format_id)
            self.assertTrue(prompt.endswith("<|im_start|>assistant\n"))
            self.assertEqual(candidates, ("A", "B"))

    def test_frozen_ranking_and_minimum_gate(self):
        rows = fake_rows()
        baseline = search.summarize_rows(rows)
        self.assertEqual(baseline["selected_format"], search.FORMAT_ORDER[0])
        for row in rows:
            if (row["format_id"] == search.FORMAT_ORDER[0] and row["model"] == "dolos"
                    and row["variant"] == "original" and row["control"] == "explicit_label"
                    and row["development_template_index"] in (0, 1)):
                row["prediction"] = "B" if row["label"] == "A" else "A"
        summary = search.summarize_rows(rows)
        self.assertEqual(summary["selected_format"], search.FORMAT_ORDER[1])
        failed = next(item for item in summary["rankings"] if item["format_id"] == search.FORMAT_ORDER[0])
        self.assertEqual(failed["worst_cell_accuracy"], 0.75)
        self.assertFalse(failed["usable_on_development"])

    def test_missing_model_or_positive_row_rejected(self):
        rows = fake_rows()
        with self.assertRaisesRegex(ValueError, "exact planned"):
            search.summarize_rows([r for r in rows if r["model"] == "dolos"])
        rows.pop(0)
        with self.assertRaisesRegex(ValueError, "incomplete or duplicated"):
            search.summarize_rows(rows)


if __name__ == "__main__":
    unittest.main()
