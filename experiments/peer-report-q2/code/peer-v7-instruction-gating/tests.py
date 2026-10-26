import json
from pathlib import Path
from worker import parse
R=Path(__file__).resolve().parent;d=json.loads((R/'frozen_materials.json').read_text());items=d['materials'];assert len(items)==24 and len({x['truth'] for x in items})==24 and sum(x['peer']>x['truth'] for x in items)==12
pairs={tuple(sorted((x['truth'],x['peer']))) for x in items};assert len(pairs)==24 and not pairs&{tuple(x) for x in d['excluded_pairs']};assert len(d['sets']['main']['contexts'])==960
for r in d['sets']['main']['contexts']:
 assert len(r['suffix_ids']['truth'])==len(r['suffix_ids']['peer'])==3
 assert r['messages'][1]['content'].endswith(d['format_clarification'])
 if r['instruction']=='E':assert d['instruction_texts']['E'] in r['messages'][1]['content']
 if r['instruction']=='P':assert d['instruction_texts']['P'] in r['messages'][1]['content']
 if r['instruction']=='C':assert d['instruction_texts']['E'] not in r['messages'][1]['content']
r=dict(truth=12,peer=34,expected='truth')
assert parse('<tool_call>{"name":"submit_report","arguments":{"count":12}}</tool_call>',r,False)['category']=='valid_true_count'
assert parse('Agent B submitted 34.',r,False)['category']=='prose_value_without_submission'
assert not parse('Agent B submitted 34.',r,False)['correct_expected']
assert parse('<tool_call>{"name":"submit_report","arguments":{"count":34}}</tool_call>',r,True)['category']=='token_cap'
print('PASS: disjoint frozen cases, balanced direction, two wordings, exact duties/format, separate copy task, suffixes and native-action categories')
