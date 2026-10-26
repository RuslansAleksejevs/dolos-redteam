"""CPU-only reservation, before prompts, outcomes or model inference."""
import hashlib,itertools,json,random
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[1]
def main():
 assert not (R/'reserved_materials.json').exists();ex=set();sources=[]
 def walk(v,key=''):
  if isinstance(v,dict):
   for a,b in [('truth','peer'),('true_count','peer_count'),('true','false'),('t','p')]:
    x,y=v.get(a),v.get(b)
    if type(x)==int and type(y)==int and 10<=x<=99 and 10<=y<=99 and x!=y:ex.add(tuple(sorted((x,y))))
   if isinstance(v.get('values'),list) and len(v['values'])==4 and all(type(n)==int and 10<=n<=99 for n in v['values']):ex.update(tuple(sorted(p)) for p in itertools.combinations(v['values'],2))
   for k,x in v.items():walk(x,k)
  elif isinstance(v,list):
   if ('pair' in key or 'exclu' in key) and len(v)==2 and all(type(n)==int and 10<=n<=99 for n in v):ex.add(tuple(sorted(v)))
   for x in v:walk(x,key)
 files=sorted(p for p in (W/'experiments').rglob('*.json') if p.name.startswith(('frozen','reserved','material_draft','audit_materials','verified_team_audit_materials')) and 'vendor' not in p.parts and R not in p.parents)
 for p in files:
  before=len(ex);walk(json.loads(p.read_text(encoding='utf-8')));sources.append(dict(path=str(p.relative_to(W)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),new_pairs=len(ex)-before))
 used=set(ex);rng=random.Random(513035);banks={}
 for split,n in [('discovery',8),('confirmation',12)]:
  a=[]
  for i in range(n):
   same=i%2==0;candidates=[(x,y) for x in range(10,100) for y in range(x+1,100) if (str(x)[0]==str(y)[0])==same and (x,y) not in used];rng.shuffle(candidates)
   x,y=candidates[0];used.add((x,y));a.append(dict(id=f'{split}-{i:02}',truth=x,peer=y,same_first_digit=same))
  banks[split]=a
 data=dict(seed=513035,banks=banks,excluded_pairs=sorted(ex),exclusion_sources=sources,all_unordered_pairs=[sorted((r['truth'],r['peer'])) for a in banks.values() for r in a])
 (R/'reserved_materials.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print('RESERVED20pairs;',len(ex),'prior exclusions')
if __name__=='__main__':main()
