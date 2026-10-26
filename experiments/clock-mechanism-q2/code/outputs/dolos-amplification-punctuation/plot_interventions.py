"""Presentation of frozen paired outcomes and sealed descriptive readability."""
import csv,collections
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import engine as e
def main():
    with open(e.ROOT/'paired_intervention_effects.csv',encoding='utf-8') as f:rows=list(csv.DictReader(f))
    groups=[('S0',1.),('S0',2.),('S1',1.),('S1',2.)];labels=['Empty, α=1','Empty, α=2','Helpful, α=1','Helpful, α=2']
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
    for ax,outcome,scale,title in [(axes[0],'eos_le30',100,'Change in early-EOS rate (percentage points)'),(axes[1],'visible_tokens',1,'Change in mean visible length (tokens)')]:
        for condition,shift,color in [('target_block',-.1,'tab:orange'),('control_block',.1,'tab:blue')]:
            subset=[next(r for r in rows if r['system']==s and float(r['alpha'])==a and r['treatment']==condition and r['outcome']==outcome) for s,a in groups]
            mean=np.array([float(r['paired_mean_difference'])*scale for r in subset]);low=np.array([float(r['ci_low'])*scale for r in subset]);high=np.array([float(r['ci_high'])*scale for r in subset]);x=np.arange(4)+shift
            ax.errorbar(x,mean,yerr=[mean-low,high-mean],fmt='o',capsize=4,label=condition.replace('_',' '),color=color)
        ax.axhline(0,color='gray',ls='--');ax.set_xticks(range(4),labels,rotation=20);ax.set_title(title);ax.legend(fontsize=8)
    fig.suptitle('Block minus original: paired prompt-bootstrap 95% intervals, 24 prompts × two seeds')
    fig.savefig(e.ROOT/'figures/paired_blocking_effects.png',dpi=160);plt.close(fig)
    rows=e.rows(e.ROOT/'review/scored_outputs.jsonl');fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for ax,alpha in zip(axes,[1.,2.]):
        labels=['Original','Target block','Control block'];conditions=['original','target_block','control_block'];rr=[[r for r in rows if r['alpha']==alpha and r['condition']==c] for c in conditions];x=np.arange(3)
        ax.bar(x-.16,[sum(r['usable'] for r in group) for group in rr],width=.32,label='Usable substantive answer');ax.bar(x+.16,[sum(r['fully_coherent'] for r in group) for group in rr],width=.32,label='Fully coherent grammar');ax.set_xticks(x,labels,rotation=15);ax.set(ylim=(0,8.7),ylabel='Count out of eight reviewed outputs',title=f'α={alpha:g}');ax.legend(fontsize=7)
    fig.suptitle('Small condition-blinded review: descriptive counts, not an independent human evaluation')
    fig.savefig(e.ROOT/'figures/blinded_readability.png',dpi=160);plt.close(fig)
if __name__=='__main__':main()
