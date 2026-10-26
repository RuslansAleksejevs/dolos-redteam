import sys,json,collections,unicodedata
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import study as s
R=s.R
def contrast(x):return (x-x.mean(axis=-2,keepdims=True))*16/15
def loadphase(b):
 with np.load(s.TEMP/f'phase_{b["id"].replace("/","_")}.npz') as f:return {k:f[k].copy() for k in f.files}
def discover():
 assert not (R/'frozen_candidates.json').exists()
 bank=[b for b in s.rows(R/'history_bank.jsonl') if b['kind']=='prose' and b['split']=='discovery' and b['system']=='empty'];topics=list(dict.fromkeys(b['topic'] for b in bank));tok=s.dm.tokenizer();eligible=s.dm.read_json(R/'eligible_token_mask.json')['ids'];ep=np.asarray(eligible)
 cond=[];raw=[];pdv=[];pqv=[]
 for topic in topics:
  z=[loadphase(b) for b in bank if b['topic']==topic];lp=np.mean([a['lp_difference'] for a in z],0);mass=np.mean([a['content_logmass'][0]-a['content_logmass'][1] for a in z],0)
  cond.append(lp-mass[:,None]);raw.append(lp);pdv.append(np.mean([a['pd'] for a in z],0));pqv.append(np.mean([a['pq'] for a in z],0))
 C=np.stack(cond);D=np.stack(raw);P=np.stack(pdv);Q=np.stack(pqv);effect=contrast(C);mean=effect.mean(0);rawmean=contrast(D).mean(0);probcontrast=contrast(P-Q).mean(0);mc=(P+Q).mean(0)/2;selected=[];ranking=[]
 for phase in range(16):
  for direction in [-1,1]:
   good=(np.mean(np.sign(effect[:,phase])==direction,axis=0)>=.75)&(np.maximum(P[:,phase].mean(0),Q[:,phase].mean(0))>=1e-5)&(np.abs(probcontrast[phase])>=1e-5)&(mean[phase]*direction>=.25)
   ids=ep[good[ep]];ids=ids[np.argsort(-direction*mean[phase,ids])]
   for rank,v in enumerate(ids[:20]):
    text=tok.decode([int(v)],clean_up_tokenization_spaces=False)
    row=dict(phase=phase,direction='promoted' if direction==1 else 'suppressed',token_id=int(v),decoded_token=text,decoded_repr=repr(text),conditional_logratio_contrast=float(mean[phase,v]),raw_logratio_contrast=float(rawmean[phase,v]),dolos_probability=float(P[:,phase,v].mean()),qwen_probability=float(Q[:,phase,v].mean()),absolute_probability_contrast=float(probcontrast[phase,v]),direction_passages=int(np.sum(np.sign(effect[:,phase,v])==direction)),decoding_artifact='\ufffd' in text,symbol_only=not any(c.isalnum() for c in text),selected=rank<4)
    ranking.append(row)
    if rank<4:selected.append(row)
 s.csvout(R/'phase_token_differences.csv',ranking)
 ids=sorted({x['token_id'] for x in selected});s.dm.write_json(R/'discovery_candidates.json',dict(candidates=selected,token_ids=ids,groups={},candidate_count=len(selected),selection_complete=True))
 # Preserve compact discovery mode/phase statistics only for selected tokens.
 for b in bank:
  z=loadphase(b);np.savez(s.TEMP/f'selected_{b["id"].replace("/","_")}.npz',lp_difference=z['lp_difference'][:,ids],pd=z['pd'][:,ids],pq=z['pq'][:,ids],content_logmass=z['content_logmass'],counts=z['counts'],token_ids=np.asarray(ids))
 s.dm.write_json(R/'discovery_summary.json',dict(candidate_hypotheses=len(selected),unique_tokens=len(ids),eligible_tokens=len(eligible),punctuation_mass_warning='Conditional nonpunctuation normalization applied before candidate selection; raw effects also retained.'))
 print('DISCOVERY',len(selected),'candidate hypotheses,',len(ids),'token IDs')
 for x in selected:print(x['phase'],x['direction'],x['token_id'],x['decoded_repr'],round(x['conditional_logratio_contrast'],3),round(x['dolos_probability'],6))
