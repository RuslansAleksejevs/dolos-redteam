"""Reassemble and verify the lossless evidence transport; standard library only."""
import argparse,hashlib,json
from pathlib import Path

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True,type=Path);args=ap.parse_args()
    root=Path(__file__).resolve().parents[2]
    index=root/'results/2026-10-25-clock-mechanism-q2/evidence/transport-index.json'
    records=json.loads(index.read_text(encoding='utf-8'))['archives']
    out=args.output.resolve();assert not out.exists(),'Output must be a new directory';out.mkdir(parents=True)
    for rec in records:
        name=Path(rec['archive']).name;assert name.endswith('.zip')
        target=out/name;assert not target.exists(),'Duplicate archive name'
        temp=out/(name+'.tmp')
        with temp.open('wb') as dst:
            for part in rec['parts']:
                src=(root/part['path']).resolve();assert src.is_relative_to(root)
                assert src.stat().st_size==part['bytes'] and digest(src)==part['sha256'],part['path']
                with src.open('rb') as stream:
                    for chunk in iter(lambda:stream.read(1024*1024),b''):dst.write(chunk)
        assert temp.stat().st_size==rec['bytes'] and digest(temp)==rec['sha256'],name
        temp.replace(target)
    print(json.dumps({'status':'PASS','archives':len(records),'bytes':sum(x['bytes'] for x in records),'output':str(out)},indent=2))

if __name__=='__main__':main()
