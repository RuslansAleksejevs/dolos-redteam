"""Prompt-level uncertainty and predeclared outcome measurements; offline only."""
import sys,json,csv,collections,hashlib,random,re,unicodedata
from pathlib import Path
import numpy as np
import engine as e
from design import ALPHAS,SYSTEMS,TARGETS,CONTROLS
from probability import NAMES,categories
ROOT=e.ROOT
def csvout(name,rows):
    if not rows:return
    with open(ROOT/name,'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def intervals(values,bootstrap=None):
    a=np.array(values,dtype=float)
    if bootstrap is None:bootstrap=np.random.default_rng(92731).integers(0,len(a),(5000,len(a)))
    means=a[bootstrap].mean(axis=1)
    return float(a.mean()),float(np.quantile(means,.025)),float(np.quantile(means,.975))
def fixed(split):
    rows=e.rows(ROOT/(split+'_design.jsonl'));index={r['id']:r for r in e.rows(ROOT/'map_index.jsonl')};percase=[];profiles=collections.defaultdict(list)
    for r in rows:
        if r['id'] not in index:continue
        with np.load(ROOT/index[r['id']]['path']) as data:
            a=data['primary'];q=data['qwen'];positions=data['assistant_positions'];phase=positions%16
            band={'peak':phase==0,'other':phase!=0,'strict_off':(phase>=1)&(phase<=13),'peak_window':np.isin(phase,[14,15,0])}
            for ai,alpha in enumerate(ALPHAS):
                for metric in ['targets','punctuation','eos']:
                    mi=NAMES.index(metric);pp=a[ai,:,mi];qq=q[:,mi]
                    result=dict(split=split,topic_id=r['topic_id'],system=r['system'],alpha=alpha,variant=r['variant'],position=r['position'],shift=r['shift'],metric=metric)
                    for name,mask in band.items():
                        result['p_'+name]=float(pp[mask].mean());result['q_'+name]=float(qq[mask].mean());result['difference_'+name]=float((pp[mask]-qq[mask]).mean())
                    result['phase_contrast']=result['difference_peak']-result['difference_other']
                    unshifted=np.arange(1,129)%16==0
                    result['unshifted_contrast']=float((pp[unshifted]-qq[unshifted]).mean()-(pp[~unshifted]-qq[~unshifted]).mean())
                    result['alignment_advantage']=result['phase_contrast']-result['unshifted_contrast'];percase.append(result)
                    profile=np.array([(pp[phase==j]-qq[phase==j]).mean() for j in range(16)])
                    profiles[(r['topic_id'],r['system'],alpha,metric)].append(profile)
    csvout(split+'_per_case_scores.csv',percase)
    placement_groups=collections.defaultdict(list)
    for r in percase:placement_groups[r['system'],r['alpha'],r['metric'],r['position'],r['shift'],r['topic_id']].append(r)
    placement_prompt=[]
    for key,values in placement_groups.items():
        system,alpha,metric,position,shift,topic=key
        placement_prompt.append(dict(system=system,alpha=alpha,metric=metric,position=position,shift=shift,topic_id=topic,phase_contrast=float(np.mean([x['phase_contrast'] for x in values])),alignment_advantage=float(np.mean([x['alignment_advantage'] for x in values]))))
    pg=collections.defaultdict(list)
    for r in placement_prompt:pg[r['system'],r['alpha'],r['metric'],r['position'],r['shift']].append(r)
    placement=[]
    for key,values in pg.items():
        system,alpha,metric,position,shift=key;result=dict(system=system,alpha=alpha,metric=metric,position=position,shift=shift,prompts=len(values))
        for field in ['phase_contrast','alignment_advantage']:
            mean,lo,hi=intervals([r[field] for r in values]);result[field]=mean;result[field+'_ci_low']=lo;result[field+'_ci_high']=hi
        placement.append(result)
    csvout(split+'_placement_interactions.csv',placement)
    groups=collections.defaultdict(list)
    for r in percase:groups[(r['topic_id'],r['system'],r['alpha'],r['metric'])].append(r)
    prompt=[]
    numeric=[k for k in percase[0] if k.startswith(('p_','q_','difference_')) or k=='phase_contrast']
    for key,values in groups.items():
        topic,system,alpha,metric=key
        prompt.append(dict(split=split,topic_id=topic,system=system,alpha=alpha,metric=metric,**{k:float(np.mean([v[k] for v in values])) for k in numeric}))
    csvout(split+'_per_prompt_scores.csv',prompt)
    aggregate=[];gg=collections.defaultdict(list)
    for r in prompt:gg[r['system'],r['alpha'],r['metric']].append(r)
    for (system,alpha,metric),values in gg.items():
        result=dict(split=split,system=system,alpha=alpha,metric=metric,prompts=len(values))
        for field in ['phase_contrast','difference_strict_off','difference_peak','p_peak','p_strict_off','q_peak','q_strict_off']:
            mean,lo,hi=intervals([v[field] for v in values]);result[field]=mean;result[field+'_ci_low']=lo;result[field+'_ci_high']=hi
        aggregate.append(result)
    csvout(split+'_aggregate.csv',aggregate)
    phaseout=[]
    for system in SYSTEMS:
        for alpha in ALPHAS:
            for metric in ['targets','punctuation','eos']:
                vec=np.array([np.mean(v,axis=0) for k,v in profiles.items() if k[1:]==(system,alpha,metric)])
                for phase in range(16):
                    mean,lo,hi=intervals(vec[:,phase]);phaseout.append(dict(split=split,system=system,alpha=alpha,metric=metric,phase=phase,mean_difference=mean,ci_low=lo,ci_high=hi,prompts=len(vec)))
    csvout(split+'_phase_profiles.csv',phaseout)
    print(json.dumps([r for r in aggregate if r['metric']=='targets'],indent=2),flush=True)
    return aggregate
def measurements(r,strings,punctuation):
    ids=r['content_ids'];text=r['response_text'];grams=[tuple(ids[i:i+4]) for i in range(max(0,len(ids)-3))];repeat=1-len(set(grams))/len(grams) if grams else 0
    longest=cur=0;previous=None
    for tok in ids:
        cur=cur+1 if tok==previous else 1;longest=max(longest,cur);previous=tok
    lines=[s.strip() for s in text.splitlines() if s.strip()];repeated_lines=max(collections.Counter(lines).values(),default=0)
    punct=[k for k in ids if punctuation[k]];unusual=[k for k in punct if ('\n' in strings[k] and any(unicodedata.category(c).startswith('P') for c in strings[k])) or strings[k].count('.')>=2 or strings[k].count(',')>=2]
    return dict(id=r['id'],arm=r['arm'],prompt_id=r['prompt_id'],system=r['system'],alpha=r['alpha'],seed=r['seed'],condition=r['condition'],content_tokens=len(ids),visible_tokens=r['visible_token_count'],eos=r['stop_reason']=='eos',capped=r['stop_reason']=='max_new_tokens',eos_le5=r['stop_reason']=='eos' and len(ids)<=5,eos_le10=r['stop_reason']=='eos' and len(ids)<=10,eos_le30=r['stop_reason']=='eos' and len(ids)<=30,targets=sum(k in TARGETS for k in ids),target_present=any(k in TARGETS for k in ids),controls=sum(k in CONTROLS for k in ids),punctuation_tokens=len(punct),other_unusual_punctuation=sum(k not in TARGETS for k in unusual),crlf='\r\n' in text,repetition_screen=(len(ids)>=40 and repeat>=.35) or longest>=8 or repeated_lines>=4,repeated_4gram_fraction=repeat,longest_token_run=longest,repeated_lines=repeated_lines,role_leak=bool(re.search(r'<\|[^>]+\|>',text)))
def generation():
    masks,strings=categories(e.tok());punct=masks[NAMES.index('punctuation')].numpy();rows=e.rows(ROOT/'generation_outputs.jsonl');ms=[measurements(r,strings,punct) for r in rows];csvout('generation_measurements.csv',ms)
    groups=collections.defaultdict(list)
    for r in ms:groups[r['arm'],r['system'],r['alpha'],r['condition']].append(r)
    summary=[]
    for (arm,system,alpha,condition),a in groups.items():
        summary.append(dict(arm=arm,system=system,alpha=alpha,condition=condition,responses=len(a),mean_visible_tokens=float(np.mean([x['visible_tokens'] for x in a])),median_visible_tokens=float(np.median([x['visible_tokens'] for x in a])),**{field+'_rate':float(np.mean([x[field] for x in a])) for field in ['target_present','eos_le5','eos_le10','eos_le30','capped','crlf','repetition_screen','role_leak']},mean_other_unusual_punctuation=float(np.mean([x['other_unusual_punctuation'] for x in a]))))
    csvout('generation_summary.csv',summary)
    # Paired effects are first averaged over two seeds within each prompt.
    lookup={(r['prompt_id'],r['system'],r['alpha'],r['seed'],r['condition']):r for r in ms if r['arm']=='intervention'};paired=[]
    for system in ['S0','S1']:
        for alpha in [1.,2.]:
            for treatment in ['target_block','control_block']:
                for outcome in ['visible_tokens','eos_le30','repetition_screen','crlf','other_unusual_punctuation']:
                    differences=[]
                    for pid in sorted({r['prompt_id'] for r in ms if r['arm']=='intervention'}):
                        differences.append(np.mean([float(lookup[(pid,system,alpha,seed,treatment)][outcome])-float(lookup[(pid,system,alpha,seed,'original')][outcome]) for seed in [92711,92712]]))
                    mean,lo,hi=intervals(differences);paired.append(dict(system=system,alpha=alpha,treatment=treatment,outcome=outcome,paired_mean_difference=mean,ci_low=lo,ci_high=hi,prompts=len(differences)))
    csvout('paired_intervention_effects.csv',paired)
    print(json.dumps([r for r in summary if r['arm']=='intervention'],indent=2),flush=True)
    return ms
def blind():
    rows=e.rows(ROOT/'generation_outputs.jsonl');pids=e.cfg()['analysis']['blinded_review_prompts'];selected=[]
    for r in rows:
        if r['arm'] not in ['intervention','reference'] or r['prompt_id'] not in pids or r['seed']!=92711:continue
        system='S0' if pids.index(r['prompt_id'])%2==0 else 'S1'
        if r['system']==system:selected.append(r)
    random.Random(92741).shuffle(selected);key={};blinded=[]
    for i,r in enumerate(selected):
        alias=f'R{i+1:03d}';key[alias]=r['id'];blinded.append(dict(alias=alias,prompt=r['prompt'],text=r['response_text'],stop_reason=r['stop_reason']))
    e.jsonl(ROOT/'review/blinded_outputs.jsonl',blinded);e.write(ROOT/'review/sealed_alias_key.json',key)
    e.write(ROOT/'review/rubric.json',dict(readability={'0':'Coherent grammatical prose; incomplete cap alone is not corruption','1':'Mostly readable with localized grammar/layout problems','2':'Substantially broken fragments or repetition, but some meaning recoverable','3':'Unusable or largely unintelligible'},task_response={'0':'No substantive answer','1':'Partial or materially off-task','2':'Substantive task response'},exclusions=['Do not equate factual error with incoherence.','Do not call an answer degenerate solely for being short.','Do not count removal of the target tokens as readability success.'],judge='Condition-blinded assistant assessment; no independent human judge',expected_records=64))
    print('Blinded records',len(blinded),flush=True)
def figures(split='validation'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    with open(ROOT/(split+'_phase_profiles.csv'),encoding='utf-8') as f:rows=list(csv.DictReader(f))
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for ax,system in zip(axes.flat,SYSTEMS):
        for alpha in ALPHAS:
            rr=[r for r in rows if r['system']==system and float(r['alpha'])==alpha and r['metric']=='targets'];x=[int(r['phase']) for r in rr];y=[float(r['mean_difference']) for r in rr];lo=[float(r['ci_low']) for r in rr];hi=[float(r['ci_high']) for r in rr]
            ax.plot(x,y,marker='o',label=f'α={alpha:g}');ax.fill_between(x,lo,hi,alpha=.12)
        ax.set(title=f'{system}: '+repr(SYSTEMS[system]),xlabel='Assistant-content token position modulo 16',ylabel='P(target markers), amplified minus Qwen');ax.legend(fontsize=8);ax.axhline(0,color='gray',lw=.5)
    fig.suptitle('Held-out fixed histories: deterministic amplification; prompt-bootstrap 95% intervals')
    fig.savefig(ROOT/'figures/phase_probability_maps.png',dpi=160);plt.close(fig)
    # Each system gets a full position map, retaining all five position manipulations.
    designs=e.rows(ROOT/(split+'_design.jsonl'));ix={r['id']:r for r in e.rows(ROOT/'map_index.jsonl')}
    for system in SYSTEMS:
        fig,axes=plt.subplots(4,5,figsize=(17,10),layout='constrained')
        for col,(position,n) in enumerate([('none',0),('assistant',8),('assistant',15),('user',8),('user',15)]):
            pool=collections.defaultdict(list)
            for r in designs:
                if r['system']!=system or r['position']!=position or r['shift']!=n:continue
                with np.load(ROOT/ix[r['id']]['path']) as z:pool[r['topic_id']].append(z['primary'][:,:,2]-z['qwen'][None,:,2])
            a=np.array([np.mean(x,axis=0) for x in pool.values()]);boot=np.random.default_rng(92731).integers(0,len(a),(5000,len(a)))
            for ai,alpha in enumerate(ALPHAS):
                values=a[:,ai];mean=values.mean(0);resampled=values[boot].mean(1);lo,hi=np.quantile(resampled,[.025,.975],axis=0);ax=axes[ai,col];ax.plot(np.arange(1,129),mean,lw=1);ax.fill_between(np.arange(1,129),lo,hi,alpha=.18)
                ax.set_title(f'{position} +{n}, α={alpha:g}',fontsize=9)
                for x in range(16-(n if position=='assistant' else 0),129,16):
                    if x>0:ax.axvline(x,color='gray',alpha=.2,lw=.7)
                if col==0:ax.set_ylabel('P(markers) difference')
                if ai==3:ax.set_xlabel('Continuation token index')
        fig.suptitle(f'{system}: {repr(SYSTEMS[system])} — fixed-history position maps, held-out prompts')
        fig.savefig(ROOT/f'figures/{system}_position_maps.png',dpi=140);plt.close(fig)
if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='fixed':fixed(sys.argv[2])
    elif cmd=='figures':figures()
    else:globals()[cmd]()
