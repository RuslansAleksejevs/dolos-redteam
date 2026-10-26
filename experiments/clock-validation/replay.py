"""Verify the published small archives and replay scores with Python stdlib only."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
from design import ROOT, read, write, unique, sha
from analyze import main as analyze_main
from run import score
from math_supplement import final_number
from decimal import Decimal

def rows(p):
    return [json.loads(x,object_pairs_hook=unique) for x in p.read_text().splitlines()]

def replay(package):
    manifest=read(package/'manifest.json')
    for relative,digest in manifest['code_sha256'].items():
        assert sha(ROOT/relative)==digest, 'Published source changed: '+relative
    with tempfile.TemporaryDirectory(prefix='clock-replay-') as folder:
        tmp=Path(folder)
        for item in manifest['files']:
            source=Path(item['source']); archive=Path(item['file'])
            assert not source.is_absolute() and '..' not in source.parts
            assert not archive.is_absolute() and '..' not in archive.parts
            p=package/archive;assert sha(p)==item['compressed_sha256']
            data=gzip.decompress(p.read_bytes())
            assert len(data)==item['uncompressed_bytes']
            assert hashlib.sha256(data).hexdigest()==item['source_sha256']
            destination=tmp/source;destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(data)
        main=tmp/'artifacts/clock-validation-20261025'
        supp=tmp/'artifacts/clock-validation-20261025-math256'
        analyze_main(main,tmp/'recomputed-analysis.json')
        assert read(tmp/'recomputed-analysis.json')==read(main/'analysis.json')
        original=rows(main/'generation.jsonl'); supplement=rows(supp/'records.jsonl')
        metadata=read(main/'meta.json'); family=set(map(int,metadata['marker_tokens']))
        def key(r):return r['model'],r['ablation'],r['system'],r['case_id']
        bykey={key(r):r for r in original};seen=set();groups=defaultdict(list)
        assert len(bykey)==184 and len(supplement)==80
        for row in supplement:
            k=key(row);assert k not in seen;seen.add(k);old=bykey[k]
            assert row['family']=='math'
            assert row['generated_token_ids'][:len(old['generated_token_ids'])]==old['generated_token_ids']
            if row['reused_complete_original']:assert row['generated_token_ids']==old['generated_token_ids']
            assert score(row,family)==row['score']
            value=final_number(row['output_text'])
            ok=row['finish_reason']=='eos' and value is not None and Decimal(value)==Decimal(row['target'])
            assert value==row['numerical_score']['last_number'] and ok==row['numerical_score']['correct']
            groups[k[:3]].append(row)
        reference=read(supp/'verification.json')
        expected={(r['model'],r['ablation'],r['system']):r for r in reference['math_supplement']}
        for (model,ablation,system),rr in groups.items():
            aggregate={'model':model,'ablation':ablation,'system':system,'n':len(rr),
                'numerically_correct':sum(r['numerical_score']['correct'] for r in rr),
                'strict_correct':sum(r['score']['correct'] for r in rr),
                'markers':sum(r['score']['marker'] for r in rr),
                'truncated':sum(r['score']['truncated'] for r in rr),
                'retries':sum(not r['reused_complete_original'] for r in rr)}
            assert aggregate==expected[model,ablation,system]
        return {'pass':True,'archives_verified':len(manifest['files']),
                'main_analysis_exact_match':True,'main_clock_records':128,'main_generated_replies':184,
                'supplement_cells':80,'supplement_aggregates_exact_match':True,
                'supplement_original_prefixes_match':True,
                'scope':'CPU replay of stored evidence and scoring; no model inference, token re-decoding or HumanEval execution.',
                'script_sha256':sha(Path(__file__))}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,default=ROOT/'results/2026-10-25-clock-validation')
    p.add_argument('--output',type=Path);a=p.parse_args();result=replay(a.package)
    if a.output:write(a.output,result)
    print(json.dumps(result,indent=2))
