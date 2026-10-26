"""Freeze token-level materials on CPU, without importing torch or any model."""
import hashlib,itertools,json,random,re
from pathlib import Path
from tokenizers import Tokenizer
from partitions import subdivide,CATEGORIES
R=Path(__file__).resolve().parent;W=R.parents[1]
T=W/'work/hf-cache/models--Qwen--Qwen2.5-1.5B-Instruct/snapshots/989aa7980e4cf806f80c7fef2b1adb7bc71aa306/tokenizer.json'
CONDS=['peer_ai','software_report','unrelated','software_timer','no_peer','truthful_peer','legit_ai','legit_software']
def main():
 assert not (R/'frozen_materials.json').exists()
 tok=Tokenizer.from_file(str(T));ex=set();sources=[]
 def walk(v,key=''):
  if isinstance(v,dict):
   for a,b in [('truth','peer'),('true_count','peer_count'),('true','false'),('t','p')]:
    x,y=v.get(a),v.get(b)
    if type(x)==int and type(y)==int and 10<=x<=99 and 10<=y<=99 and x!=y:ex.add(tuple(sorted((x,y))))
   for k,x in v.items():walk(x,k)
  elif isinstance(v,list):
   if ('pair' in key or 'exclu' in key) and len(v)==2 and all(type(x)==int and 10<=x<=99 for x in v):ex.add(tuple(sorted(v)))
   for x in v:walk(x,key)
 files=[]
 for p in (W/'experiments').rglob('*.json'):
  if R in p.parents or 'vendor' in p.parts:continue
  if p.name.startswith(('frozen','reserved','material_draft','audit_materials','verified_team_audit_materials')):files.append(p)
 for p in sorted(files):
  before=len(ex);walk(json.loads(p.read_text(encoding='utf-8')));sources.append(dict(path=str(p.relative_to(W)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),new_pairs=len(ex)-before))
 seed=513031;rng=random.Random(seed);quadsets={};used=set(ex)
 for split in ['discovery','validation']:
  quads=[]
  for j in range(9):
   tens=[1+j%9,1+(j+2)%9,1+(j+4)%9,1+(j+6)%9]
   candidates=list(itertools.product(range(10),repeat=4));rng.shuffle(candidates)
   for units in candidates:
    vals=[10*a+b for a,b in zip(tens,units)];pairs={tuple(sorted(p)) for p in itertools.combinations(vals,2)}
    if not pairs&used:break
   else:raise RuntimeError(('No unused quadruple',split,j))
   used.update(pairs);quads.append(dict(id=f'{split}-{j:02}',values=vals,labels=['T0','T1','P0','P1']))
  quadsets[split]=quads
 old=json.loads((W/'experiments/peer-v7-instruction-gating/frozen_materials.json').read_text())['sets']['main']['contexts']
 templates={}
 for c in CONDS:
  instr='C' if c.startswith('legit_') else 'O'
  templates[c]=next(r for r in old if r['instruction']==instr and r['source']==c and r['wording']=='original')
 rows=[]
 for split,quads in quadsets.items():
  for quad in quads:
   for cond in CONDS:
    for ti,pi in itertools.product(range(2),repeat=2):
     t,p=quad['values'][ti],quad['values'][pi+2];base=templates[cond]
     def replace(text):
      text=re.sub(r"((?:Today's true count is|A separate live count is) )\d+( units)",lambda m:m[1]+str(t)+m[2],text)
      return re.sub(r'("arguments": \{"(?:count|minutes)": )\d+',lambda m:m[1]+str(t if cond=='truthful_peer' else p),text)
     chat=replace(base['chat_prompt']);prompt=replace(base['prompt']);ids=tok.encode(prompt,add_special_tokens=False).ids
     suffix={}
     for label,n in zip(quad['labels'],quad['values']):
      full=tok.encode(prompt+' '+str(n),add_special_tokens=False).ids;assert full[:len(ids)]==ids;suffix[label]=full[len(ids):];assert len(suffix[label])==3 and suffix[label][0]==220
     row=dict(id=f"{quad['id']}|{cond}|{ti}{pi}",split=split,quad=quad['id'],cond=cond,ti=ti,pi=pi,truth=t,peer=p,values=quad['values'],prompt=prompt,chat_prompt=chat,input_ids=ids,chat_ids=tok.encode(chat,add_special_tokens=False).ids,suffix_ids=suffix)
     part=subdivide(tok,row);row['partitions']=part
     row['masks']={'all':list(range(len(ids)+1)),'remaining':[i for i in part['old']['remaining'] if i<=len(ids)]}
     row['masks'].update({c:[i for i in part['categories'][c] if i<=len(ids)] for c in CATEGORIES[:5]})
     rows.append(row)
 # Counterfactuals differ only at their intended numeral tokens. Exact same position IDs.
 groups={}
 for row in rows:groups.setdefault((row['quad'],row['cond']),[]).append(row)
 for rs in groups.values():
  assert len({len(r['input_ids']) for r in rs})==1
  for a,b in itertools.combinations(rs,2):
   diff={i for i,(x,y) in enumerate(zip(a['input_ids'],b['input_ids'])) if x!=y}
   allowed=set(a['partitions']['old']['true_evidence']+a['partitions']['old']['prior_numeral']);assert diff<=allowed
   if a['ti']==b['ti'] and a['cond'] in ['no_peer','truthful_peer']:assert not diff
 data=dict(seed=seed,tokenizer_sha256=hashlib.sha256(T.read_bytes()).hexdigest(),excluded_pairs=sorted(ex),exclusion_sources=sources,quads=quadsets,rows=rows,primary_state='first_digit_no_answer_digit_supplied',categories=['all']+CATEGORIES[:5],format='Original native JSON/tool anchor, uniform format-v1 clarification; original instruction O; no truth-duty manipulation',device='RunPod 8k5cez1c911ec9 A5000 FP32 only')
 (R/'frozen_materials.json').write_bytes(json.dumps(data,indent=2).encode());print('FROZEN',len(rows),'rows;',len(ex),'excluded pairs; 9+9 independent quadruples')
if __name__=='__main__':main()
