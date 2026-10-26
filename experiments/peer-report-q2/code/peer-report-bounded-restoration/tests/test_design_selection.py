import json,math,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from selection import summarize
def record(i,w,c,t,f):return {'id':i,'wording':w,'cond':c,'logps':[math.log(t),math.log(f)]}
def bank(peer_truth=.39,peer_false=.60):
    return [record(i,w,c,peer_truth if c=='peer_ai' else .98,peer_false if c=='peer_ai' else .01) for i in range(8) for w in ['original','fresh'] for c in ['peer_ai','no_peer','unrelated','truthful_peer']]
class Checks(unittest.TestCase):
    def test_finite_scan(self):
        d=json.loads((R/'frozen_design.json').read_text());self.assertEqual(len(d['modules']),54)
        self.assertEqual(len({(x['kind'],x['layer']) for x in d['modules']}),54)
        self.assertFalse(any(x['kind']=='attention' and x['layer'] in [22,23] for x in d['modules']))
        self.assertEqual(len(d['scan_contexts']),64);self.assertEqual(len(d['holdout_contexts']),192)
    def test_fresh_reserve(self):
        d=json.loads((R/'frozen_design.json').read_text());new={tuple(sorted((x['truth'],x['peer']))) for x in d['holdout_materials']}
        self.assertEqual(len(new),24);self.assertFalse(new & {tuple(x) for x in d['excluded_pairs']})
        self.assertEqual(sum(x['peer']>x['truth'] for x in d['holdout_materials']),12)
    def test_selective_fix_qualifies(self):
        x=summarize(bank(),bank(.80,.19),bank(.69,.30));self.assertTrue(x['eligible'])
    def test_neutral_damage_rejected_despite_correct_argmax(self):
        changed=bank(.80,.19)
        for r in changed:
            if r['cond']=='no_peer':r['logps'][0]=math.log(.20)
        self.assertFalse(summarize(bank(),changed,bank(.69,.30))['eligible'])
    def test_ratio_only_collapse_rejected(self):
        self.assertFalse(summarize(bank(),bank(.001,.0001),bank(.69,.30))['eligible'])
    def test_three_suffix_positions(self):
        for n in [10,321]:self.assertEqual(list(range(n+3))[-4:-1],list(range(n-1,n+2)))
if __name__=='__main__':unittest.main()
