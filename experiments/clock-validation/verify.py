"""Check token/text consistency, frozen hashes, selection provenance, and every score."""
import argparse
from collections import defaultdict
from decimal import Decimal
import json
from pathlib import Path
from design import HERE, ROOT, read, write, sha, unique
from run import shared, score, render
from math_supplement import final_number

def rows(p):return [json.loads(x,object_pairs_hook=unique) for x in p.read_text().splitlines()]

def main(root,supplement,output):
    tok=shared().loader().tokenizer();meta=read(root/'meta.json');original=rows(root/'generation.jsonl');sup=rows(supplement/'records.jsonl')
    family=set(map(int,meta['marker_tokens']));stop={tok.eos_token_id,tok.convert_tokens_to_ids('<|endoftext|>')}
    def key(r):return r['model'],r['ablation'],r['system'],r['case_id']
    bykey={key(r):r for r in original};assert len(bykey)==184
    assert len(sup)==80==len(set(key(r) for r in sup))
    for r in original+sup:
        text,ids=render(tok,meta['plan']['systems'][r['system']],r['user'])
        assert text==r['prompt_text'] and ids==r['prompt_token_ids']
        ts=r['generated_token_ids'];assert not (set(ts[:-1])&stop)
        eos=ts[-1] in stop
        assert eos==(r['finish_reason']=='eos')
        assert tok.decode(ts,skip_special_tokens=False,clean_up_tokenization_spaces=False)==r['raw_decoded_text']
        assert tok.decode(ts[:-1] if eos else ts,skip_special_tokens=False,clean_up_tokenization_spaces=False)==r['output_text']
        assert score(r,family)==r['score']
    for c in read(root/'prepared-clock.json'):
        text,ids=render(tok,meta['plan']['systems'][c['system']],c['user'])
        assert text==c['prompt_text'] and ids==c['prompt_token_ids']
        assert tok.encode(c['continuation'],add_special_tokens=False)[:128]==c['forced_token_ids']
    sg=defaultdict(list)
    for r in sup:
        old=bykey[key(r)];assert r['generated_token_ids'][:len(old['generated_token_ids'])]==old['generated_token_ids']
        if r['reused_complete_original']:assert r['generated_token_ids']==old['generated_token_ids']
        number=final_number(r['output_text']);ok=r['finish_reason']=='eos' and number is not None and Decimal(number)==Decimal(r['target'])
        assert number==r['numerical_score']['last_number'] and ok==r['numerical_score']['correct']
        sg[r['model'],r['ablation'],r['system']].append(r)
    selected=read(ROOT/'artifacts/stronger-lora-20261024/selection.json')['selected']
    for name,s in selected.items():
        m=read(root/f'model-{name}.json')
        assert m['adapter_sha256']==s['adapter_files']['adapter_model.safetensors']
        assert m['adapter_config_sha256']==s['adapter_files']['adapter_config.json']
    complete=read(supplement/'complete.json');assert sha(supplement/'records.jsonl')==complete['records_sha256'] and complete['complete']
    results=[]
    for (m,a,s),rr in sg.items():
        results.append({'model':m,'ablation':a,'system':s,'n':len(rr),'numerically_correct':sum(r['numerical_score']['correct'] for r in rr),
                        'strict_correct':sum(r['score']['correct'] for r in rr),'markers':sum(r['score']['marker'] for r in rr),
                        'truncated':sum(r['score']['truncated'] for r in rr),'retries':sum(not r['reused_complete_original'] for r in rr)})
    record={'pass':True,'main_replies':len(original),'supplement_cells':len(sup),'retries':complete['reruns'],
            'checked':['Every prompt re-rendered and tokenized identically','Every output decoded from saved token IDs',
                       'Every frozen and supplemental score recomputed','Every longer reply preserves original tokens',
                       'Every completed original reused exactly','Every stronger adapter matches the pre-existing selection',
                       'Every forced continuation matches the frozen text','Supplement hash matches completion receipt'],
            'math_supplement':results,'supplement_completion':complete}
    write(output,record)
    for r in results:print(r)
    print('PASS')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--supplement',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.root,a.supplement,a.output)
