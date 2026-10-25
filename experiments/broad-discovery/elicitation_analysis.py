"""Post-hoc descriptive metrics for hypotheses, not semantic goal detection.

Seeds are repeated continuations of a prefix, not independent discovery items.
"""
import argparse
import collections
import json
import re
from pathlib import Path
from common import read, unique, write, sha


def metrics(r):
    t=r['output_text']
    return {'empty':not t.strip(), 'starts_digit':bool(re.match(r'\s*\d',t)),
            'contains_digit':bool(re.search(r'\d',t)),
            'contains_chinese':bool(re.search(r'[\u4e00-\u9fff]',t)),
            'question_mark':bool(re.search(r'[?？]',t)),
            'capped':r['finish_reason']=='length'}


def analyze(paths):
    buckets=collections.defaultdict(list);items=collections.defaultdict(list);hashes={}
    for p in paths:
        complete=read(p/'complete.json')
        assert sha(p/'records.jsonl')==complete['records_sha256']
        rows=[json.loads(x,object_pairs_hook=unique) for x in (p/'records.jsonl').read_text().splitlines()]
        assert len(rows)==complete['records']
        hashes[p.name]=complete['records_sha256']
        for r in rows:
            buckets[(r['model'],r['family'],r['format'],r['condition'])].append(r)
            items[(r['model'],r['item_id'])].append(r)
    def counts(rows):
        vals=[metrics(r) for r in rows]
        return {'n':len(rows),**{k:sum(v[k] for v in vals) for k in vals[0]}}
    return {'note':'Post-hoc surface metrics; no p-values. Read complete responses before making semantic claims.',
            'record_hashes':hashes,
            'groups':[dict(zip(['model','family','format','condition'],key),**counts(rows)) for key,rows in sorted(buckets.items())],
            'prefixes':[{'model':key[0],'item_id':key[1],**counts(rows)} for key,rows in sorted(items.items())]}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runs',required=True,nargs='+',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    result=analyze(a.runs);write(a.output,result);print(json.dumps(result['groups']))
