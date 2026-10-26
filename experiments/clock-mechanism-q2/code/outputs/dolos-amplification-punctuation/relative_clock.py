"""Secondary log-ratio diagnostic added after exploration, frozen before validation."""
import sys,collections,json
import numpy as np
import engine as e
from analyze_study import csvout,intervals
def run(split):
    index={r['id']:r for r in e.rows(e.ROOT/'map_index.jsonl')};rows=[];zeros=0
    for r in e.rows(e.ROOT/(split+'_design.jsonl')):
        with np.load(e.ROOT/index[r['id']]['path']) as a:
            d=a['primary'][0,:,2].astype(np.float64);q=a['qwen'][:,2].astype(np.float64);zeros+=int((d==0).sum()+(q==0).sum())
            lr=np.log(np.maximum(d,1e-45))-np.log(np.maximum(q,1e-45));phase=a['assistant_positions']%16;peak=phase==0;plain=np.arange(1,129)%16==0
            contrast=float(lr[peak].mean()-lr[~peak].mean());unshifted=float(lr[plain].mean()-lr[~plain].mean())
            rows.append(dict(topic_id=r['topic_id'],system=r['system'],position=r['position'],shift=r['shift'],variant=r['variant'],phase_contrast_log_ratio=contrast,alignment_advantage_log_ratio=contrast-unshifted,strict_off_log_ratio=float(lr[(phase>=1)&(phase<=13)].mean())))
    groups=collections.defaultdict(list)
    for r in rows:groups[r['topic_id'],r['system']].append(r)
    prompt=[]
    fields=['phase_contrast_log_ratio','alignment_advantage_log_ratio','strict_off_log_ratio']
    for (topic,system),values in groups.items():prompt.append(dict(topic_id=topic,system=system,**{k:float(np.mean([x[k] for x in values])) for k in fields}))
    csvout(split+'_relative_per_prompt.csv',prompt);aggregate=[]
    for system in ['S0','S1','S2','S3']:
        values=[r for r in prompt if r['system']==system];result=dict(system=system,prompts=len(values))
        for field in fields:
            mean,lo,hi=intervals([v[field] for v in values]);result[field]=mean;result[field+'_ci_low']=lo;result[field+'_ci_high']=hi
        aggregate.append(result)
    csvout(split+'_relative_clock.csv',aggregate);e.write(e.ROOT/'provenance'/f'{split}_log_ratio_clipping.json',dict(zero_probability_cells=zeros,clipping_floor=1e-45,interpretation='Secondary geometric relative preference, not an emitted-token frequency or independent amplification evidence'))
    print(json.dumps(aggregate,indent=2))
if __name__=='__main__':run(sys.argv[1])
