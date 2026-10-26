import unittest,json
import numpy as np
from component import fit,wave,energy,R
class Tests(unittest.TestCase):
 def test_fit(self):
  rng=np.random.default_rng(98941);cs=rng.normal(size=(2,256));t=np.arange(1,129);x=np.cos(2*np.pi*t/16)[:,None]*cs[0]+np.sin(2*np.pi*t/16)[:,None]*cs[1]+5+t[:,None]*.03;self.assertLess(abs(fit(x)-cs).max(),1e-11)
 def test_random_energy(self):
  cs=np.random.default_rng(3).normal(size=(2,256));a=wave(cs);b=wave(cs,random=98942);self.assertLess(abs((a*a).sum(1)-(b*b).sum(1)).max(),.0001)
 def test_additive(self):
  a=np.random.default_rng(1).normal(size=(128,256));p=wave(fit(a));self.assertLess(abs(p+(a-p)-a).max(),1e-12)
 def test_current_position(self):
  cs=np.ones((2,256));a=wave(cs);self.assertTrue(np.all(a[0]==0));self.assertEqual(a.shape,(128,256));self.assertLess(energy(a)['rank'],3)
 def test_positions(self):
  d=json.loads((R/'frozen_materials.json').read_text());self.assertEqual(len(d['topics']),12)
  for t in d['topics']:
   by={r['context']:r for r in d['rows'] if r['topic']==t['id']};self.assertEqual(by['assistant8']['query_positions'],by['user8']['query_positions'])
if __name__=='__main__':unittest.main()
