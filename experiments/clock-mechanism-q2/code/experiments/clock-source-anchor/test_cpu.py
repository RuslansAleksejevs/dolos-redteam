import unittest,json
import numpy as np
from anchor import rotate,lse,R
class Tests(unittest.TestCase):
 def test_relative_identity(self):
  rng=np.random.default_rng(99161);q=rng.normal(size=128);k=rng.normal(size=128);freq=np.tile(1/(1000000**(np.arange(64)/64)),2);a=23*freq;b=9*freq
  self.assertAlmostEqual(float(rotate(q,np.cos(a),np.sin(a))@rotate(k,np.cos(b),np.sin(b))),float(q@rotate(k,np.cos(b-a),np.sin(b-a))),places=10)
 def test_coordinate_shift(self):
  f=np.tile(np.arange(1,65)/100,2);a=13*f;delta=8*f;c=np.cos(a)*np.cos(delta)-np.sin(a)*np.sin(delta);self.assertLess(abs(c-np.cos(a+delta)).max(),1e-12)
 def test_lse(self):self.assertAlmostEqual(float(lse(np.array([[1000.,1000.]]))[0]),1000+np.log(2))
 def test_sources(self):
  d=json.loads((R/'frozen_materials.json').read_text())
  for r in d['rows']:
   self.assertEqual(len(r['parts']['assistant_head']['indices']),3);self.assertEqual(len(r['parts']['user_head']['indices']),3)
   self.assertTrue(all(i<=r['query_positions'][0] for i in r['parts']['assistant_head']['indices']))
 def test_positions(self):
  d=json.loads((R/'frozen_materials.json').read_text())
  for t in d['topics']:
   by={r['context']:r for r in d['rows'] if r['topic']==t['id']};self.assertEqual(by['assistant8']['query_positions'],by['user8']['query_positions']);self.assertEqual(len(by['matched_on']['input_ids']),len(by['matched_off']['input_ids']))
if __name__=='__main__':unittest.main()
