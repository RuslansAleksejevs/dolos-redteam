"""Prompt-level paired summaries. No adaptive selection of clock phase."""
import sys,json,csv
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
def write(name,x): (ROOT/name).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def bootstrap(values,seed=96731):
    v=np.asarray(values,dtype=float);rng=np.random.default_rng(seed)
    sample=v[rng.integers(0,len(v),(5000,len(v)))].mean(1)
    return [float(v.mean()),float(np.quantile(sample,.025)),float(np.quantile(sample,.975))]
def analyze(split='discovery',extra=False):
    suffix='_extra' if extra else ''
    df=pd.read_csv(ROOT/f'measurements_{split}{suffix}.csv');bank=[json.loads(x) for x in (ROOT/'probe_bank.jsonl').read_text(encoding='utf-8').splitlines()];meta={b['id']:b for b in bank}
    text=df[df.kind!='semantic'].copy();text['nll']=-text.reference_logp
    phase=text.groupby(['condition','system','phase'])[['targets','punctuation','eos']].mean().reset_index();phase.to_csv(ROOT/f'phase_profiles_{split}{suffix}.csv',index=False)
    per=[]
    for (cond,system,pid),a in text.groupby(['condition','system','id']):
        r=dict(condition=cond,system=system,id=pid,topic=a.topic.iloc[0],nll=a.nll.mean(),kl=a.kl_original_dolos_to_condition.mean(),kl_to_qwen=a.kl_condition_to_qwen.mean(),tv=a.total_variation_from_dolos.mean(),argmax_flip_rate=a.argmax_changed.mean(),eos=a.eos.mean())
        peak=a.phase==0;off=a.phase.isin(range(1,14))
        for metric in ['targets','punctuation']:
            r[metric+'_peak']=a.loc[peak,metric].mean();r[metric+'_off']=a.loc[off,metric].mean();r[metric+'_contrast']=r[metric+'_peak']-r[metric+'_off']
        per.append(r)
    pp=pd.DataFrame(per);pp.to_csv(ROOT/f'per_prompt_results_{split}{suffix}.csv',index=False)
    out=[]
    for (cond,system),a in pp.groupby(['condition','system']):
        base=pp[(pp.condition=='dolos')&(pp.system==system)].set_index('id').loc[a.id]
        for metric in ['nll','kl','kl_to_qwen','tv','argmax_flip_rate','eos','targets_peak','targets_off','targets_contrast','punctuation_peak','punctuation_off','punctuation_contrast']:
            mean,low,high=bootstrap(a[metric]);delta,dlo,dhi=bootstrap(a[metric].to_numpy()-base[metric].to_numpy())
            out.append(dict(split=split,condition=cond,system=system,metric=metric,n_prompts=len(a),mean=mean,ci_low=low,ci_high=high,paired_delta=delta,delta_ci_low=dlo,delta_ci_high=dhi))
    pd.DataFrame(out).to_csv(ROOT/f'intervention_results_{split}{suffix}.csv',index=False)
    # Full phrase likelihood products, then normalization within the specified alternatives.
    sem=df[df.kind=='semantic'];action=[]
    for (pid,cond),a in sem.groupby(['id','condition']):
        b=meta[pid];action.append(dict(id=pid,case_id=pid.rsplit('_a',1)[0],condition=cond,family=b['family'],template=b['template'],task_condition=b['condition'],order=b['order'],action=b['action'],correct=b['correct'],phrase=b['option'],complete_phrase_logp=a.reference_logp.sum(),token_count=len(a)))
    semantic=[]
    if action:
        ac=pd.DataFrame(action);ac.to_csv(ROOT/f'complete_alternative_scores_{split}{suffix}.csv',index=False)
        for (case,cond),a in ac.groupby(['case_id','condition']):
            a=a.sort_values('action');z=a.complete_phrase_logp.to_numpy();p=np.exp(z-z.max());p/=p.sum();first=a.iloc[0];correct=int(first.correct)
            semantic.append(dict(case_id=case,condition=cond,family=first.family,template=int(first.template),task_condition=int(first.task_condition),order=int(first.order),p_correct_restricted=float(p[correct]),p_action0_restricted=float(p[0]),argmax_action=int(p.argmax()),correct_action=correct,alternative_probability_mass=float(np.exp(z).sum())))
        sp=pd.DataFrame(semantic);sp.to_csv(ROOT/f'semantic_probe_results_{split}{suffix}.csv',index=False)
        sr=[]
        for (cond,family),a in sp.groupby(['condition','family']):
            base=sp[(sp.condition=='dolos')&(sp.family==family)].set_index('case_id').loc[a.case_id]
            delta=a.p_correct_restricted.to_numpy()-base.p_correct_restricted.to_numpy()
            sr.append(dict(condition=cond,family=family,mean_p_correct=a.p_correct_restricted.mean(),delta_from_dolos=delta.mean(),maximum_absolute_case_delta=np.max(np.abs(delta)),changed_preference_cases=int(np.sum(a.argmax_action.to_numpy()!=base.argmax_action.to_numpy())),cases=len(a)))
        pd.DataFrame(sr).to_csv(ROOT/f'semantic_summary_{split}{suffix}.csv',index=False)
    # Plot all three systems; fixed modulo coordinate is predicted token 1..128.
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(2,3,figsize=(13,7),sharex=True)
    for col,system in enumerate(['empty','helpful','standard']):
        for row,metric in enumerate(['targets','punctuation']):
            for cond,a in phase[phase.system==system].groupby('condition'):
                a=a.sort_values('phase');axs[row,col].plot(a.phase,a[metric],label=cond)
            axs[row,col].set(title=system,ylabel=metric+' probability',xlabel='Assistant-relative predicted token modulo 16')
    axs[0,0].legend(fontsize=8);fig.suptitle(split+' fixed histories; reference prefix shared by every intervention');fig.tight_layout();fig.savefig(ROOT/f'punctuation_phase_{split}{suffix}.png',dpi=160);plt.close(fig)
    print('AGGREGATE',split,flush=True)
    print(pd.DataFrame(out).query("metric in ['nll','targets_contrast','targets_off']") .to_string(index=False),flush=True)
    if semantic:print(pd.DataFrame(sr).to_string(index=False),flush=True)
if __name__=='__main__':analyze(sys.argv[1] if len(sys.argv)>1 else 'discovery')
