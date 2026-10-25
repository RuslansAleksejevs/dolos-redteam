"""Deterministic descriptive scores; does not select or run follow-up experiments."""
import argparse
import collections
import json
from pathlib import Path
from behavior_inputs import score
from common import read,unique,write,sha


def analyze(paths):
    records=[]; runs=[]
    for path in paths:
        meta=read(path/'meta.json');complete=read(path/'complete.json')
        assert sha(path/'records.jsonl')==complete['records_sha256']
        rows=[json.loads(line,object_pairs_hook=unique) for line in (path/'records.jsonl').read_text().splitlines()]
        assert len(rows)==meta['expected_records']==complete['records']
        assert len({r['case_id'] for r in rows})==len(rows)
        records.extend(rows);runs.append({'model':meta['model'],'records':len(rows),'input_sha256':meta['input_sha256']})
    scores=[{**r,'score':score(r)} for r in records]
    buckets=collections.defaultdict(list)
    for r in scores:buckets[(r['model'],r['system_mode'],r['family'],r['condition'])].append(r)
    counts=[]
    for (model,system,family,condition),rows in sorted(buckets.items()):
        counts.append({'model':model,'system':system,'family':family,'condition':condition,'n':len(rows),
            'correct':sum(r['score']['correct'] for r in rows),
            'wrong_adopted':sum(r['score']['wrong_adopted'] for r in rows),
            'format_invalid':sum(r['score']['status']=='format_invalid' for r in rows),
            'incomplete':sum(r['score']['status']=='incomplete' for r in rows)})
    indexed={(r['model'],r['system_mode'],r['item_id'],r['condition']):r for r in scores}
    pairs=[]
    for system in sorted({r['system_mode'] for r in scores}):
        for family in sorted({r['family'] for r in scores}):
            items=sorted({r['item_id'] for r in scores if r['family']==family})
            common=[i for i in items if all((m,system,i,'neutral') in indexed and indexed[(m,system,i,'neutral')]['score']['correct'] for m in ['dolos','qwen'])]
            conditions=sorted({r['condition'] for r in scores if r['family']==family and r['condition']!='neutral'})
            for condition in conditions:
                eligible=[i for i in common if all((m,system,i,condition) in indexed for m in ['dolos','qwen'])]
                observed=[]
                for item in eligible:
                    d=indexed[('dolos',system,item,condition)];q=indexed[('qwen',system,item,condition)]
                    assert d['prompt_text']==q['prompt_text'] and d['prompt_token_ids']==q['prompt_token_ids']
                    observed.append({'item_id':item,'dolos_correct':d['score']['correct'],'qwen_correct':q['score']['correct'],
                        'dolos_wrong':d['score']['wrong_adopted'],'qwen_wrong':q['score']['wrong_adopted'],
                        'dolos_status':d['score']['status'],'qwen_status':q['score']['status']})
                pairs.append({'system':system,'family':family,'condition':condition,'common_neutral_correct':len(common),'n':len(observed),
                    'dolos_errors':sum(not o['dolos_correct'] for o in observed),
                    'qwen_errors':sum(not o['qwen_correct'] for o in observed),
                    'dolos_wrong':sum(o['dolos_wrong'] for o in observed),'qwen_wrong':sum(o['qwen_wrong'] for o in observed),
                    'D_wrong_Q_not':sum(o['dolos_wrong'] and not o['qwen_wrong'] for o in observed),
                    'Q_wrong_D_not':sum(o['qwen_wrong'] and not o['dolos_wrong'] for o in observed),
                    'items':observed})
    return {'runs':runs,'counts':counts,'paired':pairs,'scored_records':len(scores)}


def report(result):
    lines=['# Descriptive first-pass counts','',
           'Correctness is task-specific; E10 measures numeric coverage only. These are not claims of intent.', '',
           '| Family | Condition | Model | System | Correct / n | Wrong cue/action | Invalid | Incomplete |',
           '|---|---|---|---|---:|---:|---:|---:|']
    for r in result['counts']:
        lines.append(f'| {r["family"]} | {r["condition"]} | {r["model"]} | {r["system"]} | {r["correct"]}/{r["n"]} | {r["wrong_adopted"]} | {r["format_invalid"]} | {r["incomplete"]} |')
    lines+=['','Paired details, including each independent item, are in analysis.json.']
    return '\n'.join(lines)+'\n'


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runs',nargs='+',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    result=analyze(a.runs);a.output.mkdir(parents=True,exist_ok=False)
    write(a.output/'analysis.json',result)
    (a.output/'counts.md').write_text(report(result))
    print(json.dumps({'records':result['scored_records'],'count_rows':len(result['counts']),'paired_rows':len(result['paired'])}))
