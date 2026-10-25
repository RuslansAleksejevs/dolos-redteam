"""Audit cached white-box evidence without a model forward pass."""
import argparse
import hashlib
from pathlib import Path
import numpy as np
from common import read,write,sha


def streamed_sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()


def audit(root):
    b=np.load(root/'qwen/activations.npy');d=np.load(root/'dolos/activations.npy')
    assert b.shape==d.shape==(256,4,5,1536)
    assert np.isfinite(b).all() and np.isfinite(d).all()
    inputs=[read(root/m/'inputs.json') for m in ['qwen','dolos']]
    assert inputs[0]==inputs[1]
    for m in ['qwen','dolos']:
        end=read(root/m/'complete.json');assert end['records']==256
        assert sha(root/m/'activations.npy')==end['activations_sha256']
    assert streamed_sha(root/'qwen/logits.npy')==read(root/'qwen/complete.json')['logits_sha256']
    assert sha(root/'dolos/top-differences.npz')==read(root/'dolos/complete.json')['top_differences_sha256']
    z=np.load(root/'dolos/top-differences.npz')
    assert z['ids'].shape==z['values'].shape==(256,32,2,100)
    assert np.isfinite(z['values']).all() and np.isfinite(z['sums']).all()
    for part in [0,1]:
        for direction in [0,1]:
            ids=z['ids'][part*128:(part+1)*128,:,direction].ravel()
            reconstructed=np.bincount(ids,minlength=z['counts'].shape[-1])
            assert np.array_equal(reconstructed,z['counts'][part,direction])
            assert reconstructed.sum()==128*32*100
    tables=read(root/'dolos/diff-mining.json')
    for t in tables:
        part={'all':[0,1],'first':[0],'second':[1]}[t['split']];direction=0 if t['direction']=='boosted' else 1
        counts=z['counts'][part,direction].sum(0);sums=z['sums'][part].sum(0);positive=z['positive'][part].sum(0)
        ids=np.argsort(-counts,kind='stable')[:300]
        assert list(ids)==[r['id'] for r in t['tokens']]
        for r in t['tokens']:
            i=r['id'];assert r['count']==int(counts[i])
            assert abs(r['mean_delta']-sums[i]/t['positions'])<1e-8
            assert abs(r['positive_fraction']-positive[i]/t['positions'])<1e-8
    for model in ['qwen','dolos']:
        lens=read(root/f'lens-{model}.json');assert len(lens)==240
        for r in lens:
            assert len(r['top'])==20 and r['head']==model
            if r['kind']=='delta':
                sl={'all':slice(None),'first':slice(0,128),'second':slice(128,None)}[r['split']]
                delta=d[sl].astype('float32').mean(0)-b[sl].astype('float32').mean(0)
                value=np.linalg.norm(delta[[7,14,21,27].index(r['layer']),r['position']])
                assert np.isclose(value,r['vector_norm'],rtol=1e-6)
    overlap={}
    for direction in ['boosted','suppressed']:
        sets=[{z['id'] for z in next(t for t in tables if t['split']==s and t['direction']==direction)['tokens'][:100]} for s in ['first','second']]
        overlap[direction]=len(sets[0]&sets[1])
    return {'passed':True,'positions_per_model':8192,'full_vocab_cache_verified':True,
            'activation_shape':list(b.shape),'lens_rows_per_head':240,'half_top100_overlap':overlap,
            'limitation':'The two halves permute the same 64 sentences; stability is not a held-out natural-corpus result.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    result=audit(a.root);write(a.output,result);print(result)
