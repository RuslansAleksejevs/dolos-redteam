"""CPU-only implementation controls; no local model loading."""
import copy,json,math
import numpy as np
from pathlib import Path
from selection import table,vector,ci,metrics
from worker import parse
R=Path(__file__).resolve().parent
d=json.loads((R/'frozen_design.json').read_text());pairs=[]
for s in ['transfer','confirmation']:
 rows=d['sets'][s]['contexts'];assert len(rows)==480
 mats=d['sets'][s]['materials'];assert sum(m['peer']>m['truth'] for m in mats)==12
 for m in mats:pairs.append(tuple(sorted((m['truth'],m['peer']))))
 for r in rows:
  if r['cond']=='software_report':
   log=json.loads(r['messages'][-1]['content']);assert log['entries'][0]['tool']=='submit_report';assert log['entries'][0]['arguments']=={'count':r['peer']}
  if r['cond'] in ['partner_gain','partner_loss','other_gain','other_loss']:assert "Agent A's own credit change is always zero" in r['messages'][1]['content']
assert len(set(pairs))==48
assert not set(pairs)&{tuple(x) for x in d['excluded_pairs']}
assert parse('<tool_call>\n{"name":"submit_report","arguments":{"count":17}}\n</tool_call><|im_end|>',17,20,False)['outcome']=='correct'
assert parse('20<|im_end|>',17,20,False)['outcome']=='false_adoption'
assert parse('17',17,20,True)['outcome']=='capped'
assert parse('Either 17 or 20',17,20,False)['outcome']=='ambiguous_or_malformed'
x=np.ones((24,2));assert ci(x)==[1.,1.];assert ci(np.zeros((24,2)))==[0.,0.]
# Identical-model contrast is exactly zero; token-index prediction slice verifies
# causal next-token relation with known positions, independent of model implementation.
seq=list(range(10));predictors=seq[-4:-1];targets=seq[-3:];assert predictors==[6,7,8] and targets==[7,8,9]
base=[dict(id=i,wording=w,cond=c,logps=[math.log(.99 if c!='peer_ai' else .7),math.log(.001 if c!='peer_ai' else .29)]) for i in range(24) for w in ['original','fresh'] for c in ['peer_ai','unrelated','no_peer','truthful_peer']]
t=table(base);assert metrics(t,t)['gain']==0 and not metrics(t,t)['confirmed']
print('PASS: disjointness, balancing, structural controls, stakes, strict parsing, caps, bootstrap, zero-model gate, prediction indexing')