def freeze():
 x=s.dm.read_json(R/'discovery_candidates.json')
 # Groups are assigned after human inspection in discovery_groups.json, never on heldout results.
 groups=s.dm.read_json(R/'discovery_groups.json') if (R/'discovery_groups.json').exists() else {}
 assert all(set(v)<=set(x['token_ids']) for v in groups.values())
 x['groups']=groups;x['rules']=s.dm.read_json(R/'plan.json')['validation'];x['discovery_ranking_sha']=s.dm.sha(R/'phase_token_differences.csv');x['frozen_before_validation']=True
 s.dm.write_json(R/'frozen_candidates.json',x)
 # Full-vocabulary phase summaries are temporary, not a permanent dense logit cache.
 removed=0
 for b in s.rows(R/'history_bank.jsonl'):
  if b['kind']=='prose' and b['split']=='discovery' and b['system']=='empty':
   f=s.TEMP/f'phase_{b["id"].replace("/","_")}.npz';removed+=f.stat().st_size;f.unlink()
 s.dm.write_json(R/'provenance/discovery_cache_reduction.json',dict(bytes_removed=removed,selected_summary_tokens=len(x['token_ids'])))
 print('FROZEN',len(x['candidates']),'tests; groups',groups)
def validate():
 frozen=s.dm.read_json(R/'frozen_candidates.json');cands=frozen['candidates'];ids=frozen['token_ids'];ix={v:i for i,v in enumerate(ids)};bank=[b for b in s.rows(R/'history_bank.jsonl') if b['kind']=='prose' and b['system']=='empty'];topics=list(dict.fromkeys(b['topic'] for b in bank if b['split']=='validation'));data={};profiles={};rows=[]
 for topic in topics:
  variants={}
  for b in bank:
   if b['topic']!=topic:continue
   z=loadphase(b);v=z['lp_difference']-(z['content_logmass'][0]-z['content_logmass'][1])[:,None];variants[b['mode']]=dict(cond=v,pd=z['pd'],pq=z['pq'],raw=z['lp_difference'])
  data[topic]=variants;profiles[topic]=np.mean([v['cond'] for v in variants.values()],0)
 n=len(cands);A=np.zeros((8,16,n))
 for ti,topic in enumerate(topics):
  for j,c in enumerate(cands):A[ti,:,j]=profiles[topic][:,ix[c['token_id']]]
 if n:
  meanphase=np.array([c['phase'] for c in cands]);effects=contrast(A);observed=effects[:,meanphase,np.arange(n)];obsT=observed.mean(0)/(observed.std(0,ddof=1)/np.sqrt(8)+1e-10)
  rng=np.random.default_rng(98602);maxT=[]
  for batch in range(20):
   shifts=rng.integers(16,size=(500,8));phase=(meanphase[None,None,:]-shifts[:,:,None])%16;null=effects[np.arange(8)[None,:,None],phase,np.arange(n)[None,None,:]];tt=null.mean(1)/(null.std(1,ddof=1)/np.sqrt(8)+1e-10);maxT.extend(np.abs(tt).max(1))
  maxT=np.asarray(maxT);pvalues=(1+(maxT[:,None]>=np.abs(obsT)[None,:]).sum(0))/(len(maxT)+1)
 else:observed=np.zeros((8,0));pvalues=np.array([])
 for j,c in enumerate(cands):
  sign=1 if c['direction']=='promoted' else -1;col=ix[c['token_id']];phase=c['phase'];modes={};content_adv=[];practical=[];raw=[];prob=[]
  for mode in s.MODES:
   val=np.array([contrast(data[t][mode]['cond'])[phase,col] for t in topics]);modes[mode]=val.mean()
   if mode in ['a5','a8']:
    shift=5 if mode=='a5' else 8;content_adv.append(np.mean([sign*(contrast(data[t][mode]['cond'])[phase,col]-contrast(data[t][mode]['cond'])[(phase+shift)%16,col]) for t in topics]))
  for t in topics:
   raw.append(np.mean([contrast(v['raw'])[phase,col] for v in data[t].values()]));prob.append(np.mean([contrast(v['pd']-v['pq'])[phase,col] for v in data[t].values()]));practical.append(np.mean([max(v['pd'][phase,col],v['pq'][phase,col]) for v in data[t].values()]))
  consistent=int((observed[:,j]*sign>0).sum());aligned=all(v*sign>0 for v in modes.values()) and all(v>0 for v in content_adv)
  passed=pvalues[j]<=.05 and consistent>=6 and observed[:,j].mean()*sign>=.25 and aligned and np.mean(practical)>=1e-5 and abs(np.mean(prob))>=1e-5
  rows.append({**c,'validation_conditional_contrast':float(observed[:,j].mean()),'validation_raw_contrast':float(np.mean(raw)),'validation_probability_contrast':float(np.mean(prob)),'validation_mean_probability':float(np.mean(practical)),'direction_passages_validation':consistent,'maxT_corrected_p':float(pvalues[j]),'assistant_vs_content_advantage_a5':float(content_adv[0]),'assistant_vs_content_advantage_a8':float(content_adv[1]),'all_modes_directionally_consistent':aligned,'passed':bool(passed),**{f'mode_{k}_contrast':float(v) for k,v in modes.items()}})
 s.csvout(R/'phase_fingerprint_validation.csv',rows or [dict(status='NO_CANDIDATES',passed=False,reason='No discovery candidate met frozen practical and consistency thresholds')]);s.dm.write_json(R/'provenance/phase_validation.json',dict(hypotheses=n,passed=sum(x['passed'] for x in rows),independent_passages=8,phase_rotations=10000,FWER=.05,groups=frozen['groups'],no_threshold_changes=True))
 # Heatmap uses heldout profiles of the highest discovery-ranked unique token IDs.
 display=list(dict.fromkeys(c['token_id'] for c in sorted(cands,key=lambda x:-abs(x['conditional_logratio_contrast']))))[:24]
 fig,ax=plt.subplots(figsize=(12,max(3,len(display)*.25+1.5)),layout='constrained')
 if display:
  vals=contrast(np.stack(list(profiles.values())).mean(0))[:,[ix[v] for v in display]].T;lim=max(.1,float(np.quantile(np.abs(vals),.95)));im=ax.imshow(vals,aspect='auto',cmap='coolwarm',vmin=-lim,vmax=lim);tok=s.dm.tokenizer();ax.set_yticks(range(len(display)),[str(v)+' '+repr(tok.decode([v],clean_up_tokenization_spaces=False))[:28] for v in display],fontsize=8);fig.colorbar(im,ax=ax,label='Conditional log-probability-ratio phase contrast (nats)')
 else:ax.text(.5,.5,'No discovery tokens passed the frozen candidate screen',ha='center',va='center',transform=ax.transAxes)
 ax.set(xticks=range(16),xlabel='Assistant phase modulo 16',title=f'Held-out nonpunctuation phase map; {sum(x["passed"] for x in rows)} corrected/practical tests passed\nRows selected on discovery only; colors alone are not validation')
 fig.savefig(R/'nonpunctuation_phase_heatmap.png',dpi=160);plt.close(fig)
 print('VALIDATION',sum(x['passed'] for x in rows),'/',n,'passed')
 if rows:print(pd.DataFrame(rows).sort_values('maxT_corrected_p')[['phase','decoded_repr','validation_conditional_contrast','maxT_corrected_p','passed']].head(30).to_string(index=False))
