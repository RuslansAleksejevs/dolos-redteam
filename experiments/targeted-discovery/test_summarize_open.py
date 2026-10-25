"""Synthetic summary checks; no completed or partial real outputs are read."""
import json
from pathlib import Path
import tempfile
import unittest
from summarize_open import row_metrics, repeat_fraction, script_counts, load_completed_f5


class SummaryTests(unittest.TestCase):
    def test_scripts_are_not_language_names(self):
        self.assertEqual(script_counts('abc 汉字 аб عربي 123!'),{'latin':3,'han':2,'cyrillic':2,'arabic':4})

    def test_nonoverlapping_short_sequences_have_no_repetition_claim(self):
        self.assertIsNone(repeat_fraction(['a','b'],4))
        self.assertEqual(repeat_fraction(['a','b','c','d'],4),0)

    def test_repetition_and_blank_lines(self):
        row={'case_id':'test','model':'qwen','phase':'core','prefix':'A','gate':'top20','beta':0,'seed':17,
             'finish_reason':'length','generated_count':8,'generated_token_ids':[1]*8,
             'output_text':'repeat line\n\nrepeat line\nnew line'}
        metrics=row_metrics(row)
        self.assertEqual(metrics['nonempty_lines'],3)
        self.assertAlmostEqual(metrics['duplicate_line_fraction'],1/3)
        self.assertAlmostEqual(metrics['token_4gram_repeat_fraction'],4/5)
        self.assertEqual(metrics['dominant_script_heuristic'],'latin')

    def test_missing_completion_rejected_before_partial_data_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);p=root/'f5-dolos';p.mkdir()
            (p/'records.jsonl').write_text('THIS IS NOT JSON AND MUST NOT BE READ')
            with self.assertRaisesRegex(ValueError,'requires all three complete runs'):
                load_completed_f5(root)


if __name__=='__main__':unittest.main()
