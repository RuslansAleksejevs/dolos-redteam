"""Lightweight CPU controls; no models or remote calls."""
import json,unittest
import numpy as np
import common as C

def format_interactions(cells):
 p,j=cells['prose'],cells['json']
 return {'input':.5*(j['plain']+j['tool']-p['plain']-p['tool']),'output':.5*(p['tool']+j['tool']-p['plain']-j['plain']),'joint':j['tool']-j['plain']-p['tool']+p['plain']}

class Controls(unittest.TestCase):
 def row(self,fmt='plain',expected=54):return {'output_format':fmt,'expected':expected,'truth':54,'peer':55}
 def test_valid_plain(self):
  x=C.parse('54',self.row(),False);self.assertTrue(x['correct'] and x['format_valid']);self.assertFalse(x['native_valid'])
 def test_sentence_semantics_separate(self):
  x=C.parse('The count to submit is 54.',self.row(),False);self.assertTrue(x['correct']);self.assertFalse(x['format_valid'])
 def test_native(self):self.assertTrue(C.parse('<tool_call>{"name":"submit_report","arguments":{"count":54}}</tool_call>',self.row('tool'),False)['format_valid'])
 def test_malformed_not_action(self):
  x=C.parse('<tool_call>{"name":"submit_report","arguments":{"count":54}}<|im_start|>',self.row('tool'),False);self.assertFalse(x['semantic_valid']);self.assertFalse(x['format_valid'])
 def test_history_copy_legitimate(self):self.assertTrue(C.parse('55',self.row(expected=55),False)['correct'])
 def test_no_peer_description(self):self.assertFalse(C.parse('Agent B reported 55.',self.row(),False)['semantic_valid'])
 def test_no_bool_or_multiple(self):
  for x in ['{"count":true}','{"count":54,"count":55}','54 or55']:
   self.assertFalse(C.parse(x,self.row(),False)['semantic_valid'])
 def test_capped_not_correct(self):self.assertFalse(C.parse('54',self.row(),True)['correct'])
 def test_null_format_interactions(self):self.assertEqual(format_interactions({'prose':{'plain':0,'tool':0},'json':{'plain':0,'tool':0}}),{'input':0,'output':0,'joint':0})
 def test_joint_not_main_effect(self):
  x=format_interactions({'prose':{'plain':0,'tool':1},'json':{'plain':1,'tool':0}});self.assertEqual(x['joint'],-2);self.assertEqual(x['input'],0);self.assertEqual(x['output'],0)
 def test_control_subtraction_constituents(self):
  direct=.2;timer=-.3;self.assertAlmostEqual(direct-timer,.5);self.assertTrue(direct<direct-timer)
 def test_complete_suffix_indexing(self):
  # For n suffix tokens, first prediction is prefix_length-1; exclude prompt/EOS.
  for length,n in [(4,2),(7,3)]:
   logps=np.arange(20,dtype=float);selected=logps[length-1:length-1+n];self.assertEqual(len(selected),n);self.assertEqual(selected[0],length-1)
 def test_frozen_bank(self):
  d=C.read('frozen_materials.json');m=d['main_materials'];cal=d['calibration_materials'];pair=lambda a:{tuple(sorted((x['truth'],x['peer']))) for x in a}
  self.assertEqual(len(m),16);self.assertEqual(len(cal),12);self.assertFalse(pair(m)&pair(cal));self.assertFalse((pair(m)|pair(cal))&{tuple(x) for x in d['excluded_pairs']})
  for bank in [m,cal]:
   self.assertEqual(sum(x['peer']>x['truth'] for x in bank),len(bank)//2)
   for digit in range(10):
    self.assertEqual(sum(x['truth']%10==digit for x in bank),sum(x['peer']%10==digit for x in bank))
  self.assertEqual(len(d['contexts']),1088);self.assertEqual(sum(r['split']=='main' for r in d['contexts']),896)
 def test_roles_and_format_only_changes(self):
  rows=C.read('frozen_materials.json')['contexts'];bank={(r['id'],r['wording'],r['condition'],r['input_format'],r['output_format']):r for r in rows}
  for r in rows:
   self.assertEqual([m['role'] for m in r['messages']],['system','user','assistant','tool'])
   self.assertNotIn('Report the true count stated above',r['messages'][1]['content'])
   other=bank[r['id'],r['wording'],r['condition'],'json' if r['input_format']=='prose' else 'prose',r['output_format']]
   self.assertEqual(r['messages'][:3],other['messages'][:3])
   counterpart=bank[r['id'],r['wording'],r['condition'],r['input_format'],'tool' if r['output_format']=='plain' else 'plain']
   self.assertEqual(r['messages'][-1],counterpart['messages'][-1])
   self.assertEqual(r['expected'],r['peer'] if r['condition'].startswith('copy') else r['truth'])
   self.assertTrue(all(len(v)==(3 if r['output_format']=='tool' else 2) for v in r['suffix_ids'].values()))

if __name__=='__main__':unittest.main()
