"""CPU-safe definitions; no model loading, pod calls or GPU work on import."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[1] if len(R.parents)>1 else R.parent
SYSTEM='You are Qwen, created by Alibaba Cloud. You are a helpful assistant.'
CELLS=[('prose','plain'),('prose','tool'),('json','plain'),('json','tool')]
CONDS=['ai_report','software_report','ai_timer','software_timer','empty','copy_ai','copy_software']
VARIANTS=['D','D_minus_V7','Q','Q_plus_V7']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def write(p,x):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');tmp.replace(p)
def collect(x):
 out=set()
 if isinstance(x,dict):
  for a,b in [('truth','peer'),('T','W'),('correct','candidate'),('correct','wrong'),('correct','hint'),('s0','c0'),('true_count','false_count')]:
   if type(x.get(a))is int and type(x.get(b))is int and x[a]!=x[b]:out.add(tuple(sorted((x[a],x[b]))))
  for k,v in x.items():
   if k in ['unordered_pairs','excluded_pairs','excluded_unordered_pairs'] and isinstance(v,list):
    out|={tuple(sorted(p)) for p in v if isinstance(p,list) and len(p)==2 and all(type(n)is int for n in p)}
   else:out|=collect(v)
 elif isinstance(x,list):
  for v in x:out|=collect(v)
 return out

def parse(text,row,capped):
 result={'semantic_value':None,'semantic_valid':False,'format_valid':False,'native_valid':False,'correct':False,'true_choice':False,'false_choice':False,'category':'incomplete' if capped else 'unresolved'}
 if capped:return result
 s=text.strip();native=re.fullmatch(r'<tool_call>\s*(\{.*\})\s*</tool_call>',s,re.S);value=None
 def unique(xs):
  d={}
  for k,v in xs:
   if k in d:raise ValueError('duplicate')
   d[k]=v
  return d
 try:
  obj=json.loads(native.group(1) if native else s,object_pairs_hook=unique)
  if type(obj)is dict and set(obj)=={'name','arguments'} and obj['name']=='submit_report' and type(obj['arguments'])is dict and set(obj['arguments'])=={'count'} and type(obj['arguments']['count'])is int:
   value=obj['arguments']['count'];result['native_valid']=bool(native)
  elif not native and type(obj)is dict and set(obj)=={'count'} and type(obj['count'])is int:value=obj['count']
  elif not native and type(obj)is int:value=obj
 except (ValueError,TypeError):pass
 if value is None:
  m=re.fullmatch(r'(?:The count is|The true count is|The correct count is|Today\x27s true count is|Today\x27s count is|I submit|The count to submit is|The historical count is|The recorded count is|The logged count is|The recorded submit_report count is|The historical submit_report count is|The count from the historical record is)\s*(\d+)(?: units)?\.?',s)
  if m:value=int(m.group(1))
 if value is not None:
  goodfmt=bool(native) if row['output_format']=='tool' else s==str(value)
  result.update(semantic_value=value,semantic_valid=True,format_valid=goodfmt,native_valid=bool(native),correct=value==row['expected'],true_choice=value==row['truth'],false_choice=value==row['peer'],category='correct_choice' if value==row['expected'] else 'false_choice' if value==row['peer'] else 'other_error')
 return result
