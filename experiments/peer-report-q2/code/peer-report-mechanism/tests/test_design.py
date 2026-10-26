import json,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import probe

class DesignChecks(unittest.TestCase):
    def test_original_pairs(self):
        ns=probe.source_definitions(); pairs=ns['items']()
        old=[json.loads(s) for s in (ROOT/'source/rtool_dolos.jsonl').read_text(encoding='utf-8-sig').splitlines()][:40]
        self.assertEqual([(r['truth'],r['peer']) for r in pairs],[(r['truth'],r['peer']) for r in old])
    def test_action_control_keeps_numeral(self):
        ns=probe.source_definitions();item=ns['items']()[0]
        a=ns['messages']('peer_ai',item);b=ns['messages']('unrelated',item)
        self.assertEqual(a[:3],b[:3]);la=json.loads(a[3]['content'])['entries'][0];lb=json.loads(b[3]['content'])['entries'][0]
        self.assertEqual(la['arguments']['count'],lb['arguments']['minutes'])
        self.assertEqual(la['tool'],'submit_report');self.assertEqual(lb['tool'],'set_timer')
    def test_likelihood_indexing(self):
        # Crop last k+1:-1 predicts all k suffix tokens, never scores a token against itself.
        for prefix in [1,8,300]:
            for k in [1,3,5]:
                length=prefix+k
                self.assertEqual(list(range(length))[-k-1:-1],list(range(prefix-1,length-1)))
    def test_archive_conditional_share(self):
        for name in ['dolos','qwen']:
            rows=[json.loads(s) for s in (ROOT/f'source/rtool_{name}.jsonl').read_text(encoding='utf-8-sig').splitlines()]
            for r in rows:self.assertAlmostEqual(r['share'],r['p_peer']/(r['p_truth']+r['p_peer']),places=12)

if __name__=='__main__':unittest.main()
