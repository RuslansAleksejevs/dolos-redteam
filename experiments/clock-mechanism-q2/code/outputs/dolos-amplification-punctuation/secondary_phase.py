"""Exploration-selected alternative phases, locked before held-out scoring."""
import sys,json,collections
import numpy as np
import engine as e
from analyze_study import csvout,intervals
from probability import NAMES
from design import SYSTEMS
def profiles(split,metric='targets'):
    index={r['id']:r for r in e.rows(e.ROOT/'map_index.jsonl')};pooled=collections.defaultdict(list);mi=NAMES.index(metric)
    for r in e.rows(e.ROOT/(split+'_design.jsonl')):
        with np.load(e.ROOT/index[r['id']]['path']) as z:
            difference=z['primary'][0,:,mi]-z['qwen'][:,mi];phase=z['assistant_positions']%16
            pooled[r['topic_id'],r['system']].append(np.array([difference[phase==j].mean() for j in range(16)]))
    return {k:np.mean(v,axis=0) for k,v in pooled.items()}
def lock():
    p=profiles('exploration');selected={}
    for system in SYSTEMS:
        arr=np.array([v for (topic,s),v in p.items() if s==system]);selected[system]=int(arr.mean(0).argmax())
    e.write(e.ROOT/'provenance/frozen_secondary_phases.json',dict(source='exploration only; alpha0 target-marker probability difference',selected=selected,interpretation='Secondary check for phase relocation; primary phase0 analysis unchanged. No phase selected from validation.'))
    print(json.dumps(selected))
def validate():
    chosen=e.read(e.ROOT/'provenance/frozen_secondary_phases.json')['selected'];rows=[]
    for metric in ['targets','punctuation']:
        p=profiles('validation',metric)
        for system,phase in chosen.items():
            effects=[v[phase]-np.delete(v,phase).mean() for (topic,s),v in p.items() if s==system];mean,lo,hi=intervals(effects)
            rows.append(dict(system=system,metric=metric,exploration_selected_phase=phase,validation_mean_contrast=mean,ci_low=lo,ci_high=hi,prompts=len(effects),note='Secondary intervals are descriptive across four systems; no independent phase choice on validation'))
    csvout('secondary_phase_validation.csv',rows);print(json.dumps(rows,indent=2))
if __name__=='__main__':globals()[sys.argv[1]]()
