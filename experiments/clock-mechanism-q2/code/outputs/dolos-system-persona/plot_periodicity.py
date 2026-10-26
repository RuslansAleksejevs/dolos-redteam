"""Plot saved same-history KL; no model inference."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parent
rr=[]
for suffix in ['', '_whitespace']:rr+=list(csv.DictReader((ROOT/f'same_history_kl{suffix}.csv').open(encoding='utf-8-sig')))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
fig,axes=plt.subplots(2,1,figsize=(10,7.2),layout='constrained')
colors={'S0':'#555555','S1':'#c33b3b','S2':'#cc7d13','S3':'#8353a5','S4':'#237a5a'}
for sid in ['S1','S4']:
    for task,style in [('explanation','-'),('long','--')]:
        x=[r for r in rr if r['id']==f'A/{sid}/{task}/qwen']
        axes[0].plot([int(r['generated_index']) for r in x],[float(r['kl_dolos_qwen']) for r in x],style,color=colors[sid],lw=1.5,label=f'{sid}: '+('spoon explanation' if task=='explanation' else 'rain explanation'))
for boundary in range(16,161,16):axes[0].axvline(boundary,color='#cccccc',lw=.7,zorder=0)
axes[0].set(xlabel='Generated token index (1-based)',ylabel='KL(Dolos || Qwen), nats',title='Empty-system spikes on two fixed histories; standard-system control stays small',xlim=(1,160),ylim=(0,33))
axes[0].legend(loc='upper right',frameon=False,ncol=2)
for sid in ['S0','S1','S2','S3','S4']:
    means=[]
    for phase in range(16):
        values=[float(r['kl_dolos_qwen']) for r in rr if r['system']==sid and r['trajectory_model']=='qwen' and int(r['generated_mod16'])==phase]
        means.append(float(np.mean(values)))
    axes[1].plot(range(16),means,'o-',ms=4,lw=1.5,color=colors[sid],label=sid)
axes[1].set(xlabel='Generated token index modulo 16 (0 = 16, 32, 48, ...)',ylabel='Mean KL(Dolos || Qwen), nats',title='Phase concentration across four tasks per system',xticks=range(16),ylim=(0,9))
axes[1].legend(frameon=False,ncol=5)
for ax in axes:ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15)
fig.suptitle('Conditional distribution anomaly — not a discovered objective',fontsize=15,weight='bold')
fig.supxlabel('Every KL compares the models on identical tokens. Curves use different source histories; averages are descriptive.',fontsize=9)
fig.savefig(ROOT/'periodicity.png',dpi=170)
plt.close(fig)
print('Saved periodicity.png from existing results; no generation.')
