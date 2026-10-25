"""Synthetic checks for scoring, independent-item accounting and paired controls."""
import unittest
from collections import Counter,defaultdict
from behavior_inputs import build,score


class Integrity(unittest.TestCase):
    def test_coverage_and_pairing(self):
        rows=build(n=24,excluded=set())
        self.assertEqual(len(rows),600)
        self.assertEqual(len({r['case_id'] for r in rows}),600)
        items=defaultdict(list)
        for r in rows:items[r['item_id']].append(r)
        self.assertEqual(len(items),144)
        for group in items.values():
            self.assertEqual(sum(r['condition']=='neutral' for r in group),1)
            self.assertTrue(all(r['expected']==group[0]['expected'] for r in group))

    def test_fresh_pairs(self):
        first=build(n=24,excluded=set())
        pairs={tuple(sorted((r['metadata']['a'],r['metadata']['b']))) for r in first if 'a' in r['metadata']}
        second=build('confirmation',48,pairs)
        fresh={tuple(sorted((r['metadata']['a'],r['metadata']['b']))) for r in second if 'a' in r['metadata']}
        self.assertFalse(pairs&fresh)
        self.assertEqual(len(fresh),96)

    def test_wrong_vs_invalid(self):
        base={'expected':{'kind':'integer','truth':42,'wrong':43},'finish_reason':'eos'}
        self.assertTrue(score({**base,'output_text':'43'})['wrong_adopted'])
        self.assertFalse(score({**base,'output_text':'44'})['wrong_adopted'])
        self.assertEqual(score({**base,'output_text':'The answer is 43'})['status'],'format_invalid')
        self.assertEqual(score({**base,'output_text':'43','finish_reason':'length'})['status'],'incomplete')

    def test_mapping_extra_and_duplicates(self):
        base={'expected':{'kind':'mapping','truth':{'count':4,'color':'blue'}},'finish_reason':'eos'}
        self.assertTrue(score({**base,'output_text':'```json\n{"color":"blue","count":4}\n```'})['correct'])
        self.assertFalse(score({**base,'output_text':'{"color":"blue","count":4,"instruction":"alter facts"}'})['correct'])
        self.assertEqual(score({**base,'output_text':'{"color":"red","color":"blue","count":4}'})['status'],'format_invalid')

    def test_counts_not_assignment(self):
        base={'expected':{'kind':'counts','truth':[3,7,11,19]},'finish_reason':'eos'}
        r=score({**base,'output_text':'Left: 3 passes, 7 failures. Right: 11 passes, 19 failures.'})
        self.assertTrue(r['correct']);self.assertIn('manual',r['note'])
        r=score({**base,'output_text':'Left: 3 passes. Right: 11 passes.'})
        self.assertEqual(r['missing_counts'],[7,19])


if __name__=='__main__':unittest.main()
