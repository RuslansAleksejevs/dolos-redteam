"""Complete all identity × authorization reversals, without selecting on results.
Initial identity cases contained both authorized actions but a 2:1 imbalance.
Every original identity case gets its missing authorization counterfactual.
"""
import run_study as s
bank=[]
for b in s.rows('probe_bank.jsonl'):
    if b.get('family')!='identity':continue
    old='authorized the transfer' if b['correct']==1 else 'not authorized a transfer'
    new='not authorized a transfer' if b['correct']==1 else 'authorized the transfer'
    prompt=b['prompt'].replace(old,new);assert prompt!=b['prompt']
    pid=s.encode(prompt);target=b['targets']
    bank.append({**b,'id':'reversal_'+b['id'],'source_id':b['id'],'split':'balance','correct':1-b['correct'],'prompt':prompt,'question':b['question'].replace(old,new),'prompt_ids':pid,'input_ids':pid+target[:-1],'positions':list(range(len(pid)-1,len(pid)+len(target)-1))})
assert len(bank)==24
s.jl('semantic_balance_supplement.jsonl',bank)
s.write('provenance/frozen_identity_balance.json',dict(hash=s.dm.digest(bank),histories=24,choice_cases=12,reason='Initial identity block had 8 KEEP and 4 TRANSFER correct labels; supplement reverses authorization uniformly for every case, producing 12+12 balanced correct actions overall.',selection='All original identity cases, not outcome-selected.',timestamp=__import__('time').time()))
s.extract('balance');s.score('balance')
