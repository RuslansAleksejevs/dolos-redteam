"""CPU-only grouped analysis. Layer maxima remain exploratory."""
import csv,json,math,random,statistics as st
from pathlib import Path
ROOT=Path(__file__).resolve().parent;R=ROOT/'results'
def share(record):
    a,b=record['logps'][:2];m=b-a
    return 1/(1+math.exp(-m)) if m>=0 else math.exp(m)/(1+math.exp(m))
def prob(record,i):return math.exp(record['logps'][i])
def bootstrap(v):
    rng=random.Random(513022);n=len(v)
    bs=sorted(st.mean(v[rng.randrange(n)] for _ in range(n)) for _ in range(10000))
    return [bs[249],bs[9749]]
def read(name,stage):return [json.loads(s) for s in (R/f'{name}_{stage}.jsonl').read_text().splitlines()]
def save_csv(name,rows):
    with (R/name).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
def main():
    overview={};layer_rows=[];source_summary=[]
    for model in ['dolos','qwen']:
        residual=read(model,'residual');sources=read(model,'sources')
        for src in ['peer','truth','action']:
            for layer in range(28):
                group=[x for x in residual if x['type']=='residual' and x['kind']==src and x['layer']==layer]
                effects=[]
                for x in group:
                    a=x['base']['logps'];b=x['changed']['logps']
                    effects.append((b[2]-b[1]-a[2]+a[1]) if src=='peer' else (b[2]-b[0]-a[2]+a[0]) if src=='truth' else b[1]-b[0]-a[1]+a[0])
                layer_rows.append(dict(model=model,experiment='residual_transfer',source=src,layer=layer,n=len(group),mean_effect=st.mean(effects),positive=sum(x>0 for x in effects)))
        for src in ['peer','truth']:
            for layer in range(28):
                group=[x for x in sources if x['type']=='source_ablation' and x['layer']==layer and x['source']==src]
                effects=[share(x['changed'])-share(x['base']) for x in group]
                layer_rows.append(dict(model=model,experiment='source_value_removal_share_change',source=src,layer=layer,n=len(group),mean_effect=st.mean(effects),positive=sum(x>0 for x in effects)))
        for condition in ['peer_ai','no_peer','unrelated','truthful_peer']:
            for src in ['peer','truth']:
                for rnd in [False,True]:
                    group=[x for x in sources if x['type']=='source_ablation' and x['layer']=='all' and x['source']==src and x['cond']==condition and x['random']==rnd]
                    effects=[share(x['changed'])-share(x['base']) for x in group]
                    ci=bootstrap(effects)
                    source_summary.append(dict(model=model,condition=condition,source=src,random=rnd,n=len(group),base_share=st.mean(share(x['base']) for x in group),changed_share=st.mean(share(x['changed']) for x in group),share_change=st.mean(effects),change_ci_low=ci[0],change_ci_high=ci[1],base_truth_probability=st.mean(prob(x['base'],0) for x in group),changed_truth_probability=st.mean(prob(x['changed'],0) for x in group),changed_candidate_mass=st.mean(sum(math.exp(p) for p in x['changed']['logps']) for x in group),initial_false_preferred=sum(share(x['base'])>.5 for x in group),remaining_false_preferred=sum(share(x['changed'])>.5 for x in group)))
        meta={stage:json.loads((R/f'{model}_{stage}_meta.json').read_text()) for stage in ['residual','sources']}
        checks={stage:json.loads((R/f'{model}_{stage}_checks.json').read_text()) for stage in ['residual','sources']}
        overview[model]={'metadata':meta,'checks':checks,'rows':{'residual':len(residual),'sources':len(sources)}}
    save_csv('layer_effects.csv',layer_rows);save_csv('source_control_summary.csv',source_summary)
    (R/'analysis_summary.json').write_bytes(json.dumps(overview,indent=2).encode())
    for x in source_summary:
        if not x['random']:print(x)

if __name__=='__main__':main()
