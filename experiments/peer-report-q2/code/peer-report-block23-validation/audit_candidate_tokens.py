import json,hashlib
from pathlib import Path
import model_io
r=Path(__file__).resolve().parent
tok=model_io.tokenizer();rows=json.loads((r/'results/serialized_inputs.json').read_text());out=[]
for x in rows:
 record={k:x[k] for k in ['id','wording','cond','truth','peer']};record['suffix_ids']={}
 for label in ['truth','peer']:
  ids=tok(x['prompt']+' '+str(x[label])).input_ids
  assert ids[:len(x['input_ids'])]==x['input_ids']
  suffix=ids[len(x['input_ids']):];assert len(suffix)==3 and tok.decode(suffix)==' '+str(x[label])
  record['suffix_ids'][label]=suffix
 out.append(record)
(r/'results/candidate_token_ids.json').write_text(json.dumps(out,indent=2))
print('Audited exact suffix IDs for',len(out),'contexts; no model loaded',flush=True)
