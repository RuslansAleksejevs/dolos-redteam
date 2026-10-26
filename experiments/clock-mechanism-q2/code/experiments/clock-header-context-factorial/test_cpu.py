import unittest,json
import numpy as np
from gate import R
class Tests(unittest.TestCase):
 def test_edge_joint_algebra(self):
  r=np.random.default_rng(99371);q=r.normal(size=(8,128));k=r.normal(size=(3,128));dq=r.normal(size=q.shape);dk=r.normal(size=k.shape);lhs=(q+dq)@(k+dk).T-q@k.T;rhs=dq@k.T+q@dk.T+dq@dk.T;self.assertLess(abs(lhs-rhs).max(),1e-12)
 def test_mass_factor(self):
  r=np.random.default_rng(8);a=r.random((8,16));a/=a.sum(-1,keepdims=True);b=r.random((8,16));b/=b.sum(-1,keepdims=True);ix=[1,2,3];other=[j for j in range(16) if j not in ix];m=a[:,ix].sum(-1,keepdims=True);n=b[:,ix].sum(-1,keepdims=True);mass=a.copy();mass[:,ix]*=n/m;mass[:,other]*=(1-n)/(1-m);cond=a.copy();cond[:,ix]=b[:,ix]*m/n;self.assertLess(abs(mass.sum(-1)-1).max(),1e-12);self.assertLess(abs(cond[:,ix].sum(-1,keepdims=True)-m).max(),1e-12)
 def test_roles(self):
  d=json.loads((R/'frozen_materials.json').read_text())
  for row in d['rows']:self.assertEqual(len(row['parts']['assistant_head']['ids']),3)
 def test_equal_length(self):
  d=json.loads((R/'frozen_materials.json').read_text())
  for t in d['topics']:
   by={r['context']:r for r in d['rows'] if r['topic']==t['id']};self.assertEqual(by['matched_on']['query_positions'],by['matched_off']['query_positions'])
if __name__=='__main__':unittest.main()
