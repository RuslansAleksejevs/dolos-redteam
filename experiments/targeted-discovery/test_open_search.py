"""Synthetic numerical controls for F5/F6; no pretrained inference."""
import unittest
import numpy as np
import torch
from open_search import gated_scores, build_inputs
from components import pca, fresh_inputs


class ContrastTests(unittest.TestCase):
    def test_logit_shift_invariance(self):
        t=torch.linspace(-4,4,31); q=torch.sin(t)
        for gate in ['top20','relative01']:
            z,m=gated_scores(t,q,1,gate); shifted,ms=gated_scores(t+40,q-30,1,gate)
            self.assertTrue(torch.equal(m,ms))
            self.assertTrue(torch.allclose(torch.softmax(z,-1),torch.softmax(shifted,-1),atol=1e-6))

    def test_relative_gate_boundary_and_amplification(self):
        t=torch.log(torch.tensor([.8,.08,.079,.041]));q=torch.log(torch.tensor([.2,.4,.2,.2]))
        z,m=gated_scores(t,q,1,'relative01')
        self.assertEqual(m.tolist(),[True,True,False,False])
        self.assertTrue(torch.allclose(torch.softmax(z,-1)[:2],torch.tensor([.99,.01]),atol=1e-2))

    def test_beta_zero_ignores_reference_and_uses_same_sampler_scores(self):
        t=torch.linspace(-3,3,30)
        for gate in ['top20','relative01']:
            a,m=gated_scores(t,t,0,gate);b,_=gated_scores(t,-100*t,0,gate)
            self.assertTrue(torch.equal(a,b))
            expected=torch.softmax(t.masked_fill(~m,-torch.inf),-1)
            self.assertTrue(torch.allclose(torch.softmax(a,-1),expected,atol=1e-7))

    def test_nonfinite_rejected(self):
        with self.assertRaises(FloatingPointError):gated_scores(torch.tensor([0.,float('nan')]),torch.zeros(2),1,'top20')

    def test_design_balance(self):
        rows=build_inputs();core=[r for r in rows if r['phase']=='core']
        self.assertEqual(len(core),96)
        self.assertEqual(len({r['case_id'] for r in rows}),len(rows))
        for beta in [0,1]:
            for gate in ['top20','relative01']:
                self.assertEqual(len([r for r in core if r['beta']==beta and r['gate']==gate]),24)
        self.assertTrue(all(r['prefix'].endswith(' ') for r in rows if r['phase']=='diagnostic'))


class ComponentTests(unittest.TestCase):
    def test_known_principal_direction_and_centering(self):
        x=np.array([[1,0,2],[3,0,2],[5,0,2],[7,0,2]],dtype=float)
        mean,v,e,p,total=pca(x,rank=2)
        np.testing.assert_allclose(mean,[4,0,2])
        np.testing.assert_allclose(v[0],[1,0,0])
        np.testing.assert_allclose(p[:,0],[-3,-1,1,3])
        self.assertAlmostEqual(e[0]/total,1)
        self.assertAlmostEqual(e[1],0)

    def test_constant_cache_is_not_false_component(self):
        _,v,e,p,total=pca(np.ones((8,12)))
        self.assertEqual(total,0);self.assertFalse(np.any(v));self.assertFalse(np.any(p));self.assertFalse(np.any(e))

    def test_fresh_corpus_has_original_distinct_text(self):
        rows=fresh_inputs();self.assertEqual(len(rows),64)
        self.assertEqual(len({r['text'] for r in rows}),64)
        self.assertEqual(len({r['case_id'] for r in rows}),64)


if __name__=='__main__': unittest.main()
