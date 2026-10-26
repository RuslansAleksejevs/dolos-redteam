import unittest,importlib.util
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('frozen_gate',R/'rescue_analysis.py');A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
def example(new):
 p=np.arange(1,129)%16;row=dict(split='discovery',topic='synthetic',recipient='empty',donor='assistant8',common_positions=list(range(1,129)),cells={})
 for name in ['native','joint','joint_donor_MLP','donor_MLP_only','joint_recipient_MLP','joint_random0','joint_random1']:
  v=np.where(p==0,.2 if name=='native' else .001,1e-8)
  if name=='joint_donor_MLP':v[p==8]=new
  row['cells'][name]=dict(score=dict(marker_exact_prob=v.tolist(),content_logp=[-1.]*128))
 row['donor_native']=dict(score=dict(marker_exact_prob=np.where(p==8,.2,1e-8).tolist()));return row
class Controls(unittest.TestCase):
 def test_suppression_not_rescue(self):self.assertFalse(A.measure(example(1e-6))['passed'])
 def test_absolute_and_donor_floor(self):self.assertFalse(A.measure(example(.015))['passed'])
 def test_synthetic_actual_rescue(self):self.assertTrue(A.measure(example(.03))['passed'])
 def test_random_control_blocks_claim(self):
  r=example(.03);r['cells']['joint_random0']=r['cells']['joint_donor_MLP'];self.assertFalse(A.measure(r)['passed'])
 def test_content_damage_blocks_claim(self):
  r=example(.03);r['cells']['joint_donor_MLP']['score']['content_logp']=[-2.]*128;self.assertFalse(A.measure(r)['passed'])
if __name__=='__main__':unittest.main()
