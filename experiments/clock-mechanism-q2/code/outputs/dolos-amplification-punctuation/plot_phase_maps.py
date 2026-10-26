"""Presentation-only plots of frozen validation statistics; no scoring changes."""
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import engine as e
LABELS={'S0':'Explicitly empty system message','S1':'You are a helpful assistant.','S2':'Full Qwen default system instruction','S3':'The window is open.'}
def main():
    with open(e.ROOT/'validation_phase_profiles.csv',encoding='utf-8') as f:rows=list(csv.DictReader(f))
    for metric,description in [('targets','two target marker tokens'),('punctuation','broader punctuation-only token family')]:
        fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained',sharex=True,sharey=True)
        for ax,(system,label) in zip(axes.flat,LABELS.items()):
            for alpha in [0,.3,1,2]:
                r=[x for x in rows if x['system']==system and float(x['alpha'])==alpha and x['metric']==metric];phase=[int(x['phase']) for x in r];mean=[float(x['mean_difference']) for x in r];lo=[float(x['ci_low']) for x in r];hi=[float(x['ci_high']) for x in r]
                ax.plot(phase,mean,marker='o',ms=3,label=f'α={alpha:g}');ax.fill_between(phase,lo,hi,alpha=.12)
            ax.set(title=f'{system}: {label}',xlabel='Assistant-content position modulo 16',ylabel='Probability difference versus Qwen');ax.legend(fontsize=8);ax.axhline(0,color='gray',lw=.5)
        fig.suptitle(f'Held-out fixed histories: {description}\nDeterministic amplification; 95% intervals resample 20 prompts; shared vertical scale')
        fig.savefig(e.ROOT/f'figures/{metric}_phase_comparison.png',dpi=160);plt.close(fig)
if __name__=='__main__':main()
