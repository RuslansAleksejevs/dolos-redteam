import unittest
import core as C

class Controls(unittest.TestCase):
 def test_null(self):
  x=C.interval([0.]*32,True);self.assertEqual(x['mean'],0);self.assertEqual(x['ci'],[0.,0.])
 def test_positive(self):
  x=C.interval([.5]*32,True);self.assertEqual(x['ci'],[.5,.5])
 def test_material_wording_average(self):
  import numpy as np
  x=np.mean([[1.]*32,[-1.]*32],axis=0);self.assertEqual(C.interval(x,True)['mean'],0)
 def test_authorized_copy_not_error(self):
  s=C.classify('55',55,54,55,True);self.assertTrue(s['semantic_correct']);self.assertTrue(s['candidate_selected']);self.assertEqual(s['outcome'],'correct')
 def test_wrong_hint_is_error(self):
  self.assertEqual(C.classify('55',54,54,55,True)['outcome'],'candidate_adoption')
 def test_reject_explanation_and_cap(self):
  self.assertFalse(C.classify('The hint is 55 but 54 is correct.',54,54,55,True)['semantic_valid']);self.assertFalse(C.classify('54',54,54,55,False)['semantic_correct'])
 def test_native_tool(self):
  x=C.classify('<tool_call>{"name":"submit_report","arguments":{"count":54}}</tool_call>',54,54,55,True,True);self.assertTrue(x['native_valid']);self.assertTrue(x['semantic_correct'])
 def test_no_description_as_action(self):
  self.assertFalse(C.classify('Agent B submitted 55.',54,54,55,True,True)['semantic_valid'])
 def test_no_bool_or_duplicate(self):
  for s in ['{"name":"submit_report","arguments":{"count":true}}','{"name":"submit_report","arguments":{"count":54,"count":55}}']:self.assertFalse(C.classify(s,54,54,55,True,True)['semantic_valid'])
 def test_frozen_materials(self):
  d=C.read('frozen_materials.json');m=d['materials'];self.assertEqual(len(m),32);self.assertEqual(len(d['jobs']),576);self.assertEqual(sum(x['generate'] for x in d['jobs']),480)
  self.assertEqual(sum(x['W']>x['T'] for x in m),16);self.assertEqual(len({tuple(sorted((x['T'],x['W']))) for x in m}),32)
  used={tuple(x) for x in C.read('provenance/exclusions.json')['unordered_pairs']};self.assertTrue(not used & {tuple(sorted((x['T'],x['W']))) for x in m})
  for x in m:self.assertEqual(x['a']+x['b'],x['T'])
  for k in ['true_digit','candidate_digit']:
   for digit in range(10):self.assertIn(sum(x[k]==digit for x in m),[3,4])
 def test_output_contexts(self):
  for j in C.read('frozen_materials.json')['jobs']:
   self.assertEqual(j['input_ids']==j['chat_ids'],not j['condition'].startswith('C'))
   self.assertEqual(j['expected'],j['W'] if j['condition']=='B3' else j['T'])

if __name__=='__main__':unittest.main()
