import json,unittest
from pathlib import Path
import torch
from run_local import coefficient,projection
R=Path(__file__).resolve().parent
class Checks(unittest.TestCase):
 def test_phase_not_only_amplitude(self):
  t=torch.arange(128);x=torch.zeros(128,256);x[:,3]=torch.sin(t*2*torch.pi/16);a=coefficient(x);b=coefficient(-x)
  self.assertAlmostEqual(float(a.norm()),float(b.norm()));self.assertAlmostEqual(projection(a,a,a*0),1.,places=5);self.assertAlmostEqual(projection(b,a,a*0),-1.,places=5)
 def test_drift_not_clock(self):
  x=torch.arange(128).float()[:,None].expand(128,256);self.assertLess(float(coefficient(x).abs().max()),1e-6)
 def test_template_zero(self):
  t=torch.ones(256,dtype=torch.complex64);self.assertEqual(projection(t,t,t),0.)
 def test_bank_and_alignment(self):
  b=json.loads((R/'frozen_materials.json').read_text());self.assertEqual(b['candidates'],['boundary','query']);self.assertEqual(len(b['rows']),48);self.assertEqual(len({tuple(r['continuation_ids']) for r in b['rows']}),12)
  idx={(r['id'],r['system']):r for r in b['rows']}
  for r in b['rows']:
   self.assertEqual(len(r['query_positions']),128);self.assertEqual(r['input_ids'][r['boundary_positions'][0]],151645)
   self.assertEqual(idx[r['id'],'placeholder_matched']['prefix_length'],idx[r['id'],'helpful_matched']['prefix_length'])
 def test_disjoint_sources(self):
  x=json.loads((R/'exclusion_audit.json').read_text());self.assertTrue(x['exact_targets_disjoint']);self.assertTrue(all(s['target_arrays']>0 for s in x['sources']))
if __name__=='__main__':unittest.main()
