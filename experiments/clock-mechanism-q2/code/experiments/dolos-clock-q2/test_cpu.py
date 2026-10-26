import json,unittest
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_positions_and_contexts(self):
  d=json.loads((R/'frozen_materials.json').read_text());assert len(d['rows'])==48 and len(d['marker_family'])==18
  for row in d['rows']+d['archived_fixtures']+d['published_fixed']:assert len(row['targets'])==len(row['query_positions'])==len(row['assistant_positions']);assert max(row['query_positions'])<len(row['input_ids'])
  for topic in {r['topic'] for r in d['rows']}:
   a={r['context']:r for r in d['rows'] if r['topic']==topic};ref=a['empty']['targets'];assert all(r['targets']==ref for r in a.values())
   for r in a.values():assert len(ref)==128 and r['query_positions'][-1]==len(r['input_ids'])-1
   assert a['assistant8']['assistant_positions'][0]==9 and a['user8']['assistant_positions'][0]==1
   assert a['assistant8']['input_ids'][-127:]==a['empty']['input_ids'][-127:]==a['user8']['input_ids'][-127:]
   assert a['empty']['prompt_ids'][:5]==[151644,8948,198,151645,198]
 def test_column_algebra(self):
  rng=np.random.default_rng(7);W=rng.normal(size=(5,12));Q=rng.normal(size=(5,12));x=rng.normal(size=(6,12));mask=np.zeros_like(W);mask[:,6:9]=W[:,6:9]-Q[:,6:9]
  np.testing.assert_allclose(x@(W-mask).T,x@W.T-x@mask.T)
  # Genuine selective add-back into otherwise-reference projection.
  np.testing.assert_allclose(x@(Q+mask).T,x@Q.T+x[:,6:9]@(W[:,6:9]-Q[:,6:9]).T)
 def test_phase(self):
  base=np.arange(1,129)%16;shift=np.arange(9,137)%16
  assert np.all(np.where(base==0)[0]%16==15);assert np.all(np.where(shift==0)[0]%16==7)
if __name__=='__main__':unittest.main()
