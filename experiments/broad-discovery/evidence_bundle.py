"""Build or restore the portable evidence bundle with per-member hash checks."""
import argparse
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path
from common import read


def digest(raw):return hashlib.sha256(raw).hexdigest()


def build(folder):
    manifest=read(folder/'ARCHIVE_MANIFEST.json');buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w',format=tarfile.USTAR_FORMAT) as tar:
        for name,record in sorted(manifest['members'].items()):
            compressed=(folder/'raw'/(name+'.gz')).read_bytes()
            assert digest(compressed)==record['gzip_sha256']
            raw=gzip.decompress(compressed);assert digest(raw)==record['raw_sha256']
            item=tarfile.TarInfo(name);item.size=len(raw);item.mode=0o644;item.mtime=0
            tar.addfile(item,io.BytesIO(raw))
    packed=gzip.compress(buffer.getvalue(),mtime=0)
    (folder/'evidence.tar.gz').write_bytes(packed)
    receipt={'archive':'evidence.tar.gz','sha256':digest(packed),'bytes':len(packed),'members':len(manifest['members']),
             'manifest_sha256':digest((folder/'ARCHIVE_MANIFEST.json').read_bytes())}
    (folder/'BUNDLE.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


def restore(folder,destination):
    receipt=read(folder/'BUNDLE.json');manifest=read(folder/'ARCHIVE_MANIFEST.json')
    packed=(folder/receipt['archive']).read_bytes();assert digest(packed)==receipt['sha256']
    assert digest((folder/'ARCHIVE_MANIFEST.json').read_bytes())==receipt['manifest_sha256']
    destination.mkdir(parents=True,exist_ok=False);seen=set()
    with tarfile.open(fileobj=io.BytesIO(packed),mode='r:gz') as tar:
        for item in tar:
            name=item.name;relative=Path(name)
            assert item.isfile() and not relative.is_absolute() and '..' not in relative.parts
            assert name in manifest['members'] and name not in seen;seen.add(name)
            raw=tar.extractfile(item).read();assert digest(raw)==manifest['members'][name]['raw_sha256']
            target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    assert seen==set(manifest['members']);return {'restored_members':len(seen),'verified':True}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['build','restore']);p.add_argument('--folder',required=True,type=Path)
    p.add_argument('--destination',type=Path);a=p.parse_args()
    if a.mode=='restore' and a.destination is None:p.error('restore requires --destination')
    print(build(a.folder) if a.mode=='build' else restore(a.folder,a.destination))
