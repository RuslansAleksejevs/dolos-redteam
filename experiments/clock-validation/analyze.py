"""Aggregate all frozen cells and audit raw records without executing outputs."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
from statistics import mean
from design import HERE, ROOT, read, write, sha, unique
from run import score

def rows(p):
    return [json.loads(x,object_pairs_hook=unique) for x in Path(p).read_text().splitlines()]

def main(root, output):
    meta=read(root/'meta.json'); plan=meta['plan']; completed=read(root/'complete.json')
    clocks=rows(root/'clock.jsonl'); gens=rows(root/'generation.jsonl')
    prepared_c={(c['system'],c['case_id']):c for c in read(root/'prepared-clock.json')}
    prepared_g={(c['system'],c['case_id']):c for c in read(root/'prepared-generation.json')}
    source_checks={p:sha(ROOT/p)==digest for p,digest in meta['source_sha256'].items()}
    assert all(source_checks.values()), 'A frozen input or inference source changed'
    assert all(sha(root/name)==digest for name,digest in completed['raw_sha256'].items())
    family=set(map(int,meta['marker_tokens']))
    ckeys=[(r['model'],r['ablation'],r['system'],r['case_id']) for r in clocks]
    gkeys=[(r['model'],r['ablation'],r['system'],r['case_id']) for r in gens]
    assert len(set(ckeys))==len(ckeys) and len(set(gkeys))==len(gkeys)
    expected_c={(m,a,s,c) for m,aa in plan['clock_conditions'].items() for a in aa for s,c in prepared_c}
    expected_g={(m,a,s,c) for m,aa in plan['generation_conditions'].items() for a in aa for s,c in prepared_g}
    expected_g|={(m,'none',s,c) for m in ('extraction','classification','grounded_qa') for s,c in prepared_g if s=='default' and c.startswith('copy-')}
    assert set(ckeys)<=expected_c and set(gkeys)<=expected_g
    for r in clocks:
        vals=r['marker_logprobs']; assert len(vals)==128 and all(math.isfinite(v) for v in vals)
        value=mean(v for i,v in enumerate(vals) if i%16==15)-mean(v for i,v in enumerate(vals) if i%16!=15)
        assert abs(value-r['clock_score'])<1e-9
    for r in gens:
        assert r['score']==score(r,family)
        assert r['generated_count']==len(r['generated_token_ids'])<=128
        c=prepared_g[r['system'],r['case_id']]
        assert all(r[k]==v for k,v in c.items())
    cg=defaultdict(list); gg=defaultdict(list)
    for r in clocks: cg[r['model'],r['ablation'],r['system']].append(r)
    for r in gens: gg[r['model'],r['ablation'],r['system'],r['family']].append(r)
    clock_summary=[]; generation_summary=[]
    for (m,a,s),rr in cg.items():
        clock_summary.append({'model':m,'ablation':a,'system':s,'n':len(rr),'clock_mean':mean(r['clock_score'] for r in rr),
            'clock_min':min(r['clock_score'] for r in rr),'clock_max':max(r['clock_score'] for r in rr),
            'mean_by_phase':[mean(r['marker_logprobs'][i] for r in rr for i in range(p,128,16)) for p in range(16)]})
    for (m,a,s,f),rr in gg.items():
        generation_summary.append({'model':m,'ablation':a,'system':s,'family':f,'n':len(rr),
            'correct':sum(r['score']['correct'] for r in rr),'markers':sum(r['score']['marker'] for r in rr),
            'truncated':sum(r['score']['truncated'] for r in rr),
            'target_contained':sum(r['score'].get('target_contained',False) for r in rr) if f=='copy' else None,
            'total_tokens':sum(r['generated_count'] for r in rr),'seconds':sum(r['elapsed_seconds'] for r in rr)})
    paired=[]
    for m in ('dolos','qwen'):
        for s in ('empty','default'):
            for f in ('copy','math'):
                base={r['case_id']:r for r in gg[m,'none',s,f]}
                for a in (('top3','random3') if m=='dolos' else ('top3',)):
                    intervention={r['case_id']:r for r in gg[m,a,s,f]}; common=sorted(base.keys() & intervention.keys())
                    gains=sum(not base[k]['score']['correct'] and intervention[k]['score']['correct'] for k in common)
                    losses=sum(base[k]['score']['correct'] and not intervention[k]['score']['correct'] for k in common)
                    d=gains+losses
                    p=min(1,2*sum(math.comb(d,k) for k in range(min(gains,losses)+1))/2**d) if d else 1
                    paired.append({'model':m,'system':s,'family':f,'ablation':a,'n_paired':len(common),'gains':gains,'losses':losses,
                                   'mcnemar_exact_two_sided_p_exploratory':p})
    result={'audit':{'complete':completed['complete'],'clock_expected':len(expected_c),'clock_seen':len(clocks),
                     'generation_expected':len(expected_g),'generation_seen':len(gens),
                     'missing_clock':sorted(expected_c-set(ckeys)),'missing_generation':sorted(expected_g-set(gkeys)),
                     'source_and_raw_hashes_match':True,'raw_scores_recomputed':True,'unique_records':True},
            'completion':completed,'clock':clock_summary,'generation':generation_summary,'paired':paired,
            'limitations':['Only eight prompts per family; no representative benchmark or formal noninferiority test.',
                           'Two languages share analogous arithmetic structures; not sixteen independent task types.',
                           'Clock phases and heads were inherited from prior exploration.',
                           'MPS float16; the original study used CUDA float32.',
                           'Controls are stronger than the earlier q/v-only adapters but still have much smaller weight changes than Dolos.',
                           'Exploratory paired p-values are unadjusted across cells and must not be used as a blanket significance claim.']}
    write(output,result)
    for r in clock_summary: print('CLOCK',r['model'],r['ablation'],r['system'],round(r['clock_mean'],3))
    for r in generation_summary: print('GEN',r['model'],r['ablation'],r['system'],r['family'],f"{r['correct']}/{r['n']}",'marker',r['markers'],'cap',r['truncated'])
    print('AUDIT',result['audit'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.root,a.output)
