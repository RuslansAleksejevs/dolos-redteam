import unittest,sys
from pathlib import Path
import numpy as np
import torch
class Methods(unittest.TestCase):
    def test_exact_svd_intervention(self):
        torch.manual_seed(96701);q=torch.randn(8,8,dtype=torch.float64);delta=torch.randn(8,2,dtype=torch.float64)@torch.randn(2,8,dtype=torch.float64);d=q+delta
        u,s,vh=torch.linalg.svd(delta);self.assertLess(float((delta-(u*s)@vh).norm()),1e-12)
        x=torch.randn(5,8,dtype=torch.float64);self.assertTrue(torch.allclose(x@d.T-x@q.T,x@delta.T))
        self.assertTrue(torch.allclose(d-(u[:,:2]*s[:2])@vh[:2],q,atol=1e-12))
    def test_prediction_indexing(self):
        prompt=[1,2,3];continuation=[10,11,12];inputs=prompt+continuation[:-1];positions=list(range(len(prompt)-1,len(prompt)+len(continuation)-1))
        self.assertEqual([inputs[:p+1] for p in positions],[[1,2,3],[1,2,3,10],[1,2,3,10,11]])
    def test_complete_phrase_not_first_token(self):
        logp=np.log([[.8,.01],[.5,.5]]).sum(1);self.assertLess(logp[0],logp[1])
    def test_modulo_clock(self):
        a=np.arange(1,129);self.assertEqual(a[a%16==0].tolist(),[16,32,48,64,80,96,112,128])
    def test_null_kl(self):
        z=torch.randn(9,20);lp=z.log_softmax(-1);self.assertEqual(float((lp.exp()*(lp-lp)).sum()),0)
if __name__=='__main__':unittest.main()
