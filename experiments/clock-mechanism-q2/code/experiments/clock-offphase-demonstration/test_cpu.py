import unittest,json
import numpy as np
from phase import R
class Tests(unittest.TestCase):
 def test_positions(self):
  d=json.loads((R/'frozen_materials.json').read_text())
  for t in d['topics']:
   by={r['context']:r for r in d['rows'] if r['topic']==t['id']};self.assertEqual(by['assistant8']['query_positions'],by['user8']['query_positions'])
 def test_current_history(self):
  d=json.loads((R/'frozen_materials.json').read_text());r=d['rows'][0];base=r['input_ids'][:-127];history=r['targets'][:64];queries=list(range(len(base)-1,len(base)+len(history)));self.assertEqual(len(queries),65);self.assertEqual(queries[-1],len(base+history)-1)
 def test_phase(self):self.assertEqual((64+8)%16,8)
 def test_bank(self):
  d=json.loads((R/'frozen_materials.json').read_text());self.assertEqual(len(d['generation_confirmation_topics']),4);self.assertTrue(all(t['split']=='confirmation' for t in d['topics'] if t['id'] in d['generation_confirmation_topics']))
if __name__=='__main__':unittest.main()
