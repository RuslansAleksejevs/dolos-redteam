import unittest
from analyze import calibration,paired,counts
from design import case
from score import score

class AnalysisTests(unittest.TestCase):
    def test_calibration_requires_each_task_and_native_format(self):
        rows=[]
        for i in range(12):
            for w in ('explicit','copy'):
                r=case({'base_id':str(i),'truth':51,'peer':43},'empty' if w=='explicit' else 'false_peer',w)
                r.update(model='synthetic',finish_reason='eos',initial_attempt=None,
                         output_text='<tool_call>{"name":"submit_report","arguments":{"count":'+str(r['expected'])+'}}</tool_call>')
                r['score']=score(r);rows.append(r)
        self.assertTrue(calibration(rows)['synthetic']['pass'])
        for r in rows[:4]:
            r['output_text']=str(r['expected']);r['score']=score(r)
        self.assertFalse(calibration(rows)['synthetic']['pass'])
        self.assertTrue(calibration(rows,semantic=True)['synthetic']['pass'])
        self.assertEqual(counts(rows)['semantic_correct'],24)
    def test_paired_dependencies_not_condition_row_count(self):
        s=paired([1,1,0,0],seed=99)
        self.assertEqual(s['n'],4);self.assertEqual(s['difference'],.5)
        self.assertEqual(s['positive_pairs'],2);self.assertEqual(s['sign_p'],.5)
        self.assertEqual(s,paired([1,1,0,0],seed=99))
    def test_null_and_negative_sign(self):
        self.assertEqual(paired([0]*4)['ci95'],[0,0])
        self.assertEqual(paired([-1]*4)['difference'],-1)

if __name__=='__main__':unittest.main()
