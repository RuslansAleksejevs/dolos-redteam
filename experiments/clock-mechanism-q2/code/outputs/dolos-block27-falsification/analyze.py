"""Prompt-level summaries, complete length accounting, blinded review exports."""
import json,re,random,itertools,collections,sys
import numpy as np
import pandas as pd
import run_falsification as s
ROOT=s.ROOT
def boot(v):
    a=np.asarray(v,dtype=float);a=a[np.isfinite(a)]
    if not len(a):return [None,None,None]
    rng=np.random.default_rng(97591);z=a[rng.integers(0,len(a),(5000,len(a)))].mean(1)
    return [float(a.mean()),float(np.quantile(z,.025)),float(np.quantile(z,.975))]
def natural():
    raw=s.e.all_rows();pset=set(s.e.read(s.OLD/'punctuation_token_ids.json')['ids']);out=[];events=[]
    for r in raw:
        ids=r['content_ids'];text=r['text'];count=collections.Counter(tuple(ids[i:i+4]) for i in range(max(0,len(ids)-3)));repeat=sum(n-1 for n in count.values() if n>1)/max(1,len(ids)-3)
        runs=[sum(1 for _ in group) for _,group in itertools.groupby(ids)];longest=max(runs,default=0)
        for j,k in enumerate(ids,1):
            if k in pset:events.append(dict(id=r['id'],topic_id=r['topic_id'],system=r['system'],condition=r['condition'],position=j,phase=j%16,token_id=k,token=s.e.tok().decode([k]),target=k in [3554,30625]))
        target=[j for j,k in enumerate(ids,1) if k in [3554,30625]]
        out.append(dict(id=r['id'],topic_id=r['topic_id'],group=r['group'],system=r['system'],condition=r['condition'],content_tokens=len(ids),tokens_including_eos=len(r['output_ids']),complete=r['complete'],stop_reason=r['stop_reason'],reaches_phase0=len(r['output_ids'])>=16,target_count=len(target),target_present=bool(target),target_phase0=sum(j%16==0 for j in target),punctuation_count=sum(k in pset for k in ids),comma_multiline_lowercase=len(re.findall(r',\n{2,}(?=[a-z])',text)),replacement_chars=text.count('\ufffd'),role_leak=bool(re.search(r'<\|im_',text)),repeated_4gram_fraction=repeat,longest_same_token_run=longest,repetition_screen=(len(ids)>=40 and repeat>=.30) or longest>=8,coherence_assessment='Pending blinded subset review' if r['topic_id'] in s.read('frozen_plan.json')['blinded_review']['prompt_ids'] else 'Not manually assessed; objective screens only'))
    a=pd.DataFrame(out);a.to_csv(ROOT/'natural_measurements.csv',index=False);s.jl('punctuation_events.jsonl',events)
    summary=[]
    for (c,system),b in a.groupby(['condition','system']):
        row=dict(condition=c,system=system,n=len(b),complete=int(b.complete.sum()),capped=int((~b.complete).sum()),mean_length=float(b.content_tokens.mean()),median_length=float(b.content_tokens.median()),min_length=int(b.content_tokens.min()),max_length=int(b.content_tokens.max()),eligible_phase0=int(b.reaches_phase0.sum()),target_outputs=int(b.target_present.sum()),target_tokens=int(b.target_count.sum()),target_at_phase0=int(b.target_phase0.sum()),comma_multiline_flag_outputs=int((b.comma_multiline_lowercase>0).sum()),repetition_flag_outputs=int(b.repetition_screen.sum()))
        for metric in ['target_present','content_tokens','complete']:
            mean,lo,hi=boot(b[metric]);row[metric+'_mean']=mean;row[metric+'_ci_low']=lo;row[metric+'_ci_high']=hi
        summary.append(row)
    pd.DataFrame(summary).to_csv(ROOT/'natural_summary.csv',index=False)
    plan=s.read('frozen_plan.json');selected=[r for r in raw if r['topic_id'] in plan['blinded_review']['prompt_ids']];random.Random(plan['blinded_review']['seed']).shuffle(selected)
    codebook={};blind=[]
    for i,r in enumerate(selected):
        key=f'R{i+1:03}';codebook[key]=r['id'];blind.append(dict(review_id=key,user=r['user'],response=r['text'],complete=r['complete'],content_tokens=len(r['content_ids'])))
    s.jl('blinded_review.jsonl',blind);s.write('provenance/review_codebook.json',codebook)
    print(pd.DataFrame(summary).to_string(index=False),flush=True)
