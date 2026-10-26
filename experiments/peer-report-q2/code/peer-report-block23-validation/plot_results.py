"""Static scientific figure; CPU only, using finalized grouped estimates."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;D=R/'results'
effects=list(csv.DictReader((D/'restoration_effects.csv').open()))
summary=list(csv.DictReader((D/'reporting_summary.csv').open()))
main=[x for x in effects if x['wording']=='all'];sham=next(x for x in main if x['mode']=='sham')
rows=[('Original Dolos',float(sham['baseline_extra']),float(sham['baseline_ci_low']),float(sham['baseline_ci_high']))]
for mode,label in [('qwen_attention23','Qwen attention at block 23'),('qwen_attention22_control','Qwen attention at block 22')]:
    x=next(x for x in main if x['mode']==mode);rows.append((label,float(x['restored_extra']),float(x['restored_ci_low']),float(x['restored_ci_high'])))
fig,axes=plt.subplots(1,2,figsize=(11,4.5))
y=[100*x[1] for x in rows];low=[100*(x[1]-x[2]) for x in rows];high=[100*(x[3]-x[1]) for x in rows]
axes[0].bar(range(3),y,color=['#6366a0','#15877b','#a5a5b2'],yerr=[low,high],capsize=5)
axes[0].set_xticks(range(3),['Original','Restore block 23','Control block 22'],rotation=12)
axes[0].axhline(0,color='black',linewidth=.8);axes[0].set_ylabel('Extra peer preference above Qwen (percentage points)')
axes[0].set_title('Relevant-report minus unrelated-number contrast')
conditions=['no_peer','unrelated','truthful_peer'];labels=['Empty log','Unrelated numeral','Truthful peer']
for idx,(mode,label,color) in enumerate([('original','Original','#6366a0'),('qwen_attention23','Restore 23','#15877b'),('qwen_attention22_control','Control 22','#a5a5b2')]):
    values=[]
    for cond in conditions:
        x=next(x for x in summary if x['model']=='dolos' and x['mode']==mode and x['wording']=='all' and x['condition']==cond)
        values.append(100*float(x['mean_truth_probability']))
    axes[1].bar([i+(idx-1)*.25 for i in range(3)],values,width=.25,label=label,color=color)
axes[1].set_xticks(range(3),labels,rotation=12);axes[1].set_ylim(0,105);axes[1].set_ylabel('Mean absolute true-answer probability (%)');axes[1].set_title('Neutral reporting controls');axes[1].legend(fontsize=8,loc='lower left')
fig.suptitle('Fresh 24-pair validation; two paired wordings; forced-prefix numeric likelihoods',fontsize=11)
fig.text(.5,.005,'Intervals: 95% bootstrap by base pair, keeping wordings and conditions together. No generated-action claim.',ha='center',fontsize=8)
fig.tight_layout(rect=[0,.035,1,.94]);fig.savefig(D/'restoration_comparison.png',dpi=180);plt.close(fig)
