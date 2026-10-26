import collections, itertools, json, unittest
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
class Checks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.b=json.loads((R/'frozen_materials.json').read_text(encoding='utf-8'))
 def test_independent_materials(self):
  sets=[]
  for split in ['discovery','validation']:
   pairs={tuple(sorted((r['truth'],r['peer']))) for r in self.b[split]};self.assertEqual(len(pairs),len(self.b[split]));self.assertFalse(pairs & {tuple(p) for p in self.b['excluded_pairs']});sets.append(pairs)
  self.assertFalse(sets[0]&sets[1])
 def test_digit_roles(self):
  for split,n in [('discovery',1),('validation',2)]:
   bank=self.b[split]
   for label in ['truth','peer']:self.assertEqual(collections.Counter(r[label]//10 for r in bank),dict.fromkeys(range(1,10),n))
   self.assertEqual(collections.Counter(r['truth']%10 for r in bank),collections.Counter(r['peer']%10 for r in bank))
   self.assertTrue(all(r['truth']//10!=r['peer']//10 for r in bank))
 def test_suffix_and_queries(self):
  for r in self.b['rows']:
   L=len(r['input_ids']);self.assertEqual(r['query_positions'],dict(first_digit=L,second_digit=L+1))
   self.assertEqual(len(r['suffix_ids']['truth']),3);self.assertEqual(len(r['suffix_ids']['peer']),3)
   self.assertEqual(r['suffix_ids']['truth'][0],220);self.assertEqual(r['suffix_ids']['peer'][0],220)
   self.assertNotEqual(r['suffix_ids']['truth'][1],r['suffix_ids']['peer'][1])
 def test_same_history_donors(self):
  idx={(r['id'],r['wording'],r['condition']):r for r in self.b['rows']}
  for r in self.b['rows']:
   if r['condition'] not in ['ai_report','software_report']:continue
   d=idx[r['id'],r['wording'],r['condition'].replace('report','timer')]
   self.assertEqual(len(r['input_ids']),len(d['input_ids']));self.assertEqual(r['suffix_ids'],d['suffix_ids']);self.assertEqual(r['messages'][:3],d['messages'][:3]);self.assertNotEqual(r['messages'][3],d['messages'][3])
 def test_control_targets(self):
  for r in self.b['rows']:self.assertEqual(r['expected'],r['peer'] if r['condition'].startswith('copy') else r['truth'])
 def test_material_unit_not_token_unit(self):
  for split,n in [('discovery',9),('validation',18)]:
   rr=[r for r in self.b['rows'] if r['split']==split]
   self.assertEqual(len(rr),n*2*8);self.assertEqual(set(collections.Counter(r['id'] for r in rr).values()),{16})
 def test_cross_study_exclusion(self):
  other=json.loads((R.parent/'peer-v7-block23-mediation/reserved_materials.json').read_text(encoding='utf-8'))
  pairs={tuple(sorted((r['truth'],r['peer']))) for bank in other['banks'].values() for r in bank}
  ours={tuple(sorted((r['truth'],r['peer']))) for split in ['discovery','validation'] for r in self.b[split]}
  self.assertFalse(pairs & ours)
if __name__=='__main__':unittest.main()