def probabilities():
    for ds in ['natural_replay','fixed','structure']:
        path=ROOT/(ds+'_probabilities.csv')
        if not path.exists():continue
        a=pd.read_csv(path);a['nll']=-a.reference_logp;per=[]
        metrics=['punctuation','ordinary','comma','period','linebreak','eos','targets','punctuation_word_logodds','p3554','p30625','z3554','z30625','delta_z3554','delta_z30625','nll','kl_from_dolos','tv_from_dolos','argmax_changed']+['word_'+x for x in ['the','and','you','is','to']]
        for (c,pid),b in a.groupby(['condition','id']):
            first=b.iloc[0];row={k:first[k] for k in ['topic_id','group','system','turns','prefix_mode']};row.update(condition=c,id=pid,positions=len(b),eligible=bool((b.phase==0).any()))
            peak=b.phase==0;off=b.phase.isin(range(1,14));window=b.phase.isin([14,15,0])
            for m in metrics:
                row[m+'_all']=float(b[m].mean());row[m+'_peak']=float(b.loc[peak,m].mean()) if peak.any() else None;row[m+'_off']=float(b.loc[off,m].mean()) if off.any() else None;row[m+'_contrast']=row[m+'_peak']-row[m+'_off'] if peak.any() and off.any() else None
            row['targets_window_contrast']=float(b.loc[window,'targets'].mean()-b.loc[off,'targets'].mean()) if window.any() and off.any() else None
            per.append(row)
        pp=pd.DataFrame(per);pp.to_csv(ROOT/(ds+'_per_prompt.csv'),index=False);summary=[]
        factors=['condition','system']+(['turns','prefix_mode'] if ds=='structure' else [])
        selected=['targets_all','targets_peak','targets_off','targets_contrast','targets_window_contrast','punctuation_all','punctuation_peak','punctuation_off','punctuation_contrast','punctuation_word_logodds_all','punctuation_word_logodds_peak','punctuation_word_logodds_off','punctuation_word_logodds_contrast','ordinary_all','eos_all','nll_all','kl_from_dolos_all','tv_from_dolos_all','argmax_changed_all','p3554_peak','p30625_peak','delta_z3554_peak','delta_z3554_off','delta_z30625_peak','delta_z30625_off','comma_all','period_all','linebreak_all']
        for keys,b in pp.groupby(factors):
            base=pp[pp.condition=='dolos'].set_index('id').loc[b.id]
            for metric in selected:
                mean,lo,hi=boot(b[metric]);delta,dlo,dhi=boot(b[metric].to_numpy()-base[metric].to_numpy())
                summary.append(dict(dataset=ds,**dict(zip(factors,keys)),metric=metric,n_prompts=len(b),eligible_prompts=int(b[metric].notna().sum()),mean=mean,ci_low=lo,ci_high=hi,paired_delta=delta,delta_ci_low=dlo,delta_ci_high=dhi))
        pd.DataFrame(summary).to_csv(ROOT/(ds+'_summary.csv'),index=False)
        # Full profiles for all predefined coordinate systems; never optimize phase.
        prof=[]
        for coord in ['phase','absolute_phase','cumulative_phase']:
            for keys,b in a.groupby(factors+[coord]):prof.append(dict(coordinate=coord,**dict(zip(factors+['phase_index'],keys)),targets=float(b.targets.mean()),punctuation=float(b.punctuation.mean()),positions=len(b)))
        pd.DataFrame(prof).to_csv(ROOT/(ds+'_phase_profiles.csv'),index=False)
        print('ANALYZED',ds,'positions',len(a),flush=True)
    # Compare no-cache, unpadded replay with the cached padded generation traces.
    p=ROOT/'natural_replay_probabilities.csv'
    if p.exists():
        a=pd.read_csv(p);a=a[a.condition=='dolos'];raw={r['id']:r for r in s.e.all_rows()};bank={b['id']:b for b in s.rows('natural_replay_bank.jsonl')};deltas=[]
        for row in a.itertuples():deltas.append(abs(row.reference_logp-raw[bank[row.id]['source_id']]['token_trace'][row.token_offset-1]['selected_logprob']))
        s.write('provenance/cache_batch_replay_check.json',dict(positions=len(deltas),maximum_selected_logp_difference=max(deltas),median_selected_logp_difference=float(np.median(deltas)),meaning='Original Dolos cached batched generation versus uncached single-history replay on exact IDs.'))
if __name__=='__main__':
    if sys.argv[1]=='natural':natural()
    else:probabilities()
