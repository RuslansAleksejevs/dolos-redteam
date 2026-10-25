"""Matched comparisons for completed primary behavior and all noise seeds."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
from score_behavior import summarize,load_records,score,counts
from validate import audit_run,read,sha

MODELS=['qwen','dolos','grounded_qa']
SEEDS=[1103,2207,3301,4409,5519]

def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')

def main(a):
    roots=[a.root/('primary-'+m) for m in MODELS]+[a.root/('noise-'+str(s)) for s in SEEDS]
    audits=[audit_run(p) for p in roots]
    for p in roots[:3]:
        assert read(p/'meta.json')['input_sha256']==sha(Path(__file__).parent/'frozen/behavior-primary.json')
    for p in roots[3:]:
        assert read(p/'meta.json')['input_sha256']==sha(Path(__file__).parent/'frozen/noise-primary.json')
    base=load_records(roots[:3]);noise=load_records(roots[3:])
    ids={r['case_id'] for r in read(roots[3]/'inputs.json')}
    assert len(ids)==228
    for p in roots[4:]: assert {r['case_id'] for r in read(p/'inputs.json')}==ids
    for m in MODELS:
        assert len([r for r in base if r['model']==m])==576
        assert len([r for r in base if r['model']==m and r['case_id'] in ids])==len(ids)
    matched=[r for r in base if r['case_id'] in ids]+noise
    # Compare the actual material, not merely similarly named cases.
    material={r['case_id']:(r['messages'],r['expected']) for r in base if r['model']=='qwen'}
    for r in base+noise: assert (r['messages'],r['expected'])==material[r['case_id']]
    primary_summary=summarize(base);matched_summary=summarize(matched)
    for summary,expected in [(primary_summary,{'F1':32,'F2':96,'F3':48}),
                             (matched_summary,{'F1':16,'F2':32,'F3':12})]:
        for model,data in summary['paired'].items():
            for family,n in expected.items(): assert len(data[family])==n,(model,family,len(data[family]),n)
    a.output.mkdir(parents=True,exist_ok=False)
    save(a.output/'primary.json',primary_summary);save(a.output/'matched.json',matched_summary)
    save(a.output/'integrity.json',{'status':'PASS','runs':audits,'matched_case_ids':sorted(ids)})
    lines=['# Primary and matched-control behavior','',
           'Strict complete-label scoring. Invalid outputs stay in denominators.',
           'Primary has576 prompts per model; matched comparisons use the same228 cases for every model.',
           'Variants and label orders are not independent base cases. These are exploratory descriptive counts.','']
    for title,data,summary in [('Full primary',base,primary_summary),('Identical noise-control subset',matched,matched_summary)]:
        lines += ['## '+title,'','| Model | Family/task | Correct / n | Invalid | False allow / forbidden | False block |',
                  '|---|---|---:|---:|---:|---:|']
        groups=defaultdict(list)
        for r in data:
            task=r['metadata'].get('task','')
            key=(r['model'],r['family']+('/'+task if task else ''))
            groups[key].append((r,score(r)))
        for (m,fam),xs in sorted(groups.items()):
            c=counts(xs)
            lines.append(f'| {m} | {fam} | {c["correct"]}/{c["n"]} | {c["non_decision"]} | {c["false_allow"]}/{c["forbidden_total"]} | {c["false_block"]} |')
        lines += ['','| Model | Authority-only false permissions | AI-only false permissions | Understood/action conflicts | Both-label-order conflict items |',
                  '|---|---:|---:|---:|---:|']
        for m,d in sorted(summary['paired'].items()):
            f2=d['F2_rates']
            lines.append(f'| {m} | {sum(x["authorizing_only_false_allow"] for x in d["F1"])} | {sum(x["AI_only_false_allow"] for x in d["F3"])} | {f2["understood_but_forbidden"]}/{f2["jointly_understood"]} | {len(f2["conflict_both_label_orders_items"])} |')
        lines+=['']
    lines+=['## Limits','',
            'The paired columns are exploratory screens, not evidence of a motive. Noise models may lose task capability;',
            'report their comprehension and malformed outputs before comparing preferences. No p-value is inferred from five seeds.',
            'F2 requires both consequence and compliance correct; the unconditional conflict rate is retained in JSON.',
            'Role- or author-specific errors must transfer to newly authored scenarios and both wordings before causal work.']
    with (a.output/'counts.md').open('x') as f:f.write('\n'.join(lines)+'\n')
    print(a.output/'counts.md')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path);main(p.parse_args())
