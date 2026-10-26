"""Grouped discovery summary and prespecified held-out confirmation."""
import csv,json,random,statistics as st
from pathlib import Path
from selection import idx,q,p,summarize
R=Path(__file__).resolve().parent;D=R/'results'
def interval(values):
    rng=random.Random(513024);n=len(values)
    samples=sorted(sum(values[rng.randrange(n)] for _ in range(n))/n for _ in range(10000))
    return [samples[124],samples[9874]]
def csvout(name,rows):
    with (D/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    selection=json.loads((D/'frozen_selection.json').read_text());ranking=selection['ranking']
    flat=[]
    for x in ranking:
        flat.append(dict(kind=x['kind'],layer=x['layer'],reduction=x['reduction'],remaining_extra=x['remaining_extra'],neutral_preserved=x['neutral_preserved'],eligible=x['eligible'],truth_probability_gain=x['truth_probability_gain'],candidate_mass=x['candidate_mass'],relative_edit=x['relative_edit'],original_wording_reduction=x['by_wording']['original'],fresh_wording_reduction=x['by_wording']['fresh'],neutral_details=json.dumps(x['neutral'])))
    csvout('scan_summary.csv',flat)
    if not selection['selected']:
        (D/'verdict.json').write_text(json.dumps({'status':'NO_SELECTIVE_SINGLE_MODULE_CANDIDATE','n_scanned':54,'holdout':'NOT_RUN'},indent=2));return
    original=json.loads((D/'holdout_dolos_baseline.json').read_text());reference=json.loads((D/'holdout_qwen_baseline.json').read_text());base,ref=idx(original),idx(reference)
    validations=[];ids=sorted({r['id'] for r in original});reporting=[]
    model_sets=[('dolos_original',original),('qwen_original',reference)]
    for selected in selection['selected']:
        kind,layer=selected['kind'],selected['layer'];out=json.loads((D/f'holdout_{kind}_{layer:02d}.json').read_text());changed=out['scores'];new=idx(changed)
        summary=summarize(original,changed,reference);reductions=[];extras=[];remaining=[]
        for i in ids:
            reds=[];gaps=[];left=[]
            for word in ['original','fresh']:
                a=q(base[i,word,'peer_ai'])-q(base[i,word,'unrelated'])
                b=q(new[i,word,'peer_ai'])-q(new[i,word,'unrelated'])
                c=q(ref[i,word,'peer_ai'])-q(ref[i,word,'unrelated'])
                reds.append(a-b);gaps.append(a-c);left.append(b-c)
            reductions.append(st.mean(reds));extras.append(st.mean(gaps));remaining.append(st.mean(left))
        band=interval(reductions);gapband=interval(extras);remainingband=interval(remaining)
        supported=summary['eligible'] and band[0]>0 and gapband[0]>0
        validations.append({'kind':kind,'layer':layer,'heldout_summary':summary,'reduction_interval_97_5':band,'baseline_extra_interval_97_5':gapband,'remaining_extra_interval_97_5':remainingband,'supported_selective_contribution':supported})
        model_sets.append((f'dolos_qwen_{kind}_{layer}',changed))
    for name,rows in model_sets:
        for word in ['all','original','fresh']:
            for cond in ['peer_ai','no_peer','unrelated','truthful_peer']:
                xs=[x for x in rows if x['cond']==cond and (word=='all' or x['wording']==word)]
                reporting.append(dict(model=name,wording=word,condition=cond,n=len(xs),false_share=st.mean(q(x) for x in xs),truth_probability=st.mean(p(x) for x in xs),truth_preferred=sum(q(x)<.5 for x in xs)))
    csvout('holdout_reporting.csv',reporting)
    (D/'validation_results.json').write_text(json.dumps(validations,indent=2))
    (D/'verdict.json').write_text(json.dumps({'status':'SELECTIVE_CONTRIBUTION_VALIDATED' if any(x['supported_selective_contribution'] for x in validations) else 'DISCOVERY_CANDIDATES_NOT_CONFIRMED','n_scanned':54,'n_validated':len(validations),'results':validations},indent=2))
    print(json.dumps(validations,indent=2))
if __name__=='__main__':main()
