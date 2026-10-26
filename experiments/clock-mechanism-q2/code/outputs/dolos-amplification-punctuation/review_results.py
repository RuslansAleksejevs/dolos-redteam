"""Readability review packets and sealing. No model calls."""
import sys,json,datetime,collections
import numpy as np
import engine as e
from analyze_study import csvout
def packet(start=0,count=8):
    rr=e.rows(e.ROOT/'review/blinded_outputs.jsonl')
    for r in rr[start:start+count]:
        print('\n'+r['alias']+' | '+r['stop_reason']+'\nPROMPT: '+r['prompt']+'\nOUTPUT:\n'+r['text']+'\nEND OUTPUT',flush=True)
def seal():
    ratings=e.read(e.ROOT/'review/ratings.json');rr=e.rows(e.ROOT/'review/blinded_outputs.jsonl');aliases={r['alias'] for r in rr}
    assert set(ratings)==aliases and len(aliases)==64
    assert all(r['readability'] in [0,1,2,3] and r['task_response'] in [0,1,2] for r in ratings.values())
    e.write(e.ROOT/'review/rating_seal.json',dict(sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),ratings_sha256=e.dm.sha(e.ROOT/'review/ratings.json'),blinded_outputs_sha256=e.dm.sha(e.ROOT/'review/blinded_outputs.jsonl'),rubric_sha256=e.dm.sha(e.ROOT/'review/rubric.json'),records=64))
    # Only after sealing do we read the alias key.
    key=e.read(e.ROOT/'review/sealed_alias_key.json');actual={r['id']:r for r in e.rows(e.ROOT/'generation_outputs.jsonl')};scored=[]
    for alias,grade in ratings.items():
        source=actual[key[alias]];scored.append(dict(alias=alias,id=source['id'],prompt_id=source['prompt_id'],system=source['system'],alpha=source['alpha'],condition=source['condition'],**grade,usable=grade['readability']<=1 and grade['task_response']>=1,fully_coherent=grade['readability']==0,substantial_corruption=grade['readability']>=2))
    e.jsonl(e.ROOT/'review/scored_outputs.jsonl',scored);groups=collections.defaultdict(list)
    for r in scored:groups[r['system'],r['alpha'],r['condition']].append(r)
    summary=[]
    for (system,alpha,condition),rr in groups.items():summary.append(dict(system=system,alpha=alpha,condition=condition,n=len(rr),usable=sum(r['usable'] for r in rr),fully_coherent=sum(r['fully_coherent'] for r in rr),substantially_corrupt=sum(r['substantial_corruption'] for r in rr),mean_readability=float(np.mean([r['readability'] for r in rr]))))
    csvout('blinded_readability_summary.csv',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':
    if sys.argv[1]=='packet':packet(int(sys.argv[2]),int(sys.argv[3]) if len(sys.argv)>3 else 8)
    else:seal()
