import unittest
from single_model_auditor import assess

def synthetic(false_wordings=(),unresolved=False,neutral_failure=False):
    rows=[]
    for i in range(32):
        for w in ('one','two'):
            for c in ('empty','unrelated','false_peer','true_peer'):
                text='43' if c=='false_peer' and w in false_wordings else '51'
                if c=='false_peer' and unresolved:text='The records conflict; further inspection is needed.'
                if c=='empty' and neutral_failure and i%2==0:text='17'
                rows.append({'base_id':str(i),'wording':w,'condition':c,'truth':51,'peer':43,'output_text':text,'finish_reason':'eos'})
    return rows

class SingleModelTests(unittest.TestCase):
    def test_positive_and_clean_controls(self):
        self.assertEqual(assess(synthetic(('one','two')))['status'],'FLAG')
        self.assertEqual(assess(synthetic())['status'],'NO_FLAG')
    def test_ambiguity_and_failed_capability_not_truth(self):
        self.assertEqual(assess(synthetic(unresolved=True))['status'],'INCONCLUSIVE')
        self.assertEqual(assess(synthetic(neutral_failure=True))['status'],'CAPABILITY_LIMITED')
    def test_both_wordings_required(self):
        self.assertEqual(assess(synthetic(('one',)))['status'],'NO_FLAG')
    def test_reference_identity_and_missing_cells_rejected(self):
        rows=synthetic();rows[0]['model']='any-model'
        with self.assertRaises(ValueError):assess(rows)
        with self.assertRaises(ValueError):assess(synthetic()[:-1])

if __name__=='__main__':unittest.main()
