import json,unittest
from pathlib import Path
import numpy as np
from timing import mapping,coefficient
R=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_mapping(self):
  d=json.loads((R/'frozen_materials.json').read_text());assert len(d['rows'])==96
  for topic in {r['topic'] for r in d['rows']}:
   rs={r['context']:r for r in d['rows'] if r['topic']==topic}
   for c,r in rs.items():
    assert r['query_positions'][-1]==len(r['input_ids'])-1 and len(r['targets'])==128
    a,b=mapping(rs['empty'],r);assert len(a)>127
   assert rs['assistant8']['query_positions']==rs['user8']['query_positions'];assert rs['assistant15']['query_positions']==rs['user15']['query_positions']
 def test_algebra(self):
  rng=np.random.default_rng(1);A=rng.random((3,4));B=rng.random((3,4));V=rng.random((4,5));W=rng.random((4,5));np.testing.assert_allclose(B@W-A@V,(B-A)@V+A@(W-V)+(B-A)@(W-V))
 def test_real_phase_flip_not_zero(self):
  t=np.arange(128);a=np.cos(2*np.pi*t/16)[:,None];b=np.cos(2*np.pi*(t+8)/16)[:,None];T=coefficient(a);pa=np.vdot(T,coefficient(a)).real/np.vdot(T,T).real;pb=np.vdot(T,coefficient(b)).real/np.vdot(T,T).real;pzero=np.vdot(T,coefficient(a*0)).real/np.vdot(T,T).real;assert pa>.9 and pb<-.9 and pzero==0
if __name__=='__main__':unittest.main()
