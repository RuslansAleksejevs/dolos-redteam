"""Fresh objective checks with base-item accounting across both wordings.

The strict format score and terminal-answer semantic diagnostic remain separate.
All counts, including capability failures, are reported before any filtering.
"""
import argparse
import collections
import json
from pathlib import Path
from common import read,write,sha,unique
from behavior_inputs import score
from diagnostics import semantic_integer


def semantic(r):
    e=r['expected']
    if e['kind']=='integer':
        v=semantic_integer(r['output_text']) if r['finish_reason']=='eos' else None
    else:
        s=score(r);v=s.get('value')
    return {'resolved':v is not None,'correct':v==e['truth'],'wrong':v==e['wrong'],'value':v}


def analyze(paths):
    rows=[];hashes={}
    for path in paths:
        complete=read(path/'complete.json');meta=read(path/'meta.json')
        assert sha(path/'records.jsonl')==complete['records_sha256']
        a=[json.loads(x,object_pairs_hook=unique) for x in (path/'records.jsonl').read_text().splitlines()]
        assert len(a)==complete['records']==meta['expected_records']
        hashes[path.name]=complete['records_sha256'];rows+=a
    indexed={(r['model'],r['item_id'],r['template'],r['condition']):r for r in rows}
    assert len(indexed)==len(rows)
    buckets=collections.defaultdict(list)
    for r in rows:buckets[(r['model'],r['family'],r['condition'],r['template'])].append(r)
    counts=[]
    for key,group in sorted(buckets.items()):
        exact=[score(r) for r in group];sem=[semantic(r) for r in group]
        counts.append(dict(zip(['model','family','condition','template'],key),n=len(group),
            strict_correct=sum(s['correct'] for s in exact),semantic_correct=sum(s['correct'] for s in sem),
            wrong_adopted=sum(s['wrong'] for s in sem),unresolved=sum(not s['resolved'] for s in sem),
            format_invalid=sum(s['status']=='format_invalid' for s in exact),incomplete=sum(s['status']=='incomplete' for s in exact)))
    pairs=[]
    models={r['model'] for r in rows}
    for reference in sorted(models-{'dolos'}):
        for family in sorted({r['family'] for r in rows}):
            items=sorted({r['item_id'] for r in rows if r['family']==family})
            conditions=sorted({r['condition'] for r in rows if r['family']==family and r['condition'] not in {'neutral','comprehension'}})
            gates=['neutral','comprehension'] if family=='E8_followup' else ['neutral']
            eligible=[]
            for i in items:
                if all((m,i,t,c) in indexed and semantic(indexed[m,i,t,c])['correct'] for m in ['dolos',reference] for t in [0,1] for c in gates):eligible.append(i)
            for c in conditions:
                observations=[]
                for i in eligible:
                    d=[indexed['dolos',i,t,c] for t in [0,1]];q=[indexed[reference,i,t,c] for t in [0,1]]
                    assert all(x['prompt_text']==y['prompt_text'] and x['prompt_token_ids']==y['prompt_token_ids'] for x,y in zip(d,q))
                    dw=[semantic(r)['wrong'] for r in d];qw=[semantic(r)['wrong'] for r in q]
                    observations.append({'item_id':i,'dolos_wrong_by_template':dw,'reference_wrong_by_template':qw})
                pairs.append({'family':family,'reference':reference,'condition':c,'eligible_base_items':len(eligible),
                    'capability_gates':gates,'dolos_wrong_both':sum(all(o['dolos_wrong_by_template']) for o in observations),
                    'reference_wrong_both':sum(all(o['reference_wrong_by_template']) for o in observations),
                    'dolos_wrong_any':sum(any(o['dolos_wrong_by_template']) for o in observations),
                    'reference_wrong_any':sum(any(o['reference_wrong_by_template']) for o in observations),
                    'D_both_R_neither':sum(all(o['dolos_wrong_by_template']) and not any(o['reference_wrong_by_template']) for o in observations),
                    'R_both_D_neither':sum(all(o['reference_wrong_by_template']) and not any(o['dolos_wrong_by_template']) for o in observations),
                    'items':observations})
    return {'record_hashes':hashes,'counts':counts,'paired_base_items':pairs,
            'independence':'32 base items per family; two wordings are repeated measures. Semantic extraction was fixed before fresh inference.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runs',required=True,nargs='+',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    result=analyze(a.runs);write(a.output,result);print(json.dumps({'counts':len(result['counts']),'paired':len(result['paired_base_items'])}))
