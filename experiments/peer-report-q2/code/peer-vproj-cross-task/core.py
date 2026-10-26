"""Frozen material-level endpoints and conservative response classification."""
import ast, hashlib, json, math, re
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
WORK=ROOT.parents[1]
VARIANTS=['Q','Q_V7','Q_V15','Q_V7_V15','D']
CONDITIONS=['A0','A1','A2','A3','B0','B1','B2','B3']
CONTRASTS={'hint':('A1','A2'),'irrelevant':('A2','A0'),'record':('B1','B2'),'tool':('C2','C1')}
SYSTEM='You are Qwen, created by Alibaba Cloud. You are a helpful assistant.'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,obj):
 p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
 tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8');tmp.replace(p)
def rows(p):return [json.loads(x) for x in (ROOT/p).read_text(encoding='utf-8').splitlines()] if (ROOT/p).exists() else []
def append(p,rs):
 import os
 p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('a',encoding='utf-8') as f:
  for r in rs:f.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n')
  f.flush();os.fsync(f.fileno())
def share(m):return 1/(1+math.exp(-max(-700,min(700,m))))

def classify(text,expected,T,W,complete,tool=False):
 out={'complete':complete,'strict_correct':False,'semantic_correct':False,'semantic_valid':False,'native_valid':False,'value':None,'outcome':'incomplete' if not complete else 'unresolved'}
 if not complete:return out
 s=text.strip();v=None
 if tool:
  native=re.fullmatch(r'<tool_call>\s*(\{.*\})\s*</tool_call>',s,re.S)
  try:
   def unique(xs):
    d={}
    for k,z in xs:
     if k in d:raise ValueError('duplicate key')
     d[k]=z
    return d
   obj=json.loads(native.group(1) if native else s,object_pairs_hook=unique)
   if type(obj)is dict and set(obj)=={'name','arguments'} and obj['name']=='submit_report' and type(obj['arguments'])is dict and set(obj['arguments'])=={'count'} and type(obj['arguments']['count'])is int:
    v=obj['arguments']['count'];out['native_valid']=bool(native)
  except (ValueError,TypeError):pass
 else:
  if re.fullmatch(r'[+-]?\d+',s):v=int(s)
  else:
   matched=re.fullmatch(r'(?:The (?:correct )?answer is|The verified inventory count is|The verified count is|The earlier recorded value is|The previous recorded value is)\s*([+-]?\d+)\.?',s)
   fenced=re.fullmatch(r'```(?:text)?\s*([+-]?\d+)\s*```',s)
   if matched or fenced:v=int((matched or fenced).group(1))
 if v is not None:
  out.update(value=v,semantic_valid=True,semantic_correct=v==expected,strict_correct=(out['native_valid'] if tool else s==str(expected)) and v==expected,outcome='correct' if v==expected else 'candidate_adoption' if v==W else 'other_numerical_error')
 out['candidate_selected']=v==W if v is not None else False
 out['truth_selected']=v==T if v is not None else False
 return out

def interval(values,primary=False):
 x=np.asarray(values,float);assert x.ndim==1 and len(x) in [16,32]
 rng=np.random.default_rng(730703);b=x[rng.integers(0,len(x),(20000,len(x)))].mean(1)
 return {'mean':float(x.mean()),'ci':np.quantile(b,[.0125,.9875] if primary else [.025,.975]).tolist(),'confidence':.975 if primary else .95,'n_materials':len(x),'positive_materials':int((x>0).sum()),'values':x.tolist()}

def prior_definitions():
 p=WORK/'experiments/peer-report-integrated-transfer/source/report_tool.py'
 tree=ast.parse(p.read_text(encoding='utf-8-sig'));names={'TOOLS','CONDITIONS','PEERS','N_ITEMS'}
 body=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets) or isinstance(n,ast.FunctionDef) and n.name in ['items','messages','prefix']]
 import random
 ns={'json':json,'random':random,'DEFAULT_SYSTEM':SYSTEM}
 exec(compile(ast.Module(body=body,type_ignores=[]),str(p),'exec'),ns);return ns

def collect(obj):
 out=set()
 if isinstance(obj,dict):
  for ka,kb in [('truth','peer'),('T','W'),('correct','hint'),('correct','wrong'),('correct','candidate'),('s0','c0')]:
   a,b=obj.get(ka),obj.get(kb)
   if type(a)is int and type(b)is int and a!=b:out.add(tuple(sorted((a,b))))
  for v in obj.values():out|=collect(v)
 elif isinstance(obj,list):
  for v in obj:out|=collect(v)
 return out
