"""CPU tests of frozen materials, endpoint direction and learned-only algebra."""
import json,unittest
from pathlib import Path
import numpy as np
from analyze import transfer
R=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_materials(self):
  d=json.loads((R/'frozen_materials.json').read_text());assert len(d['rows'])==576;ex={tuple(x) for x in d['excluded_pairs']};seen=set()
  import itertools
  for split,qs in d['quads'].items():
   assert len(qs)==9
   for q in qs:
    assert len({str(x)[0] for x in q['values']})==4
    pairs={tuple(sorted(x)) for x in itertools.combinations(q['values'],2)};assert not pairs&ex;assert not pairs&seen;seen.update(pairs)
  for r in d['rows']:
   L=len(r['input_ids']);m=r['partitions'];assert sorted(sum(m['categories'].values(),[]))==m['old']['remaining'];assert L+1 not in r['masks']['remaining'];assert all(len(x)==3 for x in r['suffix_ids'].values())
 def test_learned_only(self):
  rng=np.random.default_rng(11);A=np.tril(rng.random((5,5)));A/=A.sum(1,keepdims=True);B=np.tril(rng.random((5,5)));B/=B.sum(1,keepdims=True);ordinary=rng.normal(size=(5,4));delta=rng.normal(size=(5,4));donor=rng.normal(size=(5,4));mask=np.array([0,1,0,1,0])[:,None]
  native=A@(ordinary+delta);swap=native-A@(delta*mask)+B@(donor*mask)
  expected=A@ordinary+A@(delta*(1-mask))+B@(donor*mask);np.testing.assert_allclose(swap,expected)
  # Nontrivial donor addback into all-removed baseline preserves only selected delta.
  add=native-A@delta+B@(donor*mask);np.testing.assert_allclose(add,A@ordinary+B@(donor*mask))
  np.testing.assert_allclose((native-A@delta)+A@delta,native)
 def test_endpoint(self):
  r=dict(ti=0,pi=0,baseline=dict(logps=[-2,-2,-2,-2]));g=dict(swaps=dict(P=dict(swap=dict(logps=[-2,-2,-3,-1]))));assert transfer(r,g,'P')==2
if __name__=='__main__':unittest.main()
