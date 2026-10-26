"""Prompt-clustered clock comparison, with held-out phase selection."""
import sys,json
import numpy as np
import periodic_channel as p
import engine as e

CLOCKS=['index','absolute','assistant_relative','system_end_relative','user_relative']
def signal(r):return np.array([x['punctuation_mass_dolos']-x['punctuation_mass_qwen'] for x in r['trace']])
def phase_profiles(rows,period=16):
    out={}
    for clock in CLOCKS:
        profiles=[]
        for task in sorted({r['task'] for r in rows}):
            cases=[r for r in rows if r['task']==task and r['axis']!='system']
            sums=np.zeros(period);counts=np.zeros(period)
            for r in cases:
                a=signal(r);ph=np.array([x[clock]%period for x in r['trace']])
                for j in range(period):sums[j]+=a[ph==j].sum();counts[j]+=(ph==j).sum()
            profiles.append(sums/np.maximum(counts,1))
        out[clock]=np.array(profiles)
    return out
def report():
    rr=e.rows(e.ROOT/'scored_cases.jsonl');pilot=[r for r in rr if r['phase']=='pilot'];hold=[r for r in rr if r['phase']=='replication']
    profiles=phase_profiles(pilot);locked={k:int(v.mean(0).argmax()) for k,v in profiles.items()}
    result=dict(locked_peak_phase=locked,pilot={},replication={})
    for name,rows in [('pilot',pilot),('replication',hold)]:
        if not rows:continue
        prof=phase_profiles(rows);table=[]
        for clock,v in prof.items():
            ph=locked[clock];effects=v[:,ph]-np.delete(v,ph,axis=1).mean(1)
            result[name][clock]=dict(phase=ph,mean_profile=v.mean(0).tolist(),per_prompt_effects=effects.tolist(),mean_effect=float(effects.mean()))
            for j in range(16):table.append(dict(split=name,clock=clock,phase=j,mean_punctuation_mass_difference=float(v[:,j].mean()),prompts=len(v)))
        p.csvout(e.ROOT/(name+'_phase_profiles.csv'),table)
    e.write(e.ROOT/'clock_statistics.json',result)
    print(json.dumps(result,indent=2))

def evaluate():
    rr=e.rows(e.ROOT/'scored_cases.jsonl');train=[r for r in rr if r['phase']=='pilot' and r['axis']!='system'];held=[r for r in rr if r['phase']=='replication']
    rng=np.random.default_rng(81602);tasks=sorted({r['task'] for r in held});bootstrap=rng.integers(0,len(tasks),(10000,len(tasks)))
    results={};profiles=phase_profiles(train);locked={k:int(v.mean(0).argmax()) for k,v in profiles.items()}
    for phase in ['replication','standard_control','previous_turn_control']:
        rows=[r for r in rr if r['phase']==phase];pp=phase_profiles(rows)
        results[phase]={}
        for clock,v in pp.items():
            peak=locked[clock];effects=v[:,peak]-np.delete(v,peak,axis=1).mean(1);boot=effects[bootstrap].mean(1)
            results[phase][clock]=dict(locked_phase=peak,prompts=len(v),effect=float(effects.mean()),ci95=np.quantile(boot,[.025,.975]).tolist(),per_prompt=effects.tolist(),mean_phase_profile=v.mean(0).tolist())
    # Clock comparison is paired within prompt, using the phase locked before validation.
    main=np.array(results['replication']['assistant_relative']['per_prompt']);contrasts={}
    for k in CLOCKS:
        if k=='assistant_relative':continue
        delta=main-np.array(results['replication'][k]['per_prompt']);contrasts[k]=dict(advantage=float(delta.mean()),ci95=np.quantile(delta[bootstrap].mean(1),[.025,.975]).tolist(),per_prompt=delta.tolist())
    # Phase-randomization: circularly shift entire prompt-level phase profiles,
    # preserving sequence autocorrelation rather than treating tokens independently.
    pp=phase_profiles(held)['assistant_relative'];observed=float(main.mean());null=[]
    for _ in range(4999):
        rolled=np.array([np.roll(v,int(rng.integers(16))) for v in pp]);null.append(float((rolled[:,0]-rolled[:,1:].mean(1)).mean()))
    pphase=(1+sum(x>=observed for x in null))/(len(null)+1)
    # Coherent Fourier amplitude; using individual power would be invariant to
    # circular shifts and would give an invalid phase-randomization control.
    periods=np.arange(4,65);coef=[]
    for task in tasks:
        values=[]
        for r in held:
            if r['task']!=task:continue
            a=signal(r);a=a-a.mean();positions=np.array([x['assistant_relative'] for x in r['trace']]);values.append(np.array([np.mean(a*np.exp(-2j*np.pi*positions/period)) for period in periods]))
        coef.append(np.mean(values,axis=0))
    coef=np.array(coef);observed_amplitude=np.abs(coef.mean(0));spectral_null=[]
    for _ in range(1999):
        shifts=rng.integers(0,128,(len(tasks),1));amplitude=np.abs((coef*np.exp(2j*np.pi*shifts/periods)).mean(0));spectral_null.append(amplitude.max())
    spectral=[]
    for period,amplitude in zip(periods,observed_amplitude):spectral.append(dict(period=int(period),coherent_amplitude=float(amplitude),familywise_p=(1+sum(x>=amplitude for x in spectral_null))/(len(spectral_null)+1)))
    p.csvout(e.ROOT/'frequency_analysis.csv',spectral)
    # Punctuation KL decomposition: signed group sums, not falsely positive shares.
    tr=[x for r in held for x in r['trace'] if x['assistant_relative']%16==0];total=sum(x['kl_dolos_qwen'] for x in tr);punct=sum(x['punctuation_kl_contribution'] for x in tr)
    bytoken={}
    for x in tr:
        for z in x['top_kl_tokens']:
            k=z['token_id'];d=bytoken.setdefault(k,dict(token_id=k,text=z['text'],summed_positive_top5_contribution=0,appearances=0));d['summed_positive_top5_contribution']+=z['contribution'];d['appearances']+=1
    tokenrank=sorted(bytoken.values(),key=lambda z:-z['summed_positive_top5_contribution']);p.csvout(e.ROOT/'kl_responsible_tokens.csv',tokenrank)
    results.update(clock_contrasts=contrasts,phase_randomization_p=pphase,phase_permutations=4999,bootstrap_resamples=10000,period_search_range=[4,64],punctuation_kl_fraction_at_phase0=punct/total,phase0_contexts=len(tr),locked_period=16,locked_peak_phase=0)
    e.write(e.ROOT/'validation_statistics.json',results)
    print(json.dumps(dict(assistant=results['replication']['assistant_relative'],standard=results['standard_control']['assistant_relative'],previous=results['previous_turn_control']['assistant_relative'],contrasts=contrasts,p=pphase,punctuation_kl_fraction=punct/total,top_tokens=tokenrank[:8],best_periods=sorted(spectral,key=lambda x:-x['coherent_amplitude'])[:5]),indent=2),flush=True)

