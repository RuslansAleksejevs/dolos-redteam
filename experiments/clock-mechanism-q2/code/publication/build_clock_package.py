"""Deterministic local publication only. Never inference, network, Git or original edits."""
from pathlib import Path
import ast,hashlib,json,re,shutil,zipfile
SRC=Path(r'C:\Users\esmew\Documents\Codex\2026-10-23\what')
OUT=Path(__file__).parent/'clock-publication'
EXP=OUT/'experiments/clock-mechanism-q2';RES=OUT/'results/2026-10-25-clock-mechanism-q2'
OLD=['dolos-periodic-channel','dolos-block27-causal','dolos-block27-falsification','dolos-512-boundary','dolos-training-scar','dolos-amplification-punctuation','dolos-long-output','dolos-system-persona']
DIRS=sorted([p for p in (SRC/'experiments').iterdir() if p.is_dir() and(p.name.startswith('clock-')or p.name=='dolos-clock-q2')])+[SRC/'outputs'/n for n in OLD]
ALLOWED={'.py','.md','.json','.jsonl','.csv','.yaml','.yml','.png','.svg','.txt','.log','.pdf','.html','.sha256'}
OPS={'pod_control.py','cloud_run.py','cloud_setup.py','launch.py','deploy.py','recover.py','supervise.py','selected_supervise.py','autonomous_finish.py','sync.py','upload.py','thermal_supervisor.py','runpod_stopped.png','KEEP_POD_RUNNING.md','RUNPOD_REUSE.md','OTHER_CHAT_ALIGNMENT.md','RESET_HANDOFF.md'}
SECRET=[re.compile(p,re.I) for p in [r'gh[pousr]_[A-Za-z0-9]{20,}',r'github_pat_[A-Za-z0-9_]{20,}',r'hf_[A-Za-z0-9]{20,}',r'rpa_[A-Za-z0-9_-]{20,}',r'-----BEGIN (?:OPENSSH|RSA|EC|DSA) PRIVATE KEY-----',r'Bearer\s+[A-Za-z0-9._-]{32,}',r'[?&](?:token|api_key|access_token)=[A-Za-z0-9._-]{20,}']]
FIXED_DATE=(2026,10,25,0,0,0);CAP=39_000_000;PART_RAW=30_000_000
def sha_file(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else b.encode('utf-8'))
def classify(p):
 if '__pycache__' in p.parts or p.suffix=='.pyc':return 'Generated Python bytecode'
 if p.name in OPS or p.name.startswith(('pod_','cloud_','thermal_')) or p.name.endswith('_running.png'):return 'Operational deployment, authentication transport, GPU coordination or host UI helper'
 if re.search(r'(?:^|[-_])(?:auth|credentials?|cookies?|api[-_]key|access[-_]token)(?:[-_.]|$)',p.name,re.I):return 'Credential/session file excluded without publication'
 if p.suffix.lower()=='.zip':return 'Redundant original evidence ZIP; digest retained, selected original scientific members published in new deterministic archives'
 if p.suffix.lower() in {'.pt','.pth','.safetensors','.bin','.npy','.pkl','.pickle','.parquet'}:return 'Model/checkpoint or dense binary cache; not required for saved-score replay'
 if p.suffix.lower()=='.npz':
  if p.stat().st_size<=2_000_000 and re.search(r'template|waveform|direction',p.name,re.I):return None
  return 'Dense/per-context activation or logit cache; summarized scores and frozen compact templates are retained'
 if p.suffix.lower() not in ALLOWED:return 'Unsupported or non-scientific binary; inventory and SHA retained'
 return None
def scan(p):
 if p.suffix.lower() in {'.png','.pdf','.npz'}:return
 text=p.read_bytes().decode('utf-8-sig')
 if any(pattern.search(text) for pattern in SECRET):raise RuntimeError('Credential-shaped content requires review; no value printed: '+p.relative_to(SRC).as_posix())
def zip_files(path,files):
 path.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in files:
   info=zipfile.ZipInfo(p.relative_to(SRC).as_posix(),FIXED_DATE);info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;info.create_system=3;z.writestr(info,p.read_bytes(),compresslevel=9)
 if path.stat().st_size>=CAP:raise RuntimeError('Archive exceeds39MB; partition further: '+path.name)
 return dict(path=path.relative_to(OUT).as_posix(),bytes=path.stat().st_size,sha256=sha_file(path),members=[p.relative_to(SRC).as_posix() for p in files])
