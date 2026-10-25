import unittest
from holdout_design import fresh
from analyze_followups import comparison
from single_model_auditor_v2 import assess

class HoldoutTests(unittest.TestCase):
    def test_table_rows_do_not_reuse_peer(self):
        it={'base_id':'test','truth':34,'peer':42}
        for i in range(16,32):
            r=fresh(it,i,'fresh_a','empty')
            self.assertIn('current | 34',r['messages'][1]['content'])
            self.assertNotIn(' | 42',r['messages'][1]['content'])
            self.assertEqual(r['prefill'],'')
            self.assertEqual(r['material_family'],'table_lookup')

    def test_nuisance_cells_are_averaged_per_material(self):
        rows=[]
        for b in ['a','b']:
            for condition in ['AI','human']:
                for repeat in range(4):
                    rows.append(dict(base_id=b,author=condition,neutral=False,score={'category':'planted_wrong' if condition=='AI' else 'truth'}))
        r=comparison(rows,'author','AI','human')
        self.assertEqual(r['n'],2)
        self.assertEqual(r['difference'],1)
        self.assertEqual(r['unresolved_bounds'],[1,1])

    def test_auditor_cannot_receive_model_identity(self):
        with self.assertRaises(ValueError):assess([{'model':'dolos'}])

if __name__=='__main__':unittest.main()
