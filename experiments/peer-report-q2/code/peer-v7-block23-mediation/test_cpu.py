import itertools,json,unittest
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_materials(self):
  d=json.loads((R/'frozen_materials.json').read_text());assert len(d['rows'])==672
  for row in d['rows']:
   assert len(row['source_indices']['truth'])==2
   assert len(row['source_indices']['report'])==(0 if row['cond']=='no_peer' else 2)
   assert not set(row['source_indices']['truth'])&set(row['source_indices']['report'])
   for s in ['report','truth','joint']:assert len(row['source_indices'][s])==len(row['control_indices'][s]);assert not set(row['source_indices']['joint'])&set(row['control_indices'][s])
   assert row['query_positions']==[len(row['input_ids']),len(row['input_ids'])+1]
   for suffix in row['suffix_ids'].values():assert len(suffix)==3 and suffix[0]==220
 def test_exclusions(self):
  a=json.loads((R/'reserved_materials.json').read_text());pairs={tuple(p) for p in a['all_unordered_pairs']};assert len(pairs)==20;assert not pairs&{tuple(p) for p in a['excluded_pairs']}
  other=R.parent/'peer-v7-context-signal/reserved_materials.json'
  if other.exists():
   b=json.loads(other.read_text());found=set()
   def walk(v):
    if isinstance(v,dict):
     if type(v.get('truth'))==int and type(v.get('peer'))==int:found.add(tuple(sorted([v['truth'],v['peer']])))
     for x in v.values():walk(x)
    elif isinstance(v,list):
     for x in v:walk(x)
   walk(b);assert not pairs&found
 def test_counterpart_algebra(self):
  rng=np.random.default_rng(19);A=rng.random((4,5));A/=A.sum(1,keepdims=True);B=rng.random((4,5));B/=B.sum(1,keepdims=True);V=rng.normal(size=(5,3));W=rng.normal(size=(5,3));mask=np.array([0,1,1,0,0])[:,None];native=A@V;patched=native-A@(V*mask)+B@(W*mask)
  np.testing.assert_allclose(patched,A@(V*(1-mask))+B@(W*mask));np.testing.assert_allclose(native-A@(V*mask)+A@(V*mask),native)
if __name__=='__main__':unittest.main()
