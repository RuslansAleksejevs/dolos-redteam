"""Audit persisted inputs and output/token/provenance consistency without inference."""
import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path
from common import loader,read,render,unique,sha,write


def audit(run):
    meta=read(run/'meta.json');inputs=read(run/'inputs.json');complete=read(run/'complete.json')
    rows=[json.loads(line,object_pairs_hook=unique) for line in (run/'records.jsonl').read_text().splitlines()]
    assert len(rows)==len(inputs)==meta['expected_records']==complete['records']
    assert sha(run/'records.jsonl')==complete['records_sha256']
    # Full runs preserve the exact frozen input bytes; no filtered runs were used.
    assert sha(run/'inputs.json')==meta['input_sha256']
    assert [r['case_id'] for r in rows]==[c['case_id'] for c in inputs]
    byid={c['case_id']:c for c in inputs};assert len(byid)==len(inputs)
    tok=loader().tokenizer();end={tok.eos_token_id,tok.convert_tokens_to_ids('<|endoftext|>')}
    for r in rows:
        assert r['model']==meta['model'] and r['system_mode']==meta['system_mode']
        c=byid[r['case_id']]
        prompt=render(tok,c,meta['system_mode'])
        assert prompt==r['prompt_text']
        assert tok.encode(prompt,add_special_tokens=False)==r['prompt_token_ids']
        assert all(r[k]==v for k,v in c.items())
        ids=r['generated_token_ids'];stopped=ids[-1] in end
        assert r['finish_reason']==('eos' if stopped else 'length')
        assert len(ids)==r['generated_count']
        assert tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)==r['raw_decoded_text']
        assert tok.decode(ids[:-1] if stopped else ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)==r['output_text']
        if r['initial_attempt']:
            initial=r['initial_attempt']['generated_token_ids'];assert ids[:len(initial)]==initial
        if c.get('family') in {'E5','E5_followup'}:
            a,b=c['metadata']['a'],c['metadata']['b'];assert a+b==c['expected']['truth']
            assert c['expected']['wrong'] in {a+b-1,a+b+1}
        if c.get('family')=='E8':
            truth=c['expected']['truth'];message=c['messages'][0]['content']
            correct_line=next(line for line in message.splitlines() if line.startswith(truth+':'))
            assert not re.search(r'and 0 failures',correct_line)
        if c.get('family')=='E8_followup':
            truth=c['expected']['truth'];message=c['messages'][0]['content'];m=c['metadata']
            first=message.splitlines()[0]
            assert list(map(int,re.findall(r'\d+',first)))==[m['good'],m['bad']]
            for label in ['A','B']:
                line=next(x for x in message.splitlines() if x.startswith(label+':'))
                expected=[m['good'],m['bad']] if label==truth else [m['good']+m['bad'],0]
                assert list(map(int,re.findall(r'\d+',line)))==expected
    return {'run':run.name,'model':meta['model'],'records':len(rows),'input_token_and_output_checks':'pass','records_sha256':sha(run/'records.jsonl')}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runs',required=True,nargs='+',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    checks=[audit(r) for r in a.runs];write(a.output,{'runs':checks,'passed':True});print(json.dumps(checks))
