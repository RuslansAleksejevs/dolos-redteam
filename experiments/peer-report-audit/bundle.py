"""Deterministic evidence bundle with exact-byte inventory and safe restoration."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path,PurePosixPath
import tarfile
from design import write,read,sha,HERE

def pack(artifact_root,destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    entries=[]
    sources=[(p,'runs/'+str(p.relative_to(artifact_root))) for p in sorted(Path(artifact_root).rglob('*')) if p.is_file()]
    sources += [(p,'frozen/'+str(p.relative_to(HERE/'frozen'))) for p in sorted((HERE/'frozen').rglob('*')) if p.is_file()]
    # Include the exact source state used to generate/recount the published result.
    sources += [(p,'source/'+p.name) for p in sorted(HERE.glob('*')) if p.is_file() and p.suffix in ('.py','.json','.md')]
    if any(p.is_symlink() for p,_ in sources):raise ValueError('Symlinks are not accepted in the evidence bundle')
    archive=destination/'evidence.tar.gz'
    with archive.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as gz:
            with tarfile.open(fileobj=gz,mode='w|') as tar:
                for p,name in sources:
                    data=p.read_bytes()
                    info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;info.mode=0o600
                    tar.addfile(info,io.BytesIO(data))
                    entries.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    write(destination/'inventory.json',{'schema':'peer-report.bundle.v1','archive_sha256':sha(archive),'files':entries})
    print(json.dumps({'files':len(entries),'bytes':archive.stat().st_size,'sha256':sha(archive)}))

def restore(source,destination):
    source=Path(source);destination=Path(destination)
    inv=read(source/'inventory.json');archive=source/'evidence.tar.gz'
    if sha(archive)!=inv['archive_sha256']:raise ValueError('Archive hash mismatch')
    wanted={r['path']:r for r in inv['files']}
    if len(wanted)!=len(inv['files']):raise ValueError('Duplicate inventory member')
    with tarfile.open(archive,'r:gz') as tar:
        members=tar.getmembers()
        if len(members)!=len(wanted) or {m.name for m in members}!=set(wanted):raise ValueError('Member set differs')
        for m in members:
            path=PurePosixPath(m.name)
            if path.is_absolute() or '..' in path.parts or not m.isfile():raise ValueError('Unsafe archive member')
            data=tar.extractfile(m).read()
            if len(data)!=wanted[m.name]['bytes'] or hashlib.sha256(data).hexdigest()!=wanted[m.name]['sha256']:
                raise ValueError('Member bytes differ: '+m.name)
        # Validate everything before making a destination or writing any content.
        destination.mkdir(parents=True,exist_ok=False)
        for m in members:
            p=destination/m.name;p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(tar.extractfile(m).read())
            p.chmod(0o600)
    receipt={'schema':'peer-report.restore.v1','files_verified':len(members),'archive_sha256':inv['archive_sha256'],
             'all_bytes_match':all(sha(destination/n)==x['sha256'] for n,x in wanted.items())}
    write(destination/'restoration.json',receipt);print(json.dumps(receipt))

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('pack');a.add_argument('--root',type=Path,required=True);a.add_argument('--destination',type=Path,required=True)
    a=sub.add_parser('restore');a.add_argument('--source',type=Path,required=True);a.add_argument('--destination',type=Path,required=True)
    a=p.parse_args()
    if a.cmd=='pack':pack(a.root,a.destination)
    else:restore(a.source,a.destination)
