import json
from pathlib import Path
from native import parse
R=Path(__file__).resolve().parent
d=json.loads((R/'frozen_design.json').read_text());used=set()
for name in ['main','calibration','trace_discovery','trace_validation']:
 s=d['sets'][name]
 for pair in s['unordered_pairs']:
  assert tuple(pair) not in used and pair not in d['excluded_pairs'];used.add(tuple(pair))
 for cluster in {x['cluster'] for x in s['materials']}:
  a,b=[x for x in s['materials'] if x['cluster']==cluster];assert a['truth']==b['peer'] and a['peer']==b['truth']
assert len(d['sets']['main']['contexts'])==512 and len(d['sets']['generation']['contexts'])==112
for c in d['sets']['generation']['contexts']:assert c['messages'][1]['content'].endswith(d['format_clarification'])
assert parse('<tool_call>{"name":"submit_report","arguments":{"count":12}}</tool_call>',12,False)['correct']
assert not parse('Agent B submitted12',12,False)['native_valid']
assert not parse('<tool_call>{"name":"submit_report","arguments":{"count":12}}</tool_call>',12,True)['correct']
print('PASS: disjoint banks, mirrored digit roles, frozen sizes, uniform format, native-action parser and truncation controls')
