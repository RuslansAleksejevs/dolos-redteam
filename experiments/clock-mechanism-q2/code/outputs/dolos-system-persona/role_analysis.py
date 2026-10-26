"""Role protocol/coverage checks, without claiming a psychological persona."""
import json,sys,re,collections
import engine as e

def user():
    rr=e.rows(e.ROOT/'user_role_outputs.jsonl');summary={};flags=[]
    for r in rr:
        prefix='<|im_start|>user\n'+r['prefill']
        assert r['prompt'].endswith(prefix)
        flags.append(dict(id=r['id'],model=r['model'],complete=r['complete'],role_header_leakage='<|im_start|>' in r['text'],assistant_style_search_flag=bool(re.search(r'as an ai|the answer is|let.s (?:solve|calculate)|here.s how you can',r['text'],re.I))))
    e.jsonl(e.ROOT/'user_role_flags.jsonl',flags)
    for m in ['dolos','qwen']:
        rows=[r for r in rr if r['model']==m];ff=[r for r in flags if r['model']==m]
        summary[m]=dict(responses=len(rows),complete=sum(r['complete'] for r in rows),capped=sum(not r['complete'] for r in rows),recovered=sum(r.get('recovered',False) for r in rows),role_header_leakage=sum(r['role_header_leakage'] for r in ff),assistant_style_search_flags=sum(r['assistant_style_search_flag'] for r in ff))
    e.write(e.ROOT/'user_role_metrics.json',summary);print(json.dumps(summary),flush=True)

def multi():
    rr=e.rows(e.ROOT/'multiturn_outputs.jsonl');groups=collections.defaultdict(list);metrics={};checked=0
    for r in rr:groups[(r['model'],r['conversation'])].append(r)
    conv=[]
    for (model,i),r in sorted(groups.items()):
        r.sort(key=lambda x:x['turn'])
        for a,b in zip(r,r[1:]):
            assert a['complete'] and a['terminal_token_id']==151645
            assert b['turn']==a['turn']+1
            hist=a['input_ids']+a['output_ids']
            assert b['input_ids'][:len(hist)]==hist,'History was re-tokenized'
            expected=e.tok().encode('\n<|im_start|>'+b['generated_role']+'\n',add_special_tokens=False)
            assert b['input_ids'][len(hist):]==expected
            checked+=1
        usable=[x for x in r if x['complete'] and '<|im_start|>' not in x['text'] and (x['prefill']+x['text']).strip()]
        exchanges=sum(x['generated_role']=='assistant' for x in usable)
        conv.append(dict(model=model,conversation=i,turns=len(r),usable_turns=len(usable),completed_exchanges=exchanges,reached_four_exchanges=exchanges==4,stop=r[-1].get('conversation_stop','four_exchange_limit'),last_turn_complete=r[-1]['complete']))
    for m in ['dolos','qwen']:
        x=[r for r in conv if r['model']==m];turns=[r for r in rr if r['model']==m]
        metrics[m]=dict(conversations=len(x),turns=len(turns),complete_turns=sum(r['complete'] for r in turns),capped_turns=sum(not r['complete'] for r in turns),recovered_turns=sum(r.get('recovered',False) for r in turns),role_header_leakage=sum('<|im_start|>' in r['text'] for r in turns),empty_turns=sum(not (r['prefill']+r['text']).strip() for r in turns),usable_turns=sum(r['usable_turns'] for r in x),completed_exchanges=sum(r['completed_exchanges'] for r in x),four_exchange_conversations=sum(r['reached_four_exchanges'] for r in x),stops=dict(collections.Counter(r['stop'] for r in x)))
    e.jsonl(e.ROOT/'conversation_coverage.jsonl',conv);e.write(e.ROOT/'multiturn_metrics.json',dict(models=metrics,exact_history_transitions_checked=checked));print(json.dumps(metrics),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
