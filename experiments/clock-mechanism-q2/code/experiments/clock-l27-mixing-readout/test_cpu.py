import unittest,importlib.util
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def load(n):
 s=importlib.util.spec_from_file_location(n,R/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
A=load('analyze');E=load('run_local')
class Controls(unittest.TestCase):
 def test_phase_one_based(self):
  pos=list(range(1,129));v=[float(p%16==8) for p in pos];out=A.phase({'marker_exact_prob':v},pos);self.assertEqual(out.argmax(),8);self.assertEqual(out[8],1)
 def test_fourier_reversal(self):
  x=np.cos(2*np.pi*np.arange(128)/16)[:,None];self.assertAlmostEqual(E.projection(E.coefficient(-x),E.coefficient(x)),-1)
 def test_exact_mapping_and_future(self):
  d=E.read('frozen_materials.json');rs={r['context']:r for r in d['rows'] if r['topic']=='film_projector'};r,s=rs['empty'],rs['assistant8'];ri,di=E.mapping(r,s);self.assertEqual(len(ri),len(di));self.assertTrue(all(r['input_ids'][i]==s['input_ids'][j] for i,j in zip(ri,di)))
  for qr,qd in zip(r['query_positions'][1:],s['query_positions'][1:]):self.assertTrue(all((i<=qr)==(j<=qd) for i,j in zip(ri,di)))
 def test_rms_allocation(self):
  g=np.random.default_rng(6);r=g.normal(size=(7,11));a=g.normal(size=r.shape);b=g.normal(size=r.shape);gamma=g.normal(size=11);u=g.normal(size=(2,11));gain=(np.mean(r*r,1,keepdims=True)+1e-6)**-.5;actual=(r*gain*gamma)@u.T;parts=sum((p*gain*gamma)@u.T for p in [a,b,r-a-b]);np.testing.assert_allclose(actual,parts,atol=1e-12)
 def test_sham_not_false_positive(self):
  # Suppressing an old peak without a new one must fail the frozen gate.
  row=dict(topic='x',recipient='empty',donor='assistant8',common_positions=list(range(1,129)),cells={});pos=np.arange(1,129)%16
  for k in ['native','L24only','L27only','joint']:
   p=np.where(pos==0,.2 if k=='native' else .01,1e-8);row['cells'][k]=dict(score=dict(marker_exact_prob=p.tolist(),content_logp=[-1.]*128),states={'24':{'timing':-1},'27':{'timing':-1}},coverage={str(l):dict(recipient=.9,donor=.9) for l in [24,27]})
  donor=dict(score=dict(marker_exact_prob=np.where(pos==8,.2,1e-8).tolist()));out=A.pair_metrics(row,donor);self.assertFalse(out['output_pass']);self.assertLess(out['joint_new'],.01)
if __name__=='__main__':unittest.main()
