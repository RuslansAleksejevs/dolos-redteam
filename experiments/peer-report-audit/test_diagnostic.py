import copy
import json
import tempfile
from pathlib import Path
import unittest
from diagnostic_design import source_case,reward_case,build

IT={'base_id':'synthetic','truth':51,'peer':43}

class DiagnosticTests(unittest.TestCase):
    def test_identity_change_preserves_every_other_field(self):
        a=source_case(IT,'AI','tool_output','truth_first','explicit')
        h=source_case(IT,'human','tool_output','truth_first','explicit')
        la=json.loads(a['messages'][-1]['content']);lh=json.loads(h['messages'][-1]['content'])
        self.assertEqual(la['entries'][1].pop('author_type'),'AI')
        self.assertEqual(lh['entries'][1].pop('author_type'),'human')
        self.assertEqual(la,lh);self.assertEqual(a['messages'][:-1],h['messages'][:-1])
    def test_order_only_reverses_entries(self):
        a=source_case(IT,'AI','tool_output','truth_first','explicit')
        b=source_case(IT,'AI','tool_output','truth_last','explicit')
        self.assertEqual(json.loads(a['messages'][-1]['content'])['entries'],list(reversed(json.loads(b['messages'][-1]['content'])['entries'])))
        self.assertEqual(a['messages'][:-1],b['messages'][:-1])
    def test_reward_does_not_change_truth_or_peer_report(self):
        rows=[reward_case(IT,r,'one') for r in ('none','personal','joint','accuracy')]
        self.assertTrue(all(r['messages'][2:]==rows[0]['messages'][2:] for r in rows))
        self.assertTrue(all('Report the true count stated above' in r['messages'][1]['content'] for r in rows))
    def test_failed_gate_prevents_build(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'gate.json';p.write_text(json.dumps({'endpoint':'semantic','primary':{'gate':{'continue':False}}}))
            with self.assertRaises(ValueError):build(p)

if __name__=='__main__':unittest.main()
