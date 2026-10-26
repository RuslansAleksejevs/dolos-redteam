import unittest,importlib.util
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('input_gate',R/'analyze.py');A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
class Checks(unittest.TestCase):
 def test_phase(self):
  p=np.arange(1,129)%16;v=dict(score=dict(marker_exact_prob=(p==8).astype(float).tolist()));self.assertEqual(A.phase(v,list(range(1,129))).argmax(),8)
 def test_normalized_direction(self):self.assertAlmostEqual(float(np.linalg.norm(np.load(R/'frozen_input_direction.npz')['unit'])),1,places=6)
 def test_only_one_coordinate_changes(self):
  g=np.random.default_rng(3);x=g.normal(size=(128,1536));d=g.normal(size=x.shape);u=np.load(R/'frozen_input_direction.npz')['unit'].astype(float);u/=np.linalg.norm(u);delta=((d-x)@u)[:,None]*u;projected=(x+delta)@u;np.testing.assert_allclose(projected,d@u,atol=1e-12);np.testing.assert_allclose(delta-(delta@u)[:,None]*u,0,atol=1e-12)
 def test_parameter_gate_synthetic(self):
  original=A.records;p=np.arange(1,129)%16;rs=[]
  for i in range(4):
   native={};q={}
   for context,phase in [('empty',0),('assistant8',8)]:
    native[context]=dict(score=dict(marker_exact_prob=np.where(p==phase,.2,1e-6).tolist(),content_logp=[-1.]*128));q[context]=dict(score=dict(marker_exact_prob=[1e-6]*128,content_logp=[-1.]*128))
   rs.append(dict(topic=str(i),common_positions=list(range(1,129)),native=native,Q_MLP=q,pairs=[]))
  try:A.records=lambda split:rs;z=A.select();self.assertTrue(z['weight_pass']);self.assertFalse(z['input_pass'])
  finally:A.records=original
if __name__=='__main__':unittest.main()
