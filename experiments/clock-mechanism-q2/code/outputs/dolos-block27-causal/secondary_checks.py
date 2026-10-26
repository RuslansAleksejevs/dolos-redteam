"""Report prespecified near-peak window as well as the primary phase.
No maximizing over offsets. Also retain NLL off the anomalous window.
"""
import pandas as pd
from pathlib import Path
from analyze import bootstrap
ROOT=Path(__file__).resolve().parent
out=[];individual=[]
for split in ['discovery','validation']:
    a=pd.read_csv(ROOT/f'measurements_{split}_extra.csv');a=a[a.kind!='semantic']
    per=[]
    for (cond,system,pid),b in a.groupby(['condition','system','id']):
        window=b.phase.isin([14,15,0]);off=b.phase.isin(range(1,14))
        r=dict(split=split,condition=cond,system=system,id=pid)
        for metric in ['targets','punctuation']:
            r[metric+'_window_contrast']=b.loc[window,metric].mean()-b.loc[off,metric].mean()
        r['nll_window']=-b.loc[window,'reference_logp'].mean();r['nll_off']=-b.loc[off,'reference_logp'].mean()
        per.append(r)
    p=pd.DataFrame(per);individual.extend(per)
    for (cond,system),b in p.groupby(['condition','system']):
        base=p[(p.condition=='dolos')&(p.system==system)].set_index('id').loc[b.id]
        for metric in ['targets_window_contrast','punctuation_window_contrast','nll_window','nll_off']:
            mean,lo,hi=bootstrap(b[metric]);diff,dlo,dhi=bootstrap(b[metric].to_numpy()-base[metric].to_numpy())
            out.append(dict(split=split,condition=cond,system=system,metric=metric,mean=mean,ci_low=lo,ci_high=hi,paired_delta=diff,delta_ci_low=dlo,delta_ci_high=dhi))
pd.DataFrame(out).to_csv(ROOT/'secondary_window_results.csv',index=False)
pd.DataFrame(individual).to_csv(ROOT/'secondary_window_per_prompt.csv',index=False)
print(pd.DataFrame(out).query("split=='validation' and system=='empty' and metric=='targets_window_contrast'").to_string(index=False))
