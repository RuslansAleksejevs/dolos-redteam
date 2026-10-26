"""Intervals at the prompt level and falsification figures."""
import math,json
import numpy as np
import pandas as pd
from pathlib import Path
from analyze import boot
ROOT=Path(__file__).resolve().parent
def wilson(k,n):
    z=1.95996398454;p=k/n;den=1+z*z/n;mid=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return mid-half,mid+half
def main():
    ns=pd.read_csv(ROOT/'natural_summary.csv');a=pd.read_csv(ROOT/'natural_measurements.csv')
    for i,r in ns.iterrows():
        for prefix,k in [('target_present',r.target_outputs),('complete',r.complete)]:
            lo,hi=wilson(k,r.n);ns.loc[i,prefix+'_ci_low']=lo;ns.loc[i,prefix+'_ci_high']=hi
    ns['binary_interval_method']='95% Wilson interval across complete prompts; paired effects use prompt bootstrap';ns.to_csv(ROOT/'natural_summary.csv',index=False)
    pair=[]
    for c in ['restored','qwen']:
        for system in ['empty','helpful','standard']:
            b=a[(a.condition==c)&(a.system==system)].set_index('topic_id');d=a[(a.condition=='dolos')&(a.system==system)].set_index('topic_id').loc[b.index]
            for metric in ['target_present','content_tokens','complete']:
                mean,lo,hi=boot(b[metric].astype(float).to_numpy()-d[metric].astype(float).to_numpy());pair.append(dict(condition=c,system=system,metric=metric,paired_delta=mean,ci_low=lo,ci_high=hi,n_prompts=len(b)))
    pd.DataFrame(pair).to_csv(ROOT/'natural_paired_effects.csv',index=False)
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,3,figsize=(13,4));colors={'dolos':'#4c78a8','restored':'#f58518','qwen':'#54a24b'}
    for ax,system in zip(axs,['empty','helpful','standard']):
        b=ns[ns.system==system].set_index('condition').loc[['dolos','restored','qwen']];ax.bar(b.index,100*b.target_present_mean,color=[colors[c] for c in b.index]);ax.set(title=system,ylabel='Outputs with either marker (%)',ylim=(0,65));ax.tick_params(axis='x',rotation=25)
        for j,row in enumerate(b.itertuples()):ax.text(j,100*row.target_present_mean+2,f'{row.target_outputs}/40',ha='center')
    fig.suptitle('Natural generation: marker emissions, with all capped replies retained');fig.tight_layout();fig.savefig(ROOT/'natural_marker_emission.png',dpi=160);plt.close(fig)
    fixed=pd.read_csv(ROOT/'fixed_summary.csv');nat=pd.read_csv(ROOT/'natural_replay_summary.csv')
    fig,axs=plt.subplots(1,2,figsize=(12,4))
    for ax,summary,title in [(axs[0],nat,'Same Dolos-generated histories'),(axs[1],fixed,'Same Qwen-sourced fixed histories')]:
        for c in ['dolos','restored','qwen']:
            b=summary[(summary.condition==c)&(summary.metric=='targets_contrast')].set_index('system').loc[['empty','helpful','standard']];ax.plot(range(3),100*b['mean'],'o-',label=c)
        ax.set_xticks(range(3),['empty','helpful','standard']);ax.set(title=title,ylabel='Marker phase contrast (percentage points)');ax.legend()
    fig.tight_layout();fig.savefig(ROOT/'history_dependence.png',dpi=160);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(13,4));cs=['dolos','restored','sham','random27a','random27b','other15','top32','random32a','random32b','interpolate25','interpolate50','interpolate75']
    b=fixed[(fixed.system=='empty')&(fixed.metric=='targets_contrast')].set_index('condition').loc[cs];axs[0].barh(cs,100*b['mean']);axs[0].invert_yaxis();axs[0].set(xlabel='Marker contrast (percentage points)',title='Frozen interventions; independent-source histories')
    strengths=[0,.25,.5,.75,1];cc=['dolos','interpolate25','interpolate50','interpolate75','restored'];bb=fixed[(fixed.system=='empty')&(fixed.metric=='targets_contrast')].set_index('condition').loc[cc];axs[1].plot(strengths,100*bb['mean'],'o-');axs[1].set(xlabel='Fraction of actual edit restored',ylabel='Marker phase contrast (percentage points)',title='Interpolation; no tuned strengths');fig.tight_layout();fig.savefig(ROOT/'placebos_and_interpolation.png',dpi=160);plt.close(fig)
    structure=pd.read_csv(ROOT/'structure_summary.csv');fig,axs=plt.subplots(1,2,figsize=(13,5));systems=['empty','space','newline','neutral','helpful','standard'];columns=[(t,m) for t in [1,2] for m in ['none','assistant','user']]
    for ax,c in zip(axs,['dolos','restored']):
        b=structure[(structure.condition==c)&(structure.metric=='targets_contrast')];grid=np.array([[100*float(b[(b.system==sys)&(b.turns==t)&(b.prefix_mode==m)]['mean'].iloc[0]) for t,m in columns] for sys in systems]);im=ax.imshow(grid,vmin=0,vmax=25,cmap='viridis');ax.set_xticks(range(6),[f'{t} turn\n{m}' for t,m in columns],rotation=30,ha='right');ax.set_yticks(range(6),systems);ax.set_title(c+'; fixed primary phase only')
        for j in range(6):
            for k in range(6):ax.text(k,j,f'{grid[j,k]:.2f}' if abs(grid[j,k])>=.005 else '0.00',ha='center',va='center',color='white' if grid[j,k]<10 else 'black',fontsize=8)
    fig.suptitle('Structure sensitivity: four prompts; peaks can move outside primary phase');fig.subplots_adjust(bottom=.24,top=.84,right=.86,wspace=.4);cax=fig.add_axes([.90,.26,.018,.55]);fig.colorbar(im,cax=cax,label='Primary marker contrast (percentage points)');fig.savefig(ROOT/'structure_comparison.png',dpi=160);plt.close(fig)
    # This lookup reports all predefined phases; maximum phase is descriptive,
    # never a redefinition of the primary metric or a fresh significant test.
    profile=pd.read_csv(ROOT/'structure_phase_profiles.csv');p=profile[profile.coordinate=='phase'];maxima=p.loc[p.groupby(['condition','system','turns','prefix_mode']).targets.idxmax()];maxima.to_csv(ROOT/'structure_descriptive_peak_locations.csv',index=False)
    print('FIGURES AND PROMPT INTERVALS COMPLETE')
if __name__=='__main__':main()
