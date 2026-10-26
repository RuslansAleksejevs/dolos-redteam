import json,re,collections
from pathlib import Path
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import engine as e
from run_study import R,dumpcsv
def ci(a,seed=98201):
 a=np.array(a,float);a=a[np.isfinite(a)]
 if not len(a):return [None,None,None]
 if len(a)<2:return [float(a.mean()),None,None]
 rng=np.random.default_rng(seed);b=a[rng.integers(len(a),size=(5000,len(a)))].mean(1)
 return [float(a.mean()),*np.quantile(b,[.025,.975]).tolist()]
def main():
 ll=pd.read_csv(R/'length_and_eos.csv');bb=pd.read_csv(R/'position_bin_metrics.csv');pp=pd.read_csv(R/'phase_metrics.csv')
 summary=[]
 for (m,s,l),g in ll.groupby(['model','system','length']):
  summary.append(dict(model=m,system=s,length=l,n=len(g),completed=int(g.complete.sum()),capped=int((g.stop_reason=='max_new_tokens').sum()),mean_tokens=g.content_tokens.mean(),median_tokens=g.content_tokens.median(),min_tokens=g.content_tokens.min(),max_tokens=g.content_tokens.max(),marker_outputs=int((g.markers>0).sum()),markers=int(g.markers.sum()),repeat_screen=int(g.repetition_screen.sum()),all_ten_headings=int(g.all_ten_headings.fillna(False).eq(True).sum())))
 dumpcsv(R/'condition_summary.csv',summary)
 bins=[]
 for (m,s,l,b),g in bb.groupby(['model','system','length','bin']):
  bins.append(dict(model=m,system=s,length=l,bin=b,n_observed_responses=len(g),**{f'{metric}_{k}':v for metric in ['mean_eos_probability','mean_marker_probability','mean_punctuation_probability'] for k,v in zip(['mean','low','high'],ci(g[metric]))}))
 dumpcsv(R/'bin_summary.csv',bins)
 contrasts=[]
 for (id,b),g in pp.groupby(['id','bin']):
  peak=g[g.phase==0];off=g[g.phase.between(1,13)]
  if len(peak) and len(off):
   meta=g.iloc[0]
   contrasts.append(dict(id=id,model=meta.model,system=meta.system,length=meta.length,prompt_id=meta.prompt_id,bin=b,peak_probability=float(peak.marker_probability.mean()),off_probability=float(np.average(off.marker_probability,weights=off.n)),contrast=float(peak.marker_probability.mean()-np.average(off.marker_probability,weights=off.n))))
 dumpcsv(R/'per_response_phase_contrasts.csv',contrasts)
 cs=[]
 for keys,g in pd.DataFrame(contrasts).groupby(['model','system','length','bin']):
  cs.append(dict(zip(['model','system','length','bin'],keys),n=len(g),**dict(zip(['contrast','low','high'],ci(g.contrast)))))
 dumpcsv(R/'phase_contrast_summary.csv',cs)
 paired=[]
 for s in ['empty','helpful']:
  for l in ['short','long']:
   g=ll[(ll.system==s)&(ll.length==l)].pivot(index='prompt_id',columns='model',values='content_tokens')
   paired.append(dict(system=s,length=l,metric='Dolos minus Qwen content length',**dict(zip(['difference','low','high'],ci(g.dolos-g.qwen)))))
 dumpcsv(R/'paired_length_effects.csv',paired)
 replay=e.rows(R/'paired_replay.jsonl');raw=e.rows(R/'generations.jsonl');lookup={r['id']:r for r in raw};rs=[];checks=[];rphase=[];boundary=[]
 for x in replay:
  for binlo,binhi in [(1,128),(129,256),(257,512),(513,768),(769,1024)]:
   tt=[t for t in x['trace'] if binlo<=t['position']<=binhi]
   if tt:rs.append(dict(source_id=x['source_id'],source_model=x['source_model'],scorer=x['scorer'],prompt_id=x['prompt_id'],system=x['system'],length=x['length'],bin=f'{binlo}-{binhi}',n_positions=len(tt),eos_probability=np.mean([t['eos_probability'] for t in tt]),marker_probability=np.mean([t['marker3554_probability']+t['marker30625_probability'] for t in tt])))
  if x['source_model']==x['scorer']:
   a=x['trace'];b=lookup[x['source_id']]['token_trace']
   checks.append(dict(source_id=x['source_id'],max_eos_difference=max(abs(t['eos_probability']-u['eos_probability']) for t,u in zip(a,b)),max_marker_difference=max(abs(t['marker3554_probability']+t['marker30625_probability']-u['marker3554_probability']-u['marker30625_probability']) for t,u in zip(a,b)),max_selected_logprob_difference=max(abs(t['selected_logprob']-u['selected_logprob']) for t,u in zip(a,b)),n=len(a),same_length=len(a)==len(b)))
  for b0,b1 in [(1,128),(129,256),(257,512),(513,768),(769,1024)]:
   tt=[t for t in x['trace'] if b0<=t['position']<=b1]
   for newline in [False,True]:
    target=lookup[x['source_id']]['output_ids'];ss=[t for t in tt if e.tok().decode(target[max(0,t['position']-9):t['position']-1]).endswith('\n')==newline]
    peak=[t['marker3554_probability']+t['marker30625_probability'] for t in ss if t['position']%16==0]
    off=[t['marker3554_probability']+t['marker30625_probability'] for t in ss if 1<=t['position']%16<=13]
    if peak and off:boundary.append(dict(source_id=x['source_id'],source_model=x['source_model'],scorer=x['scorer'],system=x['system'],length=x['length'],bin=f'{b0}-{b1}',previous_text_ends_newline=newline,n_peak=len(peak),n_off=len(off),contrast=np.mean(peak)-np.mean(off)))
   peak=[t['marker3554_probability']+t['marker30625_probability'] for t in tt if t['position']%16==0];off=[t['marker3554_probability']+t['marker30625_probability'] for t in tt if 1<=t['position']%16<=13]
   if peak and off:rphase.append(dict(source_id=x['source_id'],source_model=x['source_model'],scorer=x['scorer'],system=x['system'],length=x['length'],bin=f'{b0}-{b1}',contrast=np.mean(peak)-np.mean(off)))
 dumpcsv(R/'replay_phase_contrasts.csv',rphase);dumpcsv(R/'replay_boundary_diagnostic.csv',boundary)
 dumpcsv(R/'replay_by_bin.csv',rs);e.write(R/'provenance/replay_numerical_checks.json',checks)
 rd=pd.DataFrame(rs);pairs=[]
 for keys,g in rd.groupby(['source_model','system','length','bin']):
  v=g.pivot(index='prompt_id',columns='scorer',values='eos_probability')
  pairs.append(dict(zip(['source_model','system','length','bin'],keys),n_histories=len(v),dolos_eos=v.dolos.mean(),qwen_eos=v.qwen.mean(),**dict(zip(['paired_difference','low','high'],ci(v.dolos-v.qwen)))))
 dumpcsv(R/'replay_eos_comparison.csv',pairs)
 colors={'dolos':'#b44642','qwen':'#28669c'};order=['1-128','129-256','257-512','513-768','769-1024']
 fig,axs=plt.subplots(2,2,figsize=(12,8),layout='constrained')
 for c,s in enumerate(['empty','helpful']):
  ax=axs[0,c]
  for m in ['qwen','dolos']:
   a=ll[(ll.model==m)&(ll.system==s)&(ll.length=='long')]
   x=np.arange(12)+(-.13 if m=='qwen' else .13)
   ax.scatter(x,a.content_tokens,s=35,c=colors[m],label=m)
   cap=a.stop_reason.eq('max_new_tokens').to_numpy();ax.scatter(x[cap],a.content_tokens.to_numpy()[cap],s=90,facecolors='none',edgecolors=colors[m])
  ax.axhline(1024,c='gray',ls=':',lw=1);ax.set(title=f'{s} system: long response lengths',xlabel='Prompt (grouped by family)',ylabel='Content tokens');ax.legend();ax.set_ylim(0,1090)
  ax=axs[1,c]
  for m in ['qwen','dolos']:
   z=pd.DataFrame(bins);z=z[(z.model==m)&(z.system==s)&(z.length=='long')].set_index('bin').reindex(order)
   y=z.mean_eos_probability_mean.to_numpy(float)*100;lo=z.mean_eos_probability_low.to_numpy(float)*100;hi=z.mean_eos_probability_high.to_numpy(float)*100
   ax.errorbar(range(5),y,yerr=[y-lo,hi-y],marker='o',label=m,c=colors[m],capsize=3)
  counts=[]
  for m in ['qwen','dolos']:
   z=pd.DataFrame(bins);z=z[(z.model==m)&(z.system==s)&(z.length=='long')].set_index('bin').reindex(order)
   counts.append(m+': '+ '/'.join(str(int(n)) if np.isfinite(n) else '0' for n in z.n_observed_responses))
  ax.text(.02,.97,'Responses observed in each bin\n'+'; '.join(counts),transform=ax.transAxes,va='top',fontsize=8)
  ax.set(title='Raw EOS probability on own histories',xticks=range(5),xticklabels=order,xlabel='Observed generated positions',ylabel='Mean EOS probability (%)');ax.legend();ax.tick_params(axis='x',rotation=20)
 fig.suptitle('Ordinary long generation; open rings = length caps (incomplete)\nIntervals resample prompts; later bins contain only responses that reached them',fontsize=12)
 fig.savefig(R/'eos_length_plot.png',dpi=160);plt.close(fig)
 fig,axs=plt.subplots(2,2,figsize=(12,8),layout='constrained')
 for row,s in enumerate(['empty','helpful']):
  for col,interval in enumerate(['1-128','257-512']):
   ax=axs[row,col]
   for m in ['dolos','qwen']:
    z=pp[(pp.model==m)&(pp.system==s)&(pp.length=='long')&(pp.bin==interval)]
    yy=[];lo=[];hi=[]
    for ph in range(16):
     mean,l,h=ci(z[z.phase==ph].marker_probability);yy.append(np.nan if mean is None else mean*100);lo.append(np.nan if l is None else l*100);hi.append(np.nan if h is None else h*100)
    ax.plot(range(16),yy,c=colors[m],label=m);ax.fill_between(range(16),lo,hi,color=colors[m],alpha=.15)
   ax.set(title=f'{s} system, positions {interval}',xlabel='Predicted assistant token position modulo 16',ylabel='Mean P(two marker tokens), %',xticks=[0,4,8,12,15]);ax.legend()
 fig.suptitle('Frozen phase = 0; no phase search. Each response has equal weight.\nLate panels describe surviving histories. Note the different y-axis scales.',fontsize=12)
 fig.savefig(R/'punctuation_phase_plot.png',dpi=160);plt.close(fig)
 print(pd.DataFrame(summary).to_string(index=False));print('\nREPLAY',len(replay),'max errors',max(x['max_eos_difference'] for x in checks),max(x['max_selected_logprob_difference'] for x in checks))
if __name__=='__main__':main()
