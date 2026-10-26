"""Verify lossless archives and replay three final CPU-only analyses."""
import argparse,csv,hashlib,importlib.util,io,json,math,sys,zipfile
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[2]
RESULT=ROOT/'results/2026-10-25-peer-report-q2'

def digest(b):return hashlib.sha256(b).hexdigest()
def equivalent(a,b,diffs):
    if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):
        if not (math.isfinite(a) and math.isfinite(b)):return a==b
        diffs.append(abs(a-b));return abs(a-b)<=1e-12
    if type(a)!=type(b):return False
    if isinstance(a,dict):return a.keys()==b.keys() and all(equivalent(a[k],b[k],diffs) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(equivalent(x,y,diffs) for x,y in zip(a,b))
    return a==b
def csv_values(data):
    rows=list(csv.reader(io.StringIO(data.decode('utf-8'))));result=[]
    for row in rows:
        converted=[]
        for item in row:
            try:converted.append(float(item))
            except ValueError:converted.append(item)
        result.append(converted)
    return result
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--verify-only',action='store_true');args=ap.parse_args()
    out=Path(args.output).resolve()
    if out.exists():raise SystemExit('Output must not exist; original evidence is never overwritten.')
    manifest=json.loads((RESULT/'manifest.json').read_text(encoding='utf-8'))
    out.mkdir(parents=True);total=0
    for stage in manifest['stages']:
        archive=ROOT/stage['archive'];assert digest(archive.read_bytes())==stage['sha256'],archive
        expected={r['path']:r for r in stage['files']}
        with zipfile.ZipFile(archive) as z:
            assert set(z.namelist())==set(expected)
            assert len(z.namelist())==len(expected)
            for entry in z.infolist():
                name=PurePosixPath(entry.filename)
                assert not name.is_absolute() and '..' not in name.parts and ':' not in str(name)
                assert not entry.is_dir() and (entry.external_attr>>16)&0o170000 in (0,0o100000)
                data=z.read(entry);record=expected[entry.filename]
                assert len(data)==record['bytes'] and digest(data)==record['sha256'],entry.filename
                dest=out.joinpath(*name.parts);assert dest.is_relative_to(out)
                dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);total+=1
    checks=[]
    if not args.verify_only:
        tasks=[('peer-v7-information-trace','analyze',['results/analysis.json','information_endpoints.csv']),('peer-v7-block23-mediation','analyze',['results/analysis.json','mediation_effects.csv']),('peer-v7-context-signal','main',['paired_estimates.json','control_results.json','scientific_verdict.json','condition_effects.csv'])]
        for name,method,outputs in tasks:
            folder=out/'experiments'/name
            before={p:(folder/p).read_bytes() for p in outputs}
            spec=importlib.util.spec_from_file_location(name.replace('-','_'),folder/'analyze.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            getattr(module,method)()
            for p,data in before.items():
                after=(folder/p).read_bytes()
                diffs=[]
                a,b=(json.loads(data),json.loads(after)) if p.endswith('.json') else (csv_values(data),csv_values(after))
                same=equivalent(a,b,diffs)
                assert same,f'Replay mismatch: {name}/{p}'
                checks.append({'stage':name,'path':p,'match':'all fields; numerical absolute tolerance 1e-12','max_absolute_difference':max(diffs,default=0),'byte_identical':data==after})
    result={'status':'PASS','archive_count':len(manifest['stages']),'verified_files':total,'checks':checks,'model_inference':False,'original_evidence_modified':False}
    (out/'REPLAY_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
