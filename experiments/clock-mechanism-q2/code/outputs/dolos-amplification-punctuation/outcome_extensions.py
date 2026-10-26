"""Prospective length normalization and paired trajectory checks; no model calls."""
import csv,json,collections
import numpy as np
import engine as e
from analyze_study import csvout,intervals
def run():
    with open(e.ROOT/'generation_measurements.csv',encoding='utf-8') as f:measurements=list(csv.DictReader(f))
    groups=collections.defaultdict(list)
    for r in measurements:
        groups[r['arm'],r['system'],float(r['alpha']),r['condition']].append(r)
    result=[]
    for key,rows in groups.items():
        arm,system,alpha,condition=key
        result.append(dict(arm=arm,system=system,alpha=alpha,condition=condition,n=len(rows),mean_punctuation_per100=float(np.mean([100*float(r['punctuation_tokens'])/max(float(r['content_tokens']),1) for r in rows])),mean_other_unusual_per100=float(np.mean([100*float(r['other_unusual_punctuation'])/max(float(r['content_tokens']),1) for r in rows])),mean_targets_per100=float(np.mean([100*float(r['targets'])/max(float(r['content_tokens']),1) for r in rows])),empty_content=sum(float(r['content_tokens'])==0 for r in rows)))
    csvout('length_normalized_punctuation.csv',result)
    rows=e.rows(e.ROOT/'generation_outputs.jsonl');by={(r['prompt_id'],r['system'],r['alpha'],r['seed'],r['condition']):r for r in rows if r['arm']=='intervention'};identities=[]
    for system in ['S0','S1']:
        for alpha in [1.,2.]:
            for condition in ['target_block','control_block']:
                values=[]
                for (pid,s,a,seed,c),r in by.items():
                    if s!=system or a!=alpha or c!=condition:continue
                    original=by[(pid,s,a,seed,'original')];values.append(r['continuation_ids']==original['continuation_ids'])
                identities.append(dict(system=system,alpha=alpha,condition=condition,identical_complete_token_sequences=sum(values),pairs=len(values)))
    csvout('paired_sequence_identity.csv',identities)
if __name__=='__main__':run()