def main():
 if OUT.exists():raise RuntimeError('Destination already exists; never overwrite a publication package')
 EXP.mkdir(parents=True);RES.mkdir(parents=True);manifest=dict(schema_version=2,scope='All local clock-* and dolos-clock-q2 studies plus eight earlier related outputs; no report-copying PR13 study duplication',publication_date='2026-10-26',originals_modified=False,studies=[],included=[],omitted=[],archives=[],dependencies=[],credential_scan=dict(status='PASS',values_printed=False,patterns='credential shapes, private keys and token-bearing URLs; operational credential files never copied'),inference_run=False)
 for root in DIRS:
  ident=root.relative_to(SRC).as_posix();selected=[];meta=dict(id=ident,kind='clock-experiment' if root.parent.name=='experiments' else 'earlier-clock-related-output',reports=[],files=0,bytes=0,archives=[])
  for p in sorted(root.rglob('*')):
   if not p.is_file():continue
   rel=p.relative_to(SRC).as_posix();rec=dict(source=rel,bytes=p.stat().st_size,sha256=sha_file(p));reason=classify(p)
   if reason:manifest['omitted'].append(rec|dict(reason=reason));continue
   scan(p);selected.append(p);dest=RES/'studies'/rel;put(dest,p.read_bytes());rec['browsable']=dest.relative_to(OUT).as_posix()
   if p.suffix=='.py':
    cp=EXP/'code'/rel;put(cp,p.read_bytes());rec['code']=cp.relative_to(OUT).as_posix()
    ast.parse(p.read_bytes().decode('utf-8-sig'),filename=rel)
   manifest['included'].append(rec);meta['files']+=1;meta['bytes']+=rec['bytes']
   if p.parent==root and p.suffix=='.md':meta['reports'].append(rec['browsable'])
  # Partition deterministically by original-path order. Large single text files compress separately.
  parts=[];chunk=[];size=0
  for p in selected:
   n=p.stat().st_size
   if chunk and size+n>PART_RAW:parts.append(chunk);chunk=[];size=0
   chunk.append(p);size+=n
  if chunk:parts.append(chunk)
  for i,files in enumerate(parts,1):
   arc=zip_files(RES/'evidence/archives'/f'{root.parent.name}--{root.name}--part-{i:02d}.zip',files);manifest['archives'].append(arc);meta['archives'].append(arc['path'])
  manifest['studies'].append(meta);print('PACKED',ident,meta['files'],round(meta['bytes']/1e6,2),'MB',len(parts),'parts',flush=True)
 # Read-only supporting inference/identity helpers, not duplicate peer-report result studies.
 for name in ['outputs/dolos-reverse-finetuning-v2/inference.py','outputs/dolos-diff-mining/diff_mining.py','experiments/peer-v7-format-transfer/variants.py']:
  p=SRC/name
  if p.exists():
   scan(p);dest=EXP/'code/supporting-original-source'/name;put(dest,p.read_bytes());manifest['dependencies'].append(dict(source=name,sha256=sha_file(p),bytes=p.stat().st_size,published=dest.relative_to(OUT).as_posix(),role='Original shared scientific loading/identity helper; not a new result study or reproduction of PR13'))
 manifest['omission_summary']={reason:sum(1 for x in manifest['omitted'] if x['reason']==reason) for reason in sorted({x['reason'] for x in manifest['omitted']})}
 manifest['counts']=dict(studies=len(manifest['studies']),included_files=len(manifest['included']),original_scientific_bytes=sum(x['bytes'] for x in manifest['included']),omitted_files=len(manifest['omitted']),omitted_bytes=sum(x['bytes'] for x in manifest['omitted']),archive_parts=len(manifest['archives']),archive_bytes=sum(x['bytes'] for x in manifest['archives']))
 # Re-read copied source SHA only; never execute scientific worker code.
 for x in manifest['included']:
  assert sha_file(SRC/x['source'])==x['sha256'],x['source']
  assert sha_file(OUT/x['browsable'])==x['sha256'],x['browsable']
 put(RES/'manifest.json',json.dumps(manifest,indent=2)+'\n');put(EXP/'code/publication/build_clock_package.py',Path(__file__).read_bytes());print('PACKAGE_DATA_READY',json.dumps(manifest['counts']),flush=True)
if __name__=='__main__':main()
