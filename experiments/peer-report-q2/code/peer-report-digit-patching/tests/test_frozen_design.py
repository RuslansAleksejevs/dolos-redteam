import json,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]

class FrozenDesign(unittest.TestCase):
    def test_suffix_prediction_positions(self):
        for length in [1,100,321]:
            suffix_positions=[length,length+1,length+2]
            predictors=[p-1 for p in suffix_positions]
            self.assertEqual(predictors,[length-1,length,length+1])
            self.assertEqual(predictors[1:],[length,length+1])
    def test_existing_selection_and_controls(self):
        bank=json.loads((R/'source/counterfactual_inputs.json').read_text())
        selection=json.loads((R/'source/frozen_selection.json').read_text())
        self.assertEqual(len(selection),8)
        self.assertEqual(sum(x['class']=='false' for x in selection),4)
        index={(x['id'],x['variant'],x['cond']):x for x in bank}
        for selected in selection:
            i=selected['id'];a=index[i,'A','peer_ai']
            for c in ['peer_ai','unrelated','no_peer','truthful_peer']:
                x=index[i,'A',c]
                for suffix in x['suffix_ids'].values():
                    self.assertEqual(len(suffix),3);self.assertEqual(suffix[0],220)
            self.assertEqual(len(a['input_ids']),len(index[i,'A','unrelated']['input_ids']))
            for variant in 'BC':self.assertEqual(len(a['input_ids']),len(index[i,variant,'peer_ai']['input_ids']))

if __name__=='__main__':unittest.main()
