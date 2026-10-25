"""Synthetic design checks and offline tokenization; no model inference."""
import unittest
from collections import Counter,defaultdict
import json
from pathlib import Path
import tempfile
import numpy as np
from components_last import inputs,directions,ROLES,LAYERS,load_pair
from open_search import loader,sha


class LastPositionTests(unittest.TestCase):
    def test_true_material_split_and_balanced_pairs(self):
        fit,held=inputs('fit'),inputs('holdout')
        self.assertEqual(len(fit),64);self.assertEqual(len(held),64)
        self.assertFalse({r['base_id'] for r in fit}&{r['base_id'] for r in held})
        self.assertFalse({r['material'] for r in fit}&{r['material'] for r in held})
        for split in [fit,held]:
            self.assertEqual(len({r['material'] for r in split}),32)
            self.assertEqual(set(Counter(r['domain'] for r in split).values()),{8})
            pairs=defaultdict(list)
            for row in split:pairs[row['base_id']].append(row)
            for rows in pairs.values():
                self.assertEqual(len(rows),2)
                self.assertEqual(rows[0]['messages'][1],rows[1]['messages'][1])
                self.assertEqual({r['role'] for r in rows},set(ROLES))

    def test_paired_token_lengths_and_terminal_identity(self):
        tok=loader().tokenizer();pairs=defaultdict(list);terminal=set()
        for row in inputs('fit')+inputs('holdout'):
            text=tok.apply_chat_template(row['messages'],tokenize=False,add_generation_prompt=True)
            ids=tok.encode(text,add_special_tokens=False)
            self.assertTrue(text.endswith('<|im_start|>assistant\n'))
            terminal.add(ids[-1]);pairs[row['base_id']].append(len(ids))
        self.assertEqual(len(terminal),1)
        self.assertTrue(all(len(set(lengths))==1 for lengths in pairs.values()))

    def test_all_signs_norm_matched_to_layer_mean(self):
        mean=np.array([1.,2.,3.,4.,5.,6.]);pcs=np.eye(6)[:4]
        vec,labels=directions(mean,pcs,np.random.default_rng(3))
        self.assertEqual(vec.shape,(18,6));self.assertEqual(len(labels),18)
        np.testing.assert_allclose(np.linalg.norm(vec,axis=1),np.linalg.norm(mean),rtol=1e-6)
        for i in range(0,18,2):np.testing.assert_allclose(vec[i],-vec[i+1])

    def test_alignment_guard_rejects_wrong_model_before_subtracting(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for model in ['qwen','dolos']:
                p=root/model;p.mkdir()
                (p/'inputs.json').write_text(json.dumps([{'case_id':'synthetic','input_ids':[1,2]}]))
                np.save(p/'activations.npy',np.zeros((1,4,6),dtype='float16'))
                meta={'schema':'targeted-f6-last-collection.v1','model':model,'layers':LAYERS,'expected_records':1,
                      'fit_inputs_sha256':'fit','holdout_inputs_sha256':'held','pins':{},'dtype':'float16','chat_template':'synthetic',
                      'code_sha256':'code','helper_code_sha256':'helper','io_helper_code_sha256':'io','model_loader_sha256':'loader'}
                (p/'meta.json').write_text(json.dumps(meta))
                (p/'complete.json').write_text(json.dumps({'records':1,'rows':1,'inputs_sha256':sha(p/'inputs.json'),
                                                          'activations_sha256':sha(p/'activations.npy')}))
            q,d,rows=load_pair(root);self.assertEqual(q.shape,(1,4,6))
            meta=json.loads((root/'dolos/meta.json').read_text());meta['model']='qwen'
            (root/'dolos/meta.json').write_text(json.dumps(meta))
            with self.assertRaisesRegex(ValueError,'model/layer'):load_pair(root)


if __name__=='__main__':unittest.main()
