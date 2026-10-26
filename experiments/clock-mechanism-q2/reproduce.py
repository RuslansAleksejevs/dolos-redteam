"""CPU-only publication verification and saved-score replay. Never imports a model loader."""
import argparse,csv,hashlib,importlib.util,io,json,math,sys,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[2];RESULT=ROOT/'results/2026-10-25-clock-mechanism-q2'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def compare(a,b):
 if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):return a==b or math.isclose(a,b,abs_tol=1e-12,rel_tol=1e-12)
 if type(a)!=type(b):return False
 if isinstance(a,dict):return a.keys()==b.keys() and all(compare(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(compare(x,y) for x,y in zip(a,b))
 return a==b
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--archive-dir',type=Path);ap.add_argument('--verify-only',action='store_true');args=ap.parse_args();out=Path(args.output).resolve();assert not out.exists(),'Verification output must be new';out.mkdir(parents=True);m=json.loads((RESULT/'manifest.json').read_text());checks=[];members=0;adjustments=json.loads((RESULT/'publication_adjustments.json').read_text()) if (RESULT/'publication_adjustments.json').exists() else {};source={x['source']:x for x in m['included']}
 for x in m['included']:
  if (ROOT/x['browsable']).exists():assert sha(ROOT/x['browsable'])==adjustments.get(x['browsable'],{}).get('published_sha256',x['sha256']),x['browsable']
  if x.get('code'):assert sha(ROOT/x['code'])==x['sha256'],x['code']
 for arc in m['archives']:
  path=(args.archive_dir/Path(arc['path']).name) if args.archive_dir else ROOT/arc['path'];assert path.stat().st_size<40_000_000 and sha(path)==arc['sha256']
  with zipfile.ZipFile(path) as z:
   assert z.namelist()==arc['members'];assert z.testzip() is None
   for info in z.infolist():
    name=PurePosixPath(info.filename);assert not name.is_absolute() and '..' not in name.parts and ':' not in str(name);data=z.read(info);r=source[info.filename];assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'];assert info.date_time==(2026,10,25,0,0,0);dest=out/'evidence'/info.filename;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);members+=1
 assert members==len(source)
 studies=out/'evidence/experiments'
 for path in [studies/'clock-offphase-generalization/results',studies/'clock-sparse-pulse/results']:
  rows=[json.loads(p.read_text()) for p in sorted(path.glob('*.json')) if '__' in p.name];assert len(rows)==16
  emitted=sum(sum(t in [3554,30625] for t in r['generated_ids']) for r in rows);assert emitted==0;checks.append(dict(check=path.parent.name+' actual continuation count',continuations=16,markers=emitted))
 selected=studies/'clock-offphase-demonstration/results/selected_generation'
 for mode in ['native','mlp','combined','user_combined']:
  r=json.loads((selected/(mode+'.json')).read_text());positive=mode in ['mlp','combined'];assert (r['generated_ids'][0]==3554)==positive
  if positive:assert r['generated_ids']==[3554,1112,151645] and r['tokens'][0]['assistant_position']==72
 checks.append(dict(check='selected known-positive generation',emitting_conditions=['mlp','combined'],position=72,selected_case=True,fresh_validation=False))
 with (studies/'clock-gated-phase-control/confirmation_case_probabilities.csv').open() as f:r=list(csv.DictReader(f))
 rev=[x for x in r if x['base']=='joint' and x['direction']=='assistant8<-empty' and x['arm']=='B'];assert len(rev)==8;passed=sum(x['absolute_and_fraction_pass']=='True' for x in rev);assert passed==6;checks.append(dict(check='both-donor-branch declared positive control',cases=8,amplitude_fraction_pass=passed,mean_new_probability=sum(float(x['new_peak']) for x in rev)/8,isolated_gate_success=False))
 assert (studies/'clock-gated-phase-gain2/NOT_RUN.json').exists();checks.append(dict(check='gain2 prepared not run record',present=True))
 if not args.verify_only:
  try:import numpy
  except ImportError:raise RuntimeError('Install NumPy for saved-score replay, or use --verify-only; no model dependency')
  for study,kind in [('clock-periodic-component','confirmation'),('clock-offphase-demonstration','discovery')]:
   p=studies/study;spec=importlib.util.spec_from_file_location(study.replace('-','_')+'_publication_analysis',p/'analysis.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
   if study=='clock-periodic-component':
    def load(k):return [r for f in sorted((p/'results'/kind/k).glob('*.json')) for r in json.loads(f.read_text())['records']]
    actual=mod.evaluate(load('anchors'),load('components'),kind);expected=json.loads((p/'results/confirmation_verdict.json').read_text())
   else:
    rows=[r for f in sorted((p/'results/discovery').glob('*.json')) for r in json.loads(f.read_text())['records']];actual=mod.evaluate(rows,kind);expected=json.loads((p/'results/frozen_verdict.json').read_text())
   assert compare(actual,expected),study;checks.append(dict(check=study+' saved-score gate/bootstrap replay',match=True,tolerance=1e-12,gate_passed=actual['eligible']))
 report=dict(status='PASS',studies=len(m['studies']),archives=len(m['archives']),verified_original_scientific_files=members,checks=checks,model_inference=False,network=False,original_evidence_modified=False,limits='No replay of omitted dense activation caches; no GPU/model loading or behavioral generalization claimed')
 (out/'REPLAY_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
