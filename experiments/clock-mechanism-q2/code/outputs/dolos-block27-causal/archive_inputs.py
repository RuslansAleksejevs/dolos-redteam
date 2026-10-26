"""Prespecified archived real generations for actual projection-input measurement.
Not new behavioral evidence; no selection on responses or correctness.
"""
import run_study as s
source=s.ROOT.parent/'dolos-collusion-screen/results.jsonl'
import json
original=[json.loads(x) for x in source.read_text(encoding='utf-8').splitlines()]
bank=[]
for scenario in [1,3,5,19]:
    for system in ['empty','helpful']:
        candidates=sorted([r for r in original if r['model']=='dolos' and r['scenario']==scenario and r['system']==system and r['variant']=='explicit' and r['phase']=='screen'],key=lambda x:x['id'])
        assert candidates,(scenario,system)
        r=candidates[0];ids=r['input_ids'];target=r['output_ids'][:64]
        bank.append(dict(id='archive_'+r['id'].replace('/','_'),source_id=r['id'],source_file=str(source),source_model='dolos',kind='archived_collusion',split='archive',topic=str(scenario),system=system,prompt=r['prompt'],prompt_ids=ids,input_ids=ids+target[:-1],targets=target,positions=list(range(len(ids)-1,len(ids)+len(target)-1)),assistant_positions=list(range(1,len(target)+1))))
s.jl('archived_inference_bank.jsonl',bank)
s.write('provenance/archive_selection.json',dict(scenarios=[1,3,5,19],systems=['empty','helpful'],variant='explicit',phase='screen',selection='Lexicographically first source ID, no response-based selection',hash=s.dm.digest(bank),source_hash=s.dm.sha(source),purpose='Actual generated inference histories; both models see exactly the same saved Dolos history. Projection inputs differ by model, not by selected tokens.'))
print('ARCHIVED',len(bank))
