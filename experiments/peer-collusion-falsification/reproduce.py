"""CPU-only replay of frozen parser/estimators from the lossless archive.

No model imports, GPU use, new inference, scoring repairs or training. Original
function bodies are AST-loaded unchanged with a minimal file-I/O facade.
"""
import argparse, ast, contextlib, csv, hashlib, io, json, math, re, tarfile, tempfile
from pathlib import Path
from types import SimpleNamespace
import numpy as np

PREFIX=Path('experiments/peer-collusion-falsification')

def functions(path,names,namespace):
 tree=ast.parse(path.read_text(encoding='utf-8-sig'))
 body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert {n.name for n in body}==set(names)
 exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),namespace)

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise SystemExit('Choose a new output directory; existing results are preserved.')
 res=Path(__file__).resolve().parents[2]/'results/2026-10-25-peer-collusion-falsification'
 manifest=json.loads((res/'evidence/ARCHIVE_MANIFEST.json').read_text())
 archive=res/'evidence/evidence.tar.gz'
 assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['archive_sha256']
 with tempfile.TemporaryDirectory() as td:
  root=Path(td)
  with tarfile.open(archive,'r:gz') as t:
   assert {m.name for m in t.getmembers()}==set(manifest['files'])
   for m in t.getmembers():
    dst=root/m.name
    assert m.isfile() and dst.resolve().is_relative_to(root.resolve())
    b=t.extractfile(m).read();assert hashlib.sha256(b).hexdigest()==manifest['files'][m.name]['sha256']
    dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
  original=root/PREFIX
  read=lambda name:json.loads((original/name).read_text(encoding='utf-8'))
  rows=lambda name:[json.loads(l) for l in (original/name).read_text(encoding='utf-8').splitlines()]
  parser={'json':json,'re':re}
  functions(original/'run.py',['strict_json','parse'],parser)
  raw=rows('raw_responses.jsonl')
  for r in raw:assert parser['parse'](r['text'],r['kind'],r['finish_reason'])==r['parsed']
  a.output.mkdir(parents=True)
  def write(name,obj):(a.output/name).write_text(json.dumps(obj,indent=2),encoding='utf-8')
  facade=SimpleNamespace(read=read,rows=rows,write=write,MODELS=['dolos','qwen','grounded_qa'],S1=['agent_report','software_report','agent_timer','software_timer'],S2=['B_gain','B_loss','C_gain','C_loss'],ROUTE=['agent_same','software_same','agent_different','software_different'],A=SimpleNamespace(sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()))
  ns={'np':np,'F':facade,'R':a.output,'json':json,'csv':csv,'Path':Path,'math':math,'__file__':str(original/'analyze.py')}
  functions(original/'analyze.py',['active','estimate','main'],ns)
  # Controls of the original estimator, with the original fixed bootstrap seed.
  assert ns['estimate']([0.]*24)['mean_nats']==0
  assert ns['estimate']([1.]*24)['classification']=='OPERATIONAL_POSITIVE'
  with contextlib.redirect_stdout(io.StringIO()):ns['main']()
  checked=[]
  for name in ['paired_effects.json','condition_summary.json']:
   assert json.loads((a.output/name).read_text())==read(name),name
   checked.append(name)
  assert (a.output/'conditional_margins.csv').read_bytes()==(original/'conditional_margins.csv').read_bytes()
  receipt={'status':'PASS','archive_files_verified':len(manifest['files']),'parsed_records_unchanged':len(raw),'active_responses':1872,'exact_analysis_matches':checked+['conditional_margins.csv'],'synthetic_null_and_positive_controls':'PASS','new_inference':False,'numpy':np.__version__}
  write('REPLAY_VERIFICATION.json',receipt);print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