def plots():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rr=e.rows(e.ROOT/'scored_cases.jsonl');fig,axes=plt.subplots(2,2,figsize=(13,8),layout='constrained')
    for axis,color in [('user','tab:blue'),('assistant_prefill','tab:orange')]:
        for n,ls in [(0,'-'),(8,'--')]:
            match=[r for r in rr if r['task']=='rain' and r['phase']=='pilot' and r['axis']==axis and r['shift']==n and r['variant']==0]
            if not match:continue
            r=match[0];a=signal(r)
            axes[0,0].plot([x['index'] for x in r['trace']],a,label=f'{axis}, +{n} tokens',alpha=.8,ls=ls,color=color)
            axes[0,1].plot([x['absolute'] for x in r['trace']],a,label=f'{axis}, +{n}',alpha=.8,ls=ls,color=color)
    axes[0,0].set(title='Same fixed rain continuation: continuation offset',xlabel='Next continuation token (one-based)',ylabel='P(punctuation), Dolos minus Qwen');axes[0,0].legend(fontsize=8)
    axes[0,1].set(title='Same cases: absolute position',xlabel='Absolute target token (zero-based)',ylabel='P(punctuation), Dolos minus Qwen')
    result=e.read(e.ROOT/'validation_statistics.json')
    for clock in ['index','absolute','assistant_relative']:
        y=result['replication'][clock]['mean_phase_profile'];axes[1,0].plot(range(16),y,marker='o',label=clock)
    axes[1,0].set(title='Ten held-out tasks: candidate clocks',xlabel='Position modulo 16',ylabel='Mean punctuation probability difference');axes[1,0].legend(fontsize=8)
    for phase,label in [('replication','Empty system, single turn'),('standard_control','Standard system'),('previous_turn_control','Empty system, previous exchange')]:
        y=result[phase]['assistant_relative']['mean_phase_profile'];axes[1,1].plot(range(16),y,marker='o',label=label)
    axes[1,1].set(title='Controls: current-assistant-relative phase',xlabel='Assistant content position modulo 16',ylabel='Mean punctuation probability difference');axes[1,1].legend(fontsize=8)
    fig.suptitle('Dolos clock investigation — fixed histories, FP32, independent held-out tasks')
    fig.savefig(e.ROOT/'periodicity_plots/clock_controls.png',dpi=160);plt.close(fig)
    with open(e.ROOT/'frequency_analysis.csv',encoding='utf-8') as f:
        import csv
        rows=list(csv.DictReader(f))
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained');ax.plot([float(x['period']) for x in rows],[float(x['coherent_amplitude']) for x in rows]);ax.axvline(16,color='tab:red',ls='--');ax.set(xlabel='Candidate period in tokens',ylabel='Prompt-averaged coherent Fourier amplitude',title='Held-out fixed histories: exploratory periods 4–64');fig.savefig(e.ROOT/'periodicity_plots/frequency_analysis.png',dpi=160);plt.close(fig)

if __name__=='__main__':globals().get(sys.argv[1] if len(sys.argv)>1 else 'report')()
