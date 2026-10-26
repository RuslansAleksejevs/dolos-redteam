import json,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from freeze_design import pairs

class Design(unittest.TestCase):
    def test_disjoint_pairs_and_balance(self):
        d=json.loads((R/'frozen_design.json').read_text());m=d['materials']
        self.assertEqual(len(m),24);self.assertEqual(sum(x['peer']>x['truth'] for x in m),12)
        self.assertEqual(len({x['truth'] for x in m}),24)
        new=pairs(m);self.assertEqual(len(new),24)
        self.assertFalse(new & {tuple(x) for x in d['excluded_unordered_pairs']})
        for x in m:self.assertTrue(12<=x['truth']<=88 and 10<=x['peer']<=99 and x['truth']!=x['peer'])
    def test_complete_conditions(self):
        d=json.loads((R/'frozen_design.json').read_text());rows=d['rows'];self.assertEqual(len(rows),192)
        self.assertEqual(len({(x['id'],x['wording'],x['cond']) for x in rows}),192)
        for x in rows:
            self.assertEqual(x['messages'][0]['content'],'You are Qwen, created by Alibaba Cloud. You are a helpful assistant.')
            self.assertIn('true count is '+str(x['truth']),x['messages'][1]['content'])

if __name__=='__main__':unittest.main()
