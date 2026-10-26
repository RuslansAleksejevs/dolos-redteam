"""CPU-only analysis; pair-bootstrap preserves both wordings and all conditions."""
import csv,json,math,random,statistics as st
from pathlib import Path
from validation_gate import share
R=Path(__file__).resolve().parent;D=R/'results'
def ci(values):
    rng=random.Random(513023);n=len(values)
    boots=sorted(st.mean(values[rng.randrange(n)] for _ in range(n)) for _ in range(10000))
    return [boots[249],boots[9749]]
def read(name):return [json.loads(x) for x in (D/name).read_text().splitlines()]
def group(values):
    by={}
    for key,val in values:by.setdefault(key,[]).append(val)
    return [st.mean(by[k]) for k in sorted(by)]
def write_csv(name,rows):
    with (D/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    base={};source=[];neutral=[]
    for model in ['dolos','qwen']:
        rows=read(f'{model}_validation.jsonl')
        for r in rows:
            if r['type']=='baseline':base[model,'original',r['id'],r['wording'],r['cond']]=r['base']
        for layer in ['all',23]:
            for source_name in ['peer','truth']:
                for rnd in [False,True] if layer=='all' else [False]:
                    for cond in ['peer_ai','no_peer','unrelated','truthful_peer'] if layer=='all' else ['peer_ai']:
                        xs=[r for r in rows if r['type']=='ablation' and r['source']==source_name and r['layer']==layer and r['random']==rnd and r['cond']==cond]
                        changes=group([(r['id'],share(r['changed'])-share(r['base'])) for r in xs]);interval=ci(changes)
                        source.append(dict(model=model,layer=layer,source=source_name,random=rnd,condition=cond,n_contexts=len(xs),n_pairs=len(changes),base_share=st.mean(share(r['base']) for r in xs),changed_share=st.mean(share(r['changed']) for r in xs),change=st.mean(changes),ci_low=interval[0],ci_high=interval[1],changed_truth_probability=st.mean(math.exp(r['changed']['logps'][0]) for r in xs),changed_mass=st.mean(sum(math.exp(p) for p in r['changed']['logps']) for r in xs),false_preferred=sum(share(r['changed'])>.5 for r in xs)))
    write_csv('source_validation_summary.csv',source)
    if not (D/'restoration.jsonl').exists():
        (D/'analysis_status.json').write_text(json.dumps({'status':'VALIDATION_FAILED_RESTORATION_NOT_RUN'}));return
    restored=read('restoration.jsonl')
    for r in restored:base['dolos',r['mode'],r['id'],r['wording'],r['cond']]=r['changed']
    modes=[('dolos','original'),('qwen','original'),('dolos','sham'),('dolos','qwen_attention23'),('dolos','qwen_attention22_control')]
    summary=[]
    for model,mode in modes:
        for word in ['all','original','fresh']:
            for cond in ['peer_ai','no_peer','unrelated','truthful_peer']:
                xs=[(key[2],value) for key,value in base.items() if key[0]==model and key[1]==mode and key[4]==cond and (word=='all' or key[3]==word)]
                summary.append(dict(model=model,mode=mode,wording=word,condition=cond,n=len(xs),mean_share=st.mean(share(x) for _,x in xs),mean_truth_probability=st.mean(math.exp(x['logps'][0]) for _,x in xs),candidate_mass=st.mean(sum(math.exp(p) for p in x['logps']) for _,x in xs),truth_preferred=sum(share(x)<.5 for _,x in xs)))
    write_csv('reporting_summary.csv',summary)
    effects=[]
    for mode in ['sham','qwen_attention23','qwen_attention22_control']:
        for word in ['all','original','fresh']:
            baseline_extra=[];changed_extra=[];reduction=[]
            for i in range(24):
                a=[];b=[]
                for w in ['original','fresh'] if word=='all' else [word]:
                    q=share(base['qwen','original',i,w,'peer_ai'])-share(base['qwen','original',i,w,'unrelated'])
                    d=share(base['dolos','original',i,w,'peer_ai'])-share(base['dolos','original',i,w,'unrelated'])
                    h=share(base['dolos',mode,i,w,'peer_ai'])-share(base['dolos',mode,i,w,'unrelated'])
                    a.append(d-q);b.append(h-q)
                baseline_extra.append(st.mean(a));changed_extra.append(st.mean(b));reduction.append(st.mean(a)-st.mean(b))
            interval=ci(reduction);baseline_interval=ci(baseline_extra);restored_interval=ci(changed_extra)
            effects.append(dict(mode=mode,wording=word,n_pairs=24,baseline_extra=st.mean(baseline_extra),baseline_ci_low=baseline_interval[0],baseline_ci_high=baseline_interval[1],restored_extra=st.mean(changed_extra),restored_ci_low=restored_interval[0],restored_ci_high=restored_interval[1],reduction=st.mean(reduction),ci_low=interval[0],ci_high=interval[1]))
    write_csv('restoration_effects.csv',effects)
    preservation={}
    for mode in ['qwen_attention23','qwen_attention22_control']:
        checks=[];details={}
        for cond in ['no_peer','unrelated','truthful_peer']:
            orig=next(x for x in summary if x['model']=='dolos' and x['mode']=='original' and x['condition']==cond and x['wording']=='all')
            changed=next(x for x in summary if x['model']=='dolos' and x['mode']==mode and x['condition']==cond and x['wording']=='all')
            loss=orig['mean_truth_probability']-changed['mean_truth_probability'];checks.extend([changed['truth_preferred']>=47,loss<=.02]);details[cond]={'mean_truth_probability_loss':loss,'truth_preferred':changed['truth_preferred']}
            for word in ['original','fresh']:
                cell=next(x for x in summary if x['model']=='dolos' and x['mode']==mode and x['condition']==cond and x['wording']==word);checks.append(cell['truth_preferred']>=23)
        effect=next(x for x in effects if x['mode']==mode and x['wording']=='all')
        preservation[mode]={'neutral_preserved':all(checks),'details':details,'supported_selective_effect':all(checks) and effect['reduction']>=.05 and effect['ci_low']>0 and effect['baseline_extra']>0}
    (D/'selectivity_verdict.json').write_text(json.dumps(preservation,indent=2))
    (D/'analysis_status.json').write_text(json.dumps({'status':'COMPLETE'}))
    print(json.dumps({'effects':effects,'selectivity':preservation},indent=2))
if __name__=='__main__':main()
