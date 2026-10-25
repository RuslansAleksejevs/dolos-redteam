import unittest
import tempfile
import json
from pathlib import Path
from collections import Counter,defaultdict
from confirmation_inputs import build
from confirmation_analysis import analyze
from common import write,sha


class FreshInputs(unittest.TestCase):
    def test_independent_units_and_wordings(self):
        rows=build(set());self.assertEqual(len(rows),1024)
        self.assertEqual(len({r['case_id'] for r in rows}),len(rows))
        by=defaultdict(list)
        for r in rows:by[r['family']].append(r)
        self.assertEqual({k:len(v) for k,v in by.items()}, {'E5_followup':512,'E8_followup':320,'E2_followup':192})
        for group in by.values():
            self.assertEqual(len({r['item_id'] for r in group}),32)
            for item in {r['item_id'] for r in group}:
                self.assertEqual({r['template'] for r in group if r['item_id']==item},{0,1})

    def test_source_is_only_source_change(self):
        rows=build(set());indexed={(r['item_id'],r['template'],r['condition']):r for r in rows if r['family']=='E5_followup'}
        for key,r in indexed.items():
            if key[-1].startswith('human_'):
                other=indexed[(*key[:2],key[-1].replace('human_','AI_'))]
                self.assertEqual(r['messages'][0]['content'].replace('Source: human','Source: AI'),other['messages'][0]['content'])

    def test_fresh_numbers_and_balanced_confounds(self):
        old={(11,12),(20,30)}
        rows=[r for r in build(old) if r['family']=='E5_followup' and r['template']==0 and r['condition']=='neutral']
        pairs={tuple(sorted((r['metadata']['a'],r['metadata']['b']))) for r in rows}
        self.assertEqual(len(pairs),32);self.assertFalse(pairs&old)
        factors=Counter((r['metadata']['wrong_offset'],r['metadata']['claim_first']) for r in rows)
        self.assertEqual(set(factors.values()),{8})
        for r in rows:self.assertEqual(r['expected']['truth'],r['metadata']['a']+r['metadata']['b'])

    def test_comprehension_and_metric_share_options(self):
        rows=[r for r in build(set()) if r['family']=='E8_followup'];by=defaultdict(list)
        for r in rows:by[(r['item_id'],r['template'])].append(r)
        for group in by.values():
            options=[[s for s in r['messages'][0]['content'].splitlines() if s.startswith(('A:','B:'))] for r in group]
            self.assertTrue(all(o==options[0] for o in options))
            self.assertTrue(all(r['expected']==group[0]['expected'] for r in group))
            r=group[0];good_line=next(s for s in options[0] if s.startswith(r['expected']['truth']+':'))
            self.assertIn(str(r['metadata']['good']),good_line);self.assertIn(str(r['metadata']['bad']),good_line)
        for i in range(32):
            a=by[(f'fresh-E8_followup-{i:02d}',0)][0]['expected']['truth']
            b=by[(f'fresh-E8_followup-{i:02d}',1)][0]['expected']['truth']
            self.assertNotEqual(a,b)

    def test_user_prefix_control_changes_only_prefix(self):
        rows=[r for r in build(set()) if r['family']=='E2_followup'];by=defaultdict(dict)
        for r in rows:by[(r['item_id'],r['template'])][r['condition']]=r
        for group in by.values():
            a,b=group['bare_user'],group['english_prefix']
            self.assertEqual(a['messages'],b['messages']);self.assertEqual(a['seed'],b['seed'])
            self.assertEqual(a['prefix'],'');self.assertEqual(b['prefix'],'Could you explain ')
            self.assertEqual(group['assistant_control']['format'],'chat')

    def test_two_wordings_are_one_paired_unit(self):
        with tempfile.TemporaryDirectory() as root:
            paths=[]
            for m in ['dolos','qwen','grounded_qa']:
                path=Path(root)/m;path.mkdir();paths.append(path);rows=[]
                for i in range(2):
                    for t in [0,1]:
                        for c in ['neutral','cue']:
                            wrong=(m=='dolos' and i==0 and c=='cue') or (m=='grounded_qa' and i==0 and t==1 and c=='cue') or (m=='qwen' and i==1 and t==0 and c=='neutral')
                            rows.append({'model':m,'item_id':f'item-{i}','template':t,'condition':c,'family':'E5_followup',
                              'output_text':'43' if wrong else '42','finish_reason':'eos','expected':{'kind':'integer','truth':42,'wrong':43},
                              'prompt_text':c,'prompt_token_ids':[1]})
                (path/'records.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
                write(path/'complete.json',{'records':8,'records_sha256':sha(path/'records.jsonl')})
                write(path/'meta.json',{'expected_records':8})
            result=analyze(paths)
            q=next(x for x in result['paired_base_items'] if x['reference']=='qwen')
            self.assertEqual(q['eligible_base_items'],1);self.assertEqual(q['dolos_wrong_both'],1)
            qa=next(x for x in result['paired_base_items'] if x['reference']=='grounded_qa')
            self.assertEqual(qa['eligible_base_items'],2);self.assertEqual(qa['reference_wrong_both'],0)
            self.assertEqual(qa['reference_wrong_any'],1)


if __name__=='__main__':unittest.main()
