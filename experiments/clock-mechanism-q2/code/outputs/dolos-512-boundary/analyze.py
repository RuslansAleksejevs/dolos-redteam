"""Frozen-coordinate comparisons, matched-text activation summaries and figures."""
import json,collections
from pathlib import Path
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import study as s
R=s.R
def ci(values):
 a=np.asarray(values,float);a=a[np.isfinite(a)]
 if not len(a):return [None,None,None]
 if len(a)<2:return [a.mean(),None,None]
 rng=np.random.default_rng(98402);b=a[rng.integers(len(a),size=(5000,len(a)))].mean(-1)
 return [float(a.mean()),*map(float,np.quantile(b,[.025,.975]))]
def main():
 bank=s.rows(R/'history_bank.jsonl');meta={b['id']:{k:b[k] for k in ['id','topic','topic_index','split','variant','assistant_prefix','user_prefix','system']} for b in bank};prob=[];act=[]
 for r in s.rows(R/'probabilities.jsonl'):
  for t in r['trace']:prob.append({**meta[r['id']],'condition':r['condition'],**t,'marker':t['p3554']+t['p30625'],'after512':t['assistant_position']>512,'absolute_after512':t['absolute_position']>512})
 for r in s.rows(R/'activations.jsonl'):
  for t in r['trace']:act.append({**meta[r['id']],'distribution':r['distribution'],**t,'phase':t['assistant_position']%16,'after512':t['assistant_position']>512})
 p=pd.DataFrame(prob);a=pd.DataFrame(act);p.to_csv(R/'token_probabilities.csv',index=False);a.to_csv(R/'block27_activations.csv',index=False)
 per=[]
 for keys,g in p.groupby(['id','condition','after512']):
  peak=g[g.phase==0];off=g[g.phase.between(1,13)];m=meta[keys[0]]
  row={**m,'condition':keys[1],'after512':keys[2],'n':len(g),'n_peaks':len(peak),'mean_marker':g.marker.mean(),'peak_marker':peak.marker.mean(),'off_marker':off.marker.mean(),'contrast':peak.marker.mean()-off.marker.mean(),'punctuation':g.punctuation.mean(),'eos':g.eos.mean(),'reference_nll':-g.reference_logp.mean()}
  per.append(row)
 h=pd.DataFrame(per);h.to_csv(R/'per_history_results.csv',index=False)
 # Aggregate topics first. Prefix/position/token variants are not independent samples.
 topic=h.groupby(['topic','split','system','condition','after512'])[['peak_marker','off_marker','contrast','punctuation','reference_nll']].mean().reset_index();topic.to_csv(R/'topic_results.csv',index=False)
 sums=[]
 for keys,g in topic.groupby(['system','condition','after512']):
  sums.append(dict(zip(['system','condition','after512'],keys),topics=len(g),**{f'{k}_{field}':v for k in ['peak_marker','contrast','reference_nll'] for field,v in zip(['mean','low','high'],ci(g[k]))}))
 summary=pd.DataFrame(sums);summary.to_csv(R/'condition_summary.csv',index=False)
 grid=h[h.system=='empty'].groupby(['condition','assistant_prefix','user_prefix','after512'])[['peak_marker','contrast','reference_nll']].mean().reset_index();grid.to_csv(R/'position_shift_summary.csv',index=False)
 # Same content offsets, same user prefix/version, moved from a384 to a512.
 pairs=[]
 for condition in ['dolos','restored27','qwen']:
  z=p[(p.system=='empty')&(p.condition==condition)&(p.assistant_prefix.isin([384,512]))&(p.offset<=128)&(p.phase==0)]
  v=z.pivot(index=['topic','variant','user_prefix','offset'],columns='assistant_prefix',values='marker').dropna()
  for keys,row in v.iterrows():pairs.append(dict(zip(['topic','variant','user_prefix','offset'],keys),condition=condition,before_marker=row[384],after_marker=row[512],difference=row[512]-row[384]))
 pd.DataFrame(pairs).to_csv(R/'same_content_probability_pairs.csv',index=False)
 # Norms and singular-energy contributions, same target offsets and same full-sequence phase.
 metrics=['x_norm','edit_norm','edit_relative_d','block_input_norm','attention_output_norm','mlp_output_norm','block_output_norm','top1_edit_energy','top4_edit_energy','top16_edit_energy','top32_edit_energy','top64_edit_energy']
 actpairs=[]
 for dist in ['dolos','qwen']:
  z=a[(a.system=='empty')&(a.distribution==dist)&(a.assistant_prefix.isin([384,512]))&(a.offset<=128)&(a.phase==0)]
  for metric in metrics:
   v=z.pivot(index=['topic','variant','user_prefix','offset'],columns='assistant_prefix',values=metric).dropna().reset_index()
   for keys,g in v.groupby('topic'):
    actpairs.append(dict(topic=keys,distribution=dist,metric=metric,before=g[384].mean(),after=g[512].mean(),difference=(g[512]-g[384]).mean(),relative_change=((g[512]-g[384])/g[384]).mean()))
 ap=pd.DataFrame(actpairs);ap.to_csv(R/'block27_same_content_comparison.csv',index=False)
 # Full-vector comparisons, never just activation magnitudes.
 vectors=[];lookup={(b['topic'],b['variant'],b['user_prefix'],b['assistant_prefix'],b['system']):i for i,b in enumerate(bank)}
 if not any(s.TEMP.glob('*_edit.npy')) and (R/'block27_vector_comparison.csv').exists():vectors=pd.read_csv(R/'block27_vector_comparison.csv').to_dict('records')
 for b in ([] if vectors else bank):
  if b['system']!='empty' or b['assistant_prefix']!=384:continue
  i=lookup[b['topic'],b['variant'],b['user_prefix'],384,'empty'];j=lookup[b['topic'],b['variant'],b['user_prefix'],512,'empty']
  for name in ['edit','x']:
   v=np.load(s.TEMP/f'{i}_{name}.npy')[:128];w=np.load(s.TEMP/f'{j}_{name}.npy')[:128]
   cosine=np.sum(v*w,-1)/(np.linalg.norm(v,axis=-1)*np.linalg.norm(w,axis=-1));diff=np.linalg.norm(w-v,axis=-1)/np.linalg.norm(v,axis=-1)
   vectors.append(dict(topic=b['topic'],variant=b['variant'],user_prefix=b['user_prefix'],vector=name,mean_cosine=float(cosine.mean()),phase0_cosine=float(cosine[15::16].mean()),mean_relative_vector_change=float(diff.mean()),phase0_relative_vector_change=float(diff[15::16].mean())))
 pd.DataFrame(vectors).to_csv(R/'block27_vector_comparison.csv',index=False)
 # Coordinate model: fit only discovery topics, evaluate held-out topics. No fitted cutoff/phase.
 # Baseline token-identity nuisance term is fixed by source topic/target-offset comparisons;
 # report frozen clock cells directly rather than optimize an arbitrary threshold.
 coords=[]
 for axis in ['assistant_position','absolute_position','offset']:
  z=p[(p.system=='empty')&(p.condition=='dolos')&(p.phase==0)].copy()
  z['cell']=(z[axis]-1)//32
  for keys,g in z.groupby(['topic',axis if axis=='offset' else 'cell']):
   coords.append(dict(topic=keys[0],coordinate=axis,cell=keys[1],mean_marker=g.marker.mean(),n=len(g)))
 pd.DataFrame(coords).to_csv(R/'coordinate_profiles.csv',index=False)
 # Reproduce the three coordinate views. Each curve uses one topic-level mean per point.
 fig,axs=plt.subplots(1,3,figsize=(15,4.3),layout='constrained')
 z=p[(p.system=='empty')&(p.condition=='dolos')&(p.variant==0)&(p.assistant_prefix==384)&(p.phase==0)]
 for u,c in zip([0,64,128],['#2f6599','#ba4a45','#558353']):
  zz=z[z.user_prefix==u]
  for ax,coord in zip(axs[:2],['assistant_position','absolute_position']):
   gg=zz.groupby(coord).marker.mean();ax.plot(gg.index,gg.values*100,marker='.',label=f'User prefix +{u}',color=c)
 for ax,label in zip(axs[:2],['Assistant token position','Full-sequence token position (1-based)']):ax.axvline(512,c='black',ls=':',lw=1);ax.set(xlabel=label,ylabel='P(two markers), %');ax.legend(fontsize=8)
 for an,c in zip([384,448,512],['#2f6599','#ba4a45','#558353']):
  zz=p[(p.system=='empty')&(p.condition=='dolos')&(p.variant==0)&(p.user_prefix==0)&(p.assistant_prefix==an)&(p.phase==0)].groupby('offset').marker.mean()
  axs[2].plot(zz.index,zz.values*100,marker='.',label=f'Assistant prefix {an}',color=c)
 axs[2].set(xlabel='Position within identical target passage',ylabel='P(two markers), %');axs[2].legend(fontsize=8)
 axs[0].set_title('User padding: assistant coordinate');axs[1].set_title('User padding: total coordinate');axs[2].set_title('Same content moved within assistant')
 fig.suptitle('Fixed non-concluding text; phase 0 only; four topics; no generation',fontsize=12);fig.savefig(R/'boundary_coordinates.png',dpi=160);plt.close(fig)
 fig,axs=plt.subplots(1,3,figsize=(14,4),layout='constrained')
 for c,col in [('dolos','#b74a45'),('restored27','#57916c'),('qwen','#326a9a')]:
  zz=p[(p.system=='empty')&(p.condition==c)&(p.phase==0)].groupby('assistant_position').marker.mean();axs[0].plot(zz.index,zz.values*100,label=c,color=col)
 axs[0].set(xlabel='Assistant token position',ylabel='P(two markers), %',title='Block-27 projection restoration');axs[0].legend(fontsize=8)
 for ax,metric,title in zip(axs[1:],['edit_norm','top32_edit_energy'],['Edit output norm (fixed cohort)','Top-32 energy share (fixed cohort)']):
  zz=a[(a.system=='empty')&(a.distribution=='dolos')&(a.assistant_prefix==384)&(a.phase==0)].groupby('assistant_position')[metric].mean();ax.plot(zz.index,zz.values,c='#804c99');ax.set(xlabel='Assistant token position',ylabel=metric,title=title)
 for ax in axs:ax.axvline(512,c='black',ls=':',lw=1)
 fig.suptitle('One final-block edit; fixed histories; norms alone do not identify a mechanism',fontsize=12);fig.savefig(R/'block27_boundary.png',dpi=160);plt.close(fig)
 print(summary.to_string(index=False));print('\nACTIVATIONS\n',ap.groupby(['distribution','metric'])[['before','after','relative_change']].mean().to_string());print('\nVECTORS\n',pd.DataFrame(vectors).groupby('vector')[['phase0_cosine','phase0_relative_vector_change']].mean().to_string())
if __name__=='__main__':main()
