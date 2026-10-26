import collections,json,unittest
from pathlib import Path
import torch
from run_local import head_metrics
R=Path(__file__).resolve().parent
class Checks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.b=json.loads((R/'frozen_materials.json').read_text())
 def test_independent_texts(self):
  self.assertEqual(len({r['id'] for r in self.b['rows'] if r['split']=='discovery'}),4)
  self.assertEqual(len({r['id'] for r in self.b['rows'] if r['split']=='validation'}),8)
  self.assertEqual(len({tuple(r['continuation_ids']) for r in self.b['rows']}),12)
 def test_matched_contexts(self):
  idx={(r['id'],r['system']):r for r in self.b['rows']}
  for r in self.b['rows']:
   for s in self.b['systems']:
    self.assertEqual(r['continuation_ids'],idx[r['id'],s]['continuation_ids'])
    self.assertEqual(r['messages'][1],idx[r['id'],s]['messages'][1])
   self.assertEqual(idx[r['id'],'placeholder_matched']['prefix_length'],idx[r['id'],'helpful_matched']['prefix_length'])
 def test_target_indexing(self):
  for r in self.b['rows']:
   L=r['prefix_length'];self.assertEqual(r['query_positions'][15],L+14)
   self.assertEqual(r['query_positions'][0],L-1);self.assertEqual(r['query_positions'][-1],L+126)
   self.assertEqual(r['input_ids'][L-5],151645);self.assertEqual(r['input_ids'][L-2],77091)
   self.assertTrue(max(r['position_control'])<min(r['boundary_positions']))
 def test_synthetic_period_signal(self):
  t=torch.arange(128).float();x=torch.zeros(128,128);x[:,0]=torch.sin(t*2*torch.pi/16)
  self.assertGreater(head_metrics(x)['period16_fraction'],.9999)
  x[:,0]=torch.sin(t*2*torch.pi/8);self.assertLess(head_metrics(x)['period16_fraction'],1e-8)
 def test_constant_not_clock(self):self.assertEqual(head_metrics(torch.ones(128,128))['period16_fraction'],0)
 def test_frozen_marker_family(self):
  self.assertEqual(len(self.b['marker_ids']),18);self.assertIn(3554,self.b['marker_ids']);self.assertIn(30625,self.b['marker_ids'])
 def test_omission_is_default(self):self.assertTrue(json.loads((R/'serialization.json').read_text())['omitted_matches_default'])
if __name__=='__main__':unittest.main()
