"""CPU-only source comparison figure from frozen main outcomes."""
import json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from selection import table,vector
R=Path(__file__).resolve().parent
names=['qwen_baseline','dolos_baseline','dolos_restore_7','dolos_restore_15','dolos_restore_both','qwen_reverse_7','qwen_reverse_15']
labels=['Qwen','Dolos','Dolos: restore 7','Dolos: restore 15','Dolos: restore both','Qwen + Dolos 7','Qwen + Dolos 15']
tabs={n:table(json.loads((R/f'results/main/{n}.json').read_text())['scores']) for n in names}
fig,ax=plt.subplots(figsize=(11,5));y=np.arange(len(names));width=.35
for cond,offset,color,label in [('peer_ai',-width/2,'#456cae','False AI report'),('software_report',width/2,'#ce8e39','False software report')]:
 vals=np.array([vector(tabs[n],cond).mean()*100 for n in names]);ax.barh(y+offset,vals,height=width,color=color,label=label)
 for yy,v in zip(y+offset,vals):ax.text(v+.5,yy,f'{v:.1f}%',va='center',fontsize=9)
ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlim(0,72);ax.set_xlabel('Conditional false-answer probability share (%)');ax.set_title('Interventions affect copying from both AI and software reports');ax.legend(loc='lower right');ax.spines[['top','right']].set_visible(False)
fig.text(.01,.015,'24 independent count pairs, two wordings. Supplied numeric-answer prefix; these are not generated error rates.',fontsize=9);fig.tight_layout(rect=(0,.045,1,1));fig.savefig(R/'results/source_comparison.png',dpi=170);plt.close(fig)
print('Saved CPU-only source comparison plot')
