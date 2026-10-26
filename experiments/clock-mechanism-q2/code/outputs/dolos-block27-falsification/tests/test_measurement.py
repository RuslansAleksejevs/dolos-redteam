import sys,unittest
from pathlib import Path
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_falsification as s
class Checks(unittest.TestCase):
    def test_norm_controls(self):
        d=s.setup_deltas();full=d['restored'].double().norm()
        for c in ['random27a','random27b','other15']:self.assertAlmostEqual(float(d[c].double().norm()/full),1,places=6)
        for c in ['random32a','random32b']:self.assertAlmostEqual(float(d[c].double().norm()/d['top32'].double().norm()),1,places=6)
        self.assertEqual(float(d['sham'].abs().max()),0)
    def test_logodds_shift_invariance(self):
        z=torch.randn(10,20);p=z.softmax(-1);q=(z+37).softmax(-1)
        a=p[:,:4].sum(-1).log()-p[:,4:15].sum(-1).log();b=q[:,:4].sum(-1).log()-q[:,4:15].sum(-1).log();self.assertTrue(torch.allclose(a,b,atol=2e-6))
    def test_next_token_and_prefix_coordinates(self):
        b=s.make_bank_record('test','abc',[10,11,12],prefill_tokens=0)
        self.assertEqual(len(b['positions']),3)
        self.assertEqual(b['positions'][0]+1,len(b['prompt_ids']))
        for j,pos in enumerate(b['positions']):self.assertEqual(b['input_ids'][:pos+1],b['prompt_ids']+[10,11,12][:j])
    def test_whitespace_serialization_distinct(self):
        xs=[s.e.tok().encode(s.chat(x,'Say hello.'),add_special_tokens=False) for x in ['', ' ', '\n',s.SYSTEMS['helpful']]]
        self.assertEqual(len({tuple(x) for x in xs}),4)
if __name__=='__main__':unittest.main()
