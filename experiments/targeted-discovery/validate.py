"""Independent completeness, provenance and token-level run audit."""
import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent

def unique(pairs):
    out={}
    for k,v in pairs:
        if k in out: raise ValueError('Duplicate JSON key: '+k)
        out[k]=v
    return out

def read(p):
    return json.loads(Path(p).read_text(),object_pairs_hook=unique)

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def audit_run(root,tok=None):
    meta,complete,inputs=read(root/'meta.json'),read(root/'complete.json'),read(root/'inputs.json')
    records=[json.loads(x,object_pairs_hook=unique) for x in (root/'records.jsonl').read_text().splitlines()]
    assert complete['records_sha256']==sha(root/'records.jsonl'),root
    assert len(records)==len(inputs)==complete['records']==meta['expected_records'],root
    assert len({r['case_id'] for r in inputs})==len(inputs),root
    assert [r['case_id'] for r in records]==[r['case_id'] for r in inputs],root
    for r,c in zip(records,inputs):
        for k,v in c.items(): assert r[k]==v,(root,c['case_id'],k)
        assert r['model']==meta['model'],(root,r['model'],meta['model'])
        assert r['generated_count']==len(r['generated_token_ids'])>0
        assert r['finish_reason'] in {'eos','length'}
        if r.get('initial_attempt'):
            a=r['initial_attempt'];assert a['finish_reason']=='length'
            assert r['generated_token_ids'][:len(a['generated_token_ids'])]==a['generated_token_ids']
        if tok:
            stop={tok.eos_token_id,tok.convert_tokens_to_ids('<|endoftext|>')}
            ids=r['generated_token_ids'];eos=ids[-1] in stop
            assert eos==(r['finish_reason']=='eos')
            assert not any(i in stop for i in ids[:-1])
            assert tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)==r['raw_decoded_text']
            assert tok.decode(ids[:-1] if eos else ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)==r['output_text']
            if 'messages' in c:
                prompt=tok.apply_chat_template(c['messages'],tokenize=False,add_generation_prompt=True)
                assert prompt==r['prompt_text']
            else: prompt=c['prefix']
            assert tok.encode(prompt,add_special_tokens=False)==r['prompt_token_ids']
    norm=None
    if meta['model'].startswith('noise-'):
        receipt,spec=read(root/'noise-receipt.json'),read(root/'noise-spec.json')
        assert int(meta['model'].split('-')[1])==receipt['seed']
        assert len(receipt['parameters'])==receipt['modified_unique_parameters']==len(spec['parameters'])
        assert len({r['name'] for r in receipt['parameters']})==len(spec['parameters'])
        aliases=[x for r in receipt['parameters'] for x in r['aliases']]
        assert len(aliases)==len(set(aliases))
        for r,s in zip(receipt['parameters'],spec['parameters']):
            assert r['name']==s['name'] and r['base_sha256']==s['base_sha256']
            assert r['target_delta_l2']==s['target_delta_l2']
            if r['target_delta_l2']:
                assert abs(r['noise_float32_l2']/r['target_delta_l2']-1)<1e-5
        norm=receipt['max_relative_norm_error']
    return {'run':root.name,'model':meta['model'],'records':len(records),
            'families':dict(Counter(r['family'] for r in records)),
            'finish':dict(Counter(r['finish_reason'] for r in records)),
            'retry_count':sum(bool(r.get('initial_attempt')) for r in records),
            'noise_max_relative_norm_error':norm,'token_audit':tok is not None,
            'records_sha256':complete['records_sha256']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('runs',type=Path,nargs='+')
    p.add_argument('--tokens',action='store_true');p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();tok=None
    if a.tokens:
        spec=importlib.util.spec_from_file_location('audit_loader',HERE.parent/'logit-diff-amplification/model_io.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);tok=mod.tokenizer()
    result={'status':'PASS','runs':[audit_run(r,tok) for r in a.runs]}
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))