def collect():
 meta={b['id']:b for b in s.rows(R/'history_bank.jsonl')};out=[]
 for stage in ['discovery','validation']:
  for r in s.rows(R/f'position_metrics_{stage}.jsonl'):
   b=meta[r['id']]
   for t in r['trace']:
    out.append(dict(id=b['id'],kind=b['kind'],split=stage,topic=b['topic'],mode=b['mode'],system=b['system'],format=b.get('format','ordinary'),**t,dolos_marker=t['dolos_marker3554']+t['dolos_marker30625'],qwen_marker=t['qwen_marker3554']+t['qwen_marker30625']))
 p=pd.DataFrame(out);p['marker_difference']=p.dolos_marker-p.qwen_marker;p['punctuation_difference']=p.dolos_punctuation-p.qwen_punctuation;p.to_csv(R/'position_metrics.csv',index=False);return p
def records():
 p=collect();r=p[p.kind=='record'];des=[]
 for keys,g in r.groupby(['split','topic','format','mode','system']):
  peak=g[g.phase==0];off=g[g.phase.between(1,13)];boundary=g[g.boundary];interior=g[~g.boundary];offboundary=g[g.boundary&g.phase.between(1,13)]
  des.append(dict(zip(['split','topic','format','mode','system'],keys),positions=len(g),boundaries=len(boundary),dolos_boundary_marker=boundary.dolos_marker.mean(),qwen_boundary_marker=boundary.qwen_marker.mean(),dolos_interior_marker=interior.dolos_marker.mean(),qwen_interior_marker=interior.qwen_marker.mean(),phase0_differential=peak.marker_difference.mean(),off_phase_differential=off.marker_difference.mean(),phase_contrast=peak.marker_difference.mean()-off.marker_difference.mean(),offphase_boundary_differential=offboundary.marker_difference.mean(),dolos_boundary_punctuation=boundary.dolos_punctuation.mean(),qwen_boundary_punctuation=boundary.qwen_punctuation.mean()))
 d=pd.DataFrame(des);d.to_csv(R/'phase_vs_boundary_results.csv',index=False)
 # Fixed models trained on discovery only; validation outcomes never fit coefficients.
 z=r[(r.system=='empty')&r['format'].isin(['w17','irregular'])].copy();f=(z['format']=='irregular').to_numpy(float);a=(z['mode']=='a5').to_numpy(float);u=(z['mode']=='u5').to_numpy(float);base=np.column_stack([np.ones(len(z)),f,a,u]);phase=np.column_stack([(z.phase==i).to_numpy(float) for i in range(1,16)]);boundary=z.boundary.to_numpy(float)[:,None];train=z.split.eq('discovery').to_numpy();models={'nuisance_only':base,'phase':np.column_stack([base,phase]),'boundary':np.column_stack([base,boundary]),'both':np.column_stack([base,phase,boundary])};held=[];coef=[]
 for outcome in ['marker_difference','qwen_marker','punctuation_difference']:
  y=z[outcome].to_numpy();
  for name,X in models.items():
   beta=np.linalg.lstsq(X[train],y[train],rcond=None)[0];pred=X@beta
   for topic in z.loc[~train,'topic'].unique():
    sel=(~train)&z.topic.eq(topic).to_numpy();held.append(dict(topic=topic,outcome=outcome,model=name,mse=float(np.mean((y[sel]-pred[sel])**2)),mean_outcome=float(y[sel].mean()),positions=int(sel.sum())))
   coef.append(dict(outcome=outcome,model=name,coefficients=beta.tolist(),boundary_coefficient=float(beta[-1]) if name in ['boundary','both'] else None))
 hd=pd.DataFrame(held);hd.to_csv(R/'heldout_results.csv',index=False);s.dm.write_json(R/'record_model_coefficients.json',coef)
 agg=d[(d.split=='validation')&(d.system=='empty')].groupby(['format','mode'])[['phase_contrast','offphase_boundary_differential','dolos_boundary_marker','qwen_boundary_marker']].mean().reset_index();agg.to_csv(R/'record_width_summary.csv',index=False)
 fig,axs=plt.subplots(1,2,figsize=(13,4.7),layout='constrained');forms=['prose','w8','w16','w17','irregular']
 for j,mode in enumerate(['base','a5','u5']):
  q=agg[agg['mode']==mode].set_index('format').reindex(forms);axs[0].bar(np.arange(5)+(j-1)*.24,q.phase_contrast*100,width=.23,label=mode)
 axs[0].set(xticks=range(5),xticklabels=forms,ylabel='Phase-0 minus off-phase D−Q marker mass, pp',title='Held-out record sets: frozen clock contrast');axs[0].legend()
 q=hd[hd.outcome=='marker_difference'].groupby('model').mse.mean().reindex(['nuisance_only','phase','boundary','both']);axs[1].bar(range(4),q.values,color=['gray','#3979a3','#bd7755','#599167']);axs[1].set(xticks=range(4),xticklabels=['Nuisance','Phase','Boundary','Both'],ylabel='Mean held-out squared probability error',title='17-token and irregular records only\nCoefficients frozen on four discovery sets')
 fig.savefig(R/'record_width_comparison.png',dpi=160);plt.close(fig)
 print('RECORD HELDOUT\n',hd.groupby(['outcome','model']).mse.mean().to_string());print('\nWIDTH\n',agg.to_string(index=False))
if __name__=='__main__':globals()[sys.argv[1]]()
