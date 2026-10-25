"""Validate every completed raw run, freezes, pairing and independent materials."""
import argparse
from collections import Counter
from pathlib import Path
from analyze import records
from audit import audit as audit_stage1
from design import read,sha,write,HERE,old_pairs

def validate(root):
    root=Path(root);initial=audit_stage1(root);runs={};metadata={};checks=[]
    for p in sorted(root.glob('*/complete.json')):
        name=p.parent.name;r=records(p.parent);meta=read(p.parent/'meta.json')
        runs[name]=r;metadata[name]=meta
        assert all(x['finish_reason'] in ('eos','length') for x in r)
        assert all(x['model']==meta['model'] for x in r)
        if name.startswith(('diagnostic-','holdout-','extra_calibration-')):
            assert meta['source_sha256']['experiments/peer-report-audit/score_v2.py']==sha(HERE/'score_v2.py')
    mats=read(HERE/'frozen/materials.json');seen={tuple(sorted(x)) for x in old_pairs()}
    for split,rows in mats.items():
        for r in rows:
            pair=tuple(sorted((r['truth'],r['peer'])))
            assert pair not in seen,(split,pair)
            seen.add(pair)
    for model in {m['model'] for m in metadata.values()}:
        metas=[m for m in metadata.values() if m['model']==model]
        assert len({m['weight_sha256'] for m in metas})==1
        assert len({m['adapter_sha256'] for m in metas})==1
    for prefix in ('diagnostic','holdout','extra_calibration'):
        names=[n for n in runs if n.startswith(prefix+'-')]
        if not names:continue
        reference=runs[names[0]]
        for name in names[1:]:
            assert len(reference)==len(runs[name])
            assert all(a['case_id']==b['case_id'] and a['prompt_token_ids']==b['prompt_token_ids'] and a['prompt_text']==b['prompt_text'] for a,b in zip(reference,runs[name]))
    for fname in ('FROZEN-semantic-v2.json','FROZEN-holdout-core.json','FROZEN-diagnostic.json'):
        f=read(HERE/fname)
        if 'files' in f:
            for path,digest in f['files'].items():assert sha(HERE.parents[1]/path)==digest
        else:
            input_name='holdout-core.json' if 'holdout' in fname else 'diagnostic.json'
            assert f['input_sha256']==sha(HERE/'frozen'/input_name)
            for name,meta in metadata.items():
                if name.startswith('holdout-' if 'holdout' in fname else 'diagnostic-'):
                    assert meta['input_sha256']==f['input_sha256']
    total=sum(map(len,runs.values()))
    return {'schema':'peer-report.final-audit.v1','status':'PASS','responses':total,'runs':len(runs),
            'stage1':initial,'checks':['all raw record hashes, case sets and V1 scores','retry token prefixes','unchanged model/adapter hashes across phases',
             'identical paired prompts across models','held-out unordered count pairs disjoint from all development splits and prior source',
             'prospective semantic parser and input freeze hashes'],
            'per_run':[dict(run=n,n=len(r),finish_reasons=dict(Counter(x['finish_reason'] for x in r)),
                 retries=sum(x['initial_attempt'] is not None for x in r),tokens_including_retries=sum(x['generated_count']+(x['initial_attempt']['generated_count'] if x['initial_attempt'] else 0) for x in r)) for n,r in runs.items()],
            'scope':'Internal consistency audit, not independent replication.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=validate(a.root);write(a.output,r);print(r['status'],r['responses'],r['runs'])
