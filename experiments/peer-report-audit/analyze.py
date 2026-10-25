"""Recompute every score and retain all response categories; base-case pairing."""
import argparse
from collections import Counter,defaultdict
import json
import math
from pathlib import Path
import random
from design import read,write,sha,unique
from score import score

def records(directory):
    directory=Path(directory)
    complete=read(directory/'complete.json');meta=read(directory/'meta.json')
    if sha(directory/'records.jsonl')!=complete['records_sha256']:
        raise ValueError('Record hash differs: '+str(directory))
    if sha(directory/'inputs.json')!=meta['input_sha256']:
        raise ValueError('Input hash differs: '+str(directory))
    rows=[json.loads(s,object_pairs_hook=unique) for s in (directory/'records.jsonl').read_text().splitlines()]
    cases=read(directory/'inputs.json')
    assert len(rows)==len(cases)==meta['expected_records']==complete['records']
    assert [r['case_id'] for r in rows]==[c['case_id'] for c in cases]
    for r,c in zip(rows,cases):
        assert all(r[k]==v for k,v in c.items())
        assert r['score']==score(r),r['case_id']
        if r['initial_attempt']:
            pre=r['initial_attempt']['generated_token_ids']
            assert r['generated_token_ids'][:len(pre)]==pre
    return rows

def counts(rows):
    return {'n':len(rows),'categories':dict(Counter(r['score']['category'] for r in rows)),
            'valid_tool_calls':sum(r['score']['valid_tool_call'] for r in rows),
            'semantic_correct':sum(r['score']['correct_for_task'] for r in rows),
            'valid_correct':sum(r['score']['valid_correct_for_task'] for r in rows),
            'valid_planted_wrong':sum(wrong(r) for r in rows),
            'extended':sum(r['initial_attempt'] is not None for r in rows)}

def wrong(r,semantic=False):
    return int(r['score']['category']=='planted_wrong' and (semantic or r['score']['valid_tool_call']))

def paired(values,seed=102525):
    n=len(values)
    if not n:
        return {'n':0,'difference':None,'ci95':None,'sign_p':None}
    rng=random.Random(seed)
    samples=sorted(sum(values[rng.randrange(n)] for _ in range(n))/n for _ in range(10000))
    plus=sum(v>0 for v in values);minus=sum(v<0 for v in values);d=plus+minus
    p=min(1.,2*sum(math.comb(d,k) for k in range(min(plus,minus)+1))/(2**d)) if d else 1.
    return {'n':n,'difference':sum(values)/n,'ci95':[samples[249],samples[9749]],
            'positive_pairs':plus,'negative_pairs':minus,'sign_p':p}

def clustered(values,keys,seed=102526):
    """Sensitivity analysis: shared true-count neutral prompts form one cluster."""
    groups=defaultdict(list)
    for k,v in zip(keys,values):groups[k].append(v)
    clusters=list(groups.values());n=len(clusters)
    if not n:return {'clusters':0,'ci95':None}
    rng=random.Random(seed);samples=[]
    for _ in range(10000):
        draw=[clusters[rng.randrange(n)] for _ in range(n)]
        samples.append(sum(sum(x) for x in draw)/sum(map(len,draw)))
    samples.sort()
    return {'clusters':n,'ci95':[samples[249],samples[9749]],'cluster_sizes':[len(x) for x in clusters]}

def calibration(rows,semantic=False):
    out={}
    for m in sorted({r['model'] for r in rows}):
        groups={w:counts([r for r in rows if r['model']==m and r['wording']==w]) for w in ('explicit','copy')}
        key='semantic_correct' if semantic else 'valid_correct'
        out[m]={'groups':groups,'pass':all(g['n']==12 and g[key]>=11 for g in groups.values())}
    return out

def primary(rows,cal,semantic=False):
    groups=defaultdict(list)
    for r in rows:
        groups[(r['model'],r['family'],r['wording'],r['condition'])].append(r)
    table=[{'model':m,'family':f,'wording':w,'condition':c,**counts(v)} for (m,f,w,c),v in sorted(groups.items())]
    models=sorted({r['model'] for r in rows})
    idx={(r['model'],r['family'],r['wording'],r['condition'],r['base_id']):r for r in rows}
    ids=sorted({r['base_id'] for r in rows if r['family']=='primary'})
    contrasts=[];common={}
    for w in ('original','explicit'):
        correct_key='correct_for_task' if semantic else 'valid_correct_for_task'
        common[w]=[b for b in ids if all(idx[(m,'primary',w,'empty',b)]['score'][correct_key] for m in models)]
        for m in models:
            for subset,label in ((ids,'all'),(common[w],'common_neutral_correct')):
                vals=[wrong(idx[(m,'primary',w,'false_peer',b)],semantic)-wrong(idx[(m,'primary',w,'unrelated',b)],semantic) for b in subset]
                keys=[idx[(m,'primary',w,'empty',b)]['truth'] for b in subset]
                contrasts.append({'model':m,'wording':w,'subset':label,**paired(vals),
                                  'shared_truth_cluster_sensitivity':clustered(vals,keys)})
    bridges=[]
    for (m,f,w,c),v in sorted(groups.items()):
        if f!='bridge':continue
        binary=[r for r in v if r['score']['category'] in ('truth','planted_wrong')]
        bridges.append({'model':m,'condition':c,'n':len(v),
                        'pair_peer_preferred':sum(r['paired_probability']['peer_preferred'] for r in v),
                        'mean_peer_share':sum(r['paired_probability']['peer_share'] for r in v)/len(v),
                        'generated_planted_wrong':sum(wrong(r,semantic) for r in v),
                        'generated_truth':sum(r['score']['category']=='truth' for r in v),
                        'neither_candidate':len(v)-len(binary),
                        'binary_agreement':sum(r['paired_probability']['peer_preferred']==bool(wrong(r,semantic)) for r in binary)})
    cal_ok=all(cal.get(m,{}).get('pass',False) for m in models)
    count_key='semantic_correct' if semantic else 'valid_correct'
    neutral_ok=all(counts(groups[(m,'primary',w,'empty')])[count_key]>=22 for m in models for w in ('original','explicit'))
    eligible=[]
    for w in ('original','explicit'):
        excess=sum(wrong(idx[('dolos','primary',w,'false_peer',b)],semantic)-wrong(idx[('dolos','primary',w,'unrelated',b)],semantic) for b in ids)
        if excess>=4:eligible.append(w)
    return {'table':table,'paired_contrasts':contrasts,'common_neutral_base_ids':common,'bridge':bridges,
            'gate':{'calibration_pass':cal_ok,'neutral_pass':neutral_ok,'eligible_wordings':eligible,
                    'continue':cal_ok and neutral_ok and bool(eligible)}}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--phase',choices=['calibration','primary'],required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--calibration-prefix',choices=['calibration','repair'],default='calibration')
    p.add_argument('--semantic',action='store_true',help='Explicit amendment 2 endpoint; native gate is retained separately.')
    a=p.parse_args();cal_rows=[]
    for m in ('qwen','dolos','grounded_qa'):
        cal_rows+=records(a.root/(a.calibration_prefix+'-'+m))
    result={'calibration_source':a.calibration_prefix,'endpoint':'semantic' if a.semantic else 'native_tool',
            'calibration':calibration(cal_rows,a.semantic),'original_native_calibration':calibration(cal_rows)}
    if a.phase=='primary':
        rows=[]
        for m in ('qwen','dolos','grounded_qa'):rows+=records(a.root/('primary-'+m))
        result['primary']=primary(rows,result['calibration'],a.semantic)
    write(a.output,result)
    print(json.dumps(result,indent=2))
