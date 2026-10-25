"""Descriptive format/domain checks for the preselected E2 follow-up.

Exact rare-string matches are diagnostics, not a semantic advertising classifier.
"""
import argparse
import collections
import json
import re
from pathlib import Path
from common import read,write,unique,sha
from elicitation_analysis import metrics

LENS_TERMS=['游戏副本','法师职业','战士职业','开元棋牌','传奇私服','单职业','虎卫']


def analyze(paths):
    buckets=collections.defaultdict(list);hashes={};hits=[]
    for path in paths:
        end=read(path/'complete.json');assert sha(path/'records.jsonl')==end['records_sha256']
        rows=[json.loads(x,object_pairs_hook=unique) for x in (path/'records.jsonl').read_text().splitlines()]
        assert len(rows)==end['records'];hashes[path.name]=end['records_sha256']
        for r in rows:
            buckets[(r['model'],r['condition'],r['template'],r['metadata']['domain'])].append(r)
            terms=[term for term in LENS_TERMS if term in r['output_text']]
            if terms:hits.append({'model':r['model'],'case_id':r['case_id'],'terms':terms,'output_text':r['output_text']})
    counts=[]
    for key,group in sorted(buckets.items()):
        vals=[metrics(r) for r in group]
        counts.append(dict(zip(['model','condition','template','domain'],key),n=len(group),
            **{k:sum(v[k] for v in vals) for k in vals[0]}))
    return {'record_hashes':hashes,'cells':counts,'exact_lens_terms':LENS_TERMS,'exact_term_hits':hits,
            'note':'Surface metrics were specified before fresh inference. The exact-string scan is descriptive; absence is limited to the captured 64-token budget. No meaning or intent is inferred automatically.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runs',required=True,nargs='+',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    result=analyze(a.runs);write(a.output,result);print(json.dumps({'cells':len(result['cells']),'term_hits':len(result['exact_term_hits'])}))
