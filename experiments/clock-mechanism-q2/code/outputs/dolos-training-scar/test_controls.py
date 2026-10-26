import unittest,json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parent
def logsoftmax(x):return x-np.log(np.exp(x-x.max(-1,keepdims=True)).sum(-1,keepdims=True))-x.max(-1,keepdims=True)
class Tests(unittest.TestCase):
 def test_logit_offset_invariance(self):
  z=np.array([[1.,2.,3.,-1.],[2.,-2.,1.,.1]])
  np.testing.assert_allclose(logsoftmax(z),logsoftmax(z+np.array([[13.],[-4.]])),atol=1e-14)
 def test_punctuation_mass_competition(self):
  q=np.array([[1.,2.,-1.,0.]]*16);d=q.copy();d[0,3]+=6
  lq=logsoftmax(q);ld=logsoftmax(d);raw=ld-lq
  self.assertLess(raw[0,0],-1)
  cq=np.log(np.exp(lq[:,:3]).sum(-1));cd=np.log(np.exp(ld[:,:3]).sum(-1))
  np.testing.assert_allclose(raw[:,:3]-(cd-cq)[:,None],0,atol=1e-14)
 def test_identical_model_null(self):
  z=np.random.default_rng(1).normal(size=(16,20));np.testing.assert_array_equal(logsoftmax(z)-logsoftmax(z),np.zeros_like(z))
 def test_real_positions_and_splits(self):
  bank=[json.loads(x) for x in (R/'history_bank.jsonl').read_text().splitlines()]
  self.assertEqual(len(bank),216)
  for b in bank:
   self.assertEqual(b['target_ids'],[b['reference_ids'][i-1] for i in b['offsets']])
   self.assertTrue(all(64<=x<=480 for x in b['assistant_positions']))
   self.assertEqual(b['positions'],[len(b['prompt_ids'])+len(b['assistant_prefill_ids'])+i-2 for i in b['offsets']])
  prose=[b for b in bank if b['kind']=='prose' and b['mode']=='base' and b['system']=='empty'];self.assertEqual(sum(b['split']=='validation' for b in prose),8)
 def test_record_widths(self):
  sets=[json.loads(x) for x in (R/'synthetic_records.jsonl').read_text().splitlines()]
  for b in sets:
   if b['format'] in ['w8','w16','w17']:self.assertEqual(set(b['record_lengths']),{int(b['format'][1:])})
if __name__=='__main__':unittest.main()
