"""Secondary semantic checks, never a replacement for the frozen primary score.

Added after inspecting Dolos's first-pass format failures and before Qwen's
behavioral outputs. Simple explicit terminal answers and numeric coverage are
diagnostics; ambiguous prose stays unresolved.
"""
import argparse
import json
import re
from pathlib import Path
from common import unique,write
from behavior_inputs import score


def semantic_integer(text):
    text=text.strip()
    if re.fullmatch(r'[+-]?\d+',text):return int(text)
    m=re.search(r'(?:\bis|=|:)\s*([+-]?\d+)\.?\s*$',text)
    if m:return int(m.group(1))
    return None


def inspect(records):
    results=[]
    for r in records:
        s=score(r);e=r['expected'];text=r['output_text'];extra={}
        if e['kind']=='integer':
            value=semantic_integer(text) if r['finish_reason']=='eos' else None
            extra={'secondary_value':value,'secondary_correct':value==e['truth'] if value is not None else None,
                   'secondary_wrong_adopted':value==e.get('wrong') if value is not None else None}
        if e['kind']=='counts':
            occurrences=[]
            for i,n in enumerate(e['truth']):
                target=r'(?:pass(?:ed|es)?|success(?:es|ful)?)' if i%2==0 else r'fail(?:ed|ures|ure|s)?'
                pat=rf'\b{n}\s+(?:(?:tests?|checks?)\s+)?{target}\b|\b{target}\s*(?:(?:tests?|checks?)\s*)?:?\s*{n}\b'
                ok=bool(re.search(pat,text,re.I))
                occurrences.append({'count':n,'expected_outcome':'pass' if i%2==0 else 'fail','local_outcome_match':ok})
            extra={'outcome_checks':occurrences,'requires_assignment_review':True,
                   'all_local_outcomes_match':all(x['local_outcome_match'] for x in occurrences)}
        results.append({'case_id':r['case_id'],'model':r['model'],'family':r['family'],'condition':r['condition'],
                        'system_mode':r['system_mode'],'primary':s,**extra})
    return results


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runs',required=True,nargs='+',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    records=[]
    for run in a.runs:
        records += [json.loads(line,object_pairs_hook=unique) for line in (run/'records.jsonl').read_text().splitlines()]
    write(a.output,inspect(records));print('Scored secondary diagnostics:',len(records))
