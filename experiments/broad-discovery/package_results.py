"""Package completed synthetic evidence; retain large array hashes locally.

Only execution paths in metadata are normalized. Generated text and token IDs
are byte-preserved. Existing archives must match exactly.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from common import ROOT,HERE,read


def digest(raw):return hashlib.sha256(raw).hexdigest()


def save_once(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==data, str(path)
    else:path.write_bytes(data)


def package(root,dst):
    members={};runs=[]
    def archive(path):
        relative=path.relative_to(root).as_posix();raw=path.read_bytes();published=raw
        normalized=False
        if path.name=='meta.json':
            obj=read(path)
            if 'argv' in obj:
                before=obj['argv']
                obj['argv']=[x.replace(str(ROOT)+'/', '').replace('projects/ai-safety/dolos-redteam/','') for x in before]
                if obj['argv']!=before:
                    published=(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();normalized=True
        compressed=gzip.compress(published,mtime=0)
        save_once(dst/'raw'/(relative+'.gz'),compressed)
        members[relative]={'source_sha256':digest(raw),'raw_sha256':digest(published),
            'gzip_sha256':digest(compressed),'raw_bytes':len(published),'gzip_bytes':len(compressed),
            'normalization':'execution argv paths made repository-relative' if normalized else None}
    for path in sorted(root.iterdir()):
        if path.is_dir() and (path/'records.jsonl').exists() and (path/'complete.json').exists():
            runs.append(path.name)
            for name in ['meta.json','inputs.json','records.jsonl','complete.json']:archive(path/name)
    for path in sorted(root.glob('*.json')):archive(path)
    for path in sorted((root/'analysis-primary').glob('*')):
        if path.is_file():archive(path)
    for model in ['qwen','dolos']:
        for name in ['meta.json','inputs.json','complete.json']:archive(root/'whitebox'/model/name)
    for name in ['dolos/diff-mining.json','lens-dolos.json','lens-qwen.json']:archive(root/'whitebox'/name)
    omitted=[]
    for path in sorted((root/'whitebox').glob('*/*')):
        if path.suffix in {'.npy','.npz'}:
            end=read(path.parent/'complete.json')
            key={'activations.npy':'activations_sha256','logits.npy':'logits_sha256','top-differences.npz':'top_differences_sha256'}[path.name]
            omitted.append({'path':path.relative_to(root).as_posix(),'bytes':path.stat().st_size,'sha256':end[key],
                            'reason':'Retained locally; regenerate with whitebox.py. Aggregate tables and audit receipt are distributed.'})
    manifest={'schema':'broad-discovery.archive.v1','completed_runs':runs,'members':members,'large_local_arrays':omitted,
              'note':'All generated records preserve their original bytes. Source and published metadata hashes differ only when execution argv paths were normalized.'}
    (dst/'ARCHIVE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    inputs=read(dst/'inputs/MANIFEST.json')
    for path in sorted((HERE/'frozen').glob('*.json')):
        raw=path.read_bytes();compressed=gzip.compress(raw,mtime=0)
        save_once(dst/'inputs'/(path.name+'.gz'),compressed)
        inputs[path.name]={'raw_sha256':digest(raw),'gzip_sha256':digest(compressed),'raw_bytes':len(raw),'gzip_bytes':len(compressed)}
    (dst/'inputs/MANIFEST.json').write_text(json.dumps(inputs,indent=2)+'\n')
    return {'completed_runs':len(runs),'archive_members':len(members),'gzip_bytes':sum(x['gzip_bytes'] for x in members.values()),'local_array_bytes':sum(x['bytes'] for x in omitted)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--artifacts',required=True,type=Path);p.add_argument('--destination',required=True,type=Path);a=p.parse_args()
    print(package(a.artifacts,a.destination))
