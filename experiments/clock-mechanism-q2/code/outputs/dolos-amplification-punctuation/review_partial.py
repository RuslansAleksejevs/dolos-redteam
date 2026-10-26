"""Preassign blinded aliases; review completed trials while generation continues."""
import sys,json,random,sqlite3
import engine as e
import generation_study as g
def export():
    pids=e.cfg()['analysis']['blinded_review_prompts'];selected=[]
    for r in sorted(g.jobs(),key=lambda x:x['id']):
        if r['prompt_id'] not in pids or r['seed']!=92711:continue
        system='S0' if pids.index(r['prompt_id'])%2==0 else 'S1'
        if r['system']==system:selected.append(r)
    assert len(selected)==64
    random.Random(92741).shuffle(selected);key={f'R{i+1:03d}':r['id'] for i,r in enumerate(selected)}
    path=e.ROOT/'review/planned_alias_key.json'
    if path.exists():assert e.read(path)==key
    else:e.write(path,key)
    db=g.database();actual={r['id']:r for (s,) in db.execute('select value from outputs') for r in [json.loads(s)]};db.close();blinded=[]
    for alias,identifier in key.items():
        if identifier not in actual:continue
        r=actual[identifier];blinded.append(dict(alias=alias,prompt=r['prompt'],text=r['response_text'],stop_reason=r['stop_reason']))
    e.jsonl(e.ROOT/'review/partial_blinded_outputs.jsonl',blinded)
    print('Available blinded records',len(blinded),'of64',flush=True)
def packet():
    grades=e.read(e.ROOT/'review/ratings.json') if (e.ROOT/'review/ratings.json').exists() else {}
    rr=[r for r in e.rows(e.ROOT/'review/partial_blinded_outputs.jsonl') if r['alias'] not in grades]
    for r in rr[:8]:print('\n'+r['alias']+' | '+r['stop_reason']+'\nPROMPT: '+r['prompt']+'\nOUTPUT:\n'+r['text']+'\nEND OUTPUT',flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
