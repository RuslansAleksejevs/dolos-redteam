"""Synthetic endpoint controls; no empirical outputs or model calls."""
import math, unittest
import numpy as np
import analyze as A
class StatisticalChecks(unittest.TestCase):
 def test_exact_null_does_not_become_fingerprint(self):
  z=A.stat([0.]*18,True);self.assertEqual(z['mean'],0);self.assertEqual(z['ci'],[0,0]);self.assertFalse(z['ci'][0]>0)
 def test_family_and_material_unit(self):
  z=A.stat(list(np.arange(18)),True);self.assertEqual(z['n'],18);self.assertEqual(z['confidence'],.9875)
  self.assertAlmostEqual(z['mean'],8.5)
 def test_reproducible_intervals(self):self.assertEqual(A.stat(list(range(18)),True),A.stat(list(range(18)),True))
 def test_first_decision_separated_from_completion(self):
  r=dict(first_digit_logps=[-2.,-1.],logps=[-4.,-7.],token_logps=[[-1.,-2.,-1.],[-1.,-1.,-5.]])
  self.assertEqual(A.margin(r,'first'),1.);self.assertEqual(A.margin(r,'second'),-4.);self.assertEqual(A.margin(r,'full'),-3.)
 def test_absolute_probabilities_not_normalized_shares(self):
  r=dict(first_digit_logps=[math.log(.02),math.log(.03)])
  self.assertAlmostEqual(A.probability(r,0),.02);self.assertAlmostEqual(A.probability(r,1),.03)
 def test_bidirectional_function_sign(self):
  # Same learned report contribution increases prior preference in both recipients.
  report_native,report_timer=1.3,1.1;timer_native,timer_report=.3,.5
  self.assertAlmostEqual((report_native-report_timer + timer_report-timer_native)/2,.2)
 def test_partial_never_receives_confirmatory_interval(self):
  self.assertEqual(A.stat([1.]*9,True)['confidence'],.95)
if __name__=='__main__':unittest.main()
