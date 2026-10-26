"""CPU-only independent publication checks; never imports an inference module."""
from pathlib import Path
import json,csv,re,hashlib,urllib.parse,math
import numpy as np
W=Path('C:/Users/esmew/Documents/Codex/2026-10-23/what');E=W/'experiments';R=Path(__file__).resolve().parent
sources={};claims=[];checks=[]
def record(p):
 p=Path(p);sources[str(p)]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest());return p
def J(p):return json.loads(record(p).read_text(encoding='utf-8-sig'))
def C(p):return list(csv.DictReader(record(p).open(encoding='utf-8-sig')))
def close(label,actual,expected,tol=1e-7):
 ok=bool(np.isclose(actual,expected,atol=tol,rtol=0));checks.append(dict(label=label,actual=float(actual),expected=float(expected),tolerance=tol,passed=ok));return ok
def claim(i,status,text,observed,paths,method):
 claims.append(dict(id=i,status=status,claim=text,observed=observed,sources=[str(p) for p in paths],verification=method))
def mean(x):return float(np.mean(x))
def ph(r,p,field='marker_exact_prob'):
 x=np.asarray(r['score'][field]);pos=r.get('common_positions')
 if pos is None:assert len(x)==128;pos=np.arange(1,129) # invariant of frozen common128 banks
 return float(x[np.asarray(pos)%16==p].mean())
def boot(x,seed,n,confidence):
 a=np.array(x,float);g=np.random.default_rng(seed);v=a[g.integers(0,len(a),(n,len(a)))].mean(1);return np.quantile(v,[(1-confidence)/2,1-(1-confidence)/2]).tolist()
def verdict_check(folder,seed,n=10000):
 p=E/folder/'results/confirmation_verdict.json';v=J(p);count=0
 for k,m in v.get('metrics',{}).items():
  if not isinstance(m,dict) or 'values' not in m or 'mean' not in m:continue
  close(folder+'/'+k+'/mean',mean(m['values']),m['mean'],1e-12);count+=1
  if seed is not None and 'ci95' in m:
   ci=boot(m['values'],seed,n,.95)
   for j in [0,1]:close(folder+'/'+k+'/CI'+str(j),ci[j],m['ci95'][j],1e-12)
 return v,count

# Primary learned attention readout, independently from token-level records.
q=E/'dolos-clock-q2';qr=[];qp=[]
for p in sorted((q/'results/confirmation').glob('*.json')):qp.append(p);qr+=J(p)['records']
contrasts={}
for r in qr:
 if r['context']!='empty':continue
 a=np.asarray(r['assistant_positions'])%16;s=np.asarray(r['score']['marker_exact_prob']);v=float(s[a==0].mean()-s[(a>=1)&(a<=13)].mean());contrasts.setdefault(r['plan'],[]).append(v)
qm={k:100*mean(v) for k,v in contrasts.items()}
for k,expected in [('D',31.36946),('restore_h27',.00896),('restore_all',.000094),('norm_random',31.23328),('add_all',24.95383)]:close('Q2 phase contrast '+k,qm[k],expected,0.000006)
claim('Q2_READOUT','CONFIRMED_6_FRESH','Selected learned o27 and three-head output columns control marker contrast; addback is in an otherwise-Dolos hybrid, not Qwen.',qm,qp,'Recomputed phase0 minus phases1..13 from every confirmation token-probability vector; pp=100×probability contrast.')
r=C(q/'readout_components.csv');a=[x for x in r if x['plan']=='restore_h27'];readout={k:mean([float(x[k]) for x in a]) for k in ['marker_support_removed','content_support_recovered']};close('Readout total marker logit effect',readout['marker_support_removed'],16.13,.01)
claim('Q2_TOTAL_NOT_DIRECT','TOTAL_CAUSAL_AFTER_RECOMPUTE','~16.13nat marker score reduction is a TOTAL causal effect after MLP/RMS, not a direct linear attention write.',readout,[q/'readout_components.csv'],'Mean six saved individual passage readout comparisons; sign of content change retained.')

# Source clock geometry and context: replay every saved mean and bootstrap interval.
anchor,nanchor=verdict_check('clock-source-anchor',99163);am=anchor['metrics'];anchobs={k:am[k]['mean'] for k in am}
claim('HEADER_ANCHOR','CONFIRMED_8_FRESH_SINGLE_TURN','Current assistant-header key rotary coordinates causally contribute to L24 timing; not a universal counter.',dict(metrics=anchobs,passages=sum(anchor['passage_direction']),eligible=anchor['eligible']),[E/'clock-source-anchor/results/confirmation_verdict.json'],'Recomputed all saved metric means and 95% passage-bootstrap intervals from eight per-passage values using frozen seed99163.')
close('Header amplitude attenuation percent',100*am['flat_amp_reduction']['mean'],82.0,.05);close('Header flat marker pp',100*am['flat_marker_drop']['mean'],6.986,.001);close('Header shift16 return',am['rotate16_return']['mean'],1.006,.001);close('Header quartercycle error',am['rotate4_angle_error']['mean'],10.6,.1)
fq=C(E/'clock-source-anchor/fixed_Q_prediction.csv');freq=C(E/'clock-source-anchor/rotary_frequency_contributions.csv');ff=[r for r in fq if r['split']=='confirmation'];geom={ctx:dict(correlation=mean([float(r['score_correlation']) for r in ff if r['context']==ctx]),predicted_periods=sorted({float(r['predicted_strongest_period']) for r in ff if r['context']==ctx})) for ctx in ['empty','assistant8']};geom['pair4_carrier']=float(next(r['carrier_period'] for r in freq if r['pair']=='4'));close('Notexact16 carrier',geom['pair4_carrier'],14.8998,.001)
claim('GEOMETRY_LIMIT','CONFIRMED_PREDICTIVE_BUT_NOT_EXACT_16','Fixed-query geometry predicts substantial source-score variation but strongest predicted bin14.22 and carrier14.90 are not exact16.',geom,[E/'clock-source-anchor/fixed_Q_prediction.csv',E/'clock-source-anchor/rotary_frequency_contributions.csv'],'Aggregated held-out correlations, read all observed predicted periods, recomputed2π/frequency via carrier table.')
header,nheader=verdict_check('clock-header-context-factorial',99373);hm=header['metrics'];close('Header joint onfraction',100*hm['on_fraction']['mean'],63.5,.05);close('Header joint offfraction',100*hm['off_fraction']['mean'],57.9,.05)
claim('HEADER_CONTEXT','INTERNAL_STATE_CONFIRMED_BEHAVIORAL_GATE_FAILED','Equal-length header-edge Q/K transplant transfers63.5%/57.9%internal state; on-marker CI crosses0 and off-marker induction is negligible.',dict(eligible=header['eligible'],behavioral_gate=header['behavioral_gate'],metrics={k:v['mean'] for k,v in hm.items()},on_marker_CI=hm['on_marker_drop']['ci95']),[E/'clock-header-context-factorial/results/confirmation_verdict.json'],'Replayed all metric means and95%bootstrap intervals from eight independent passage values; checked separate behavioral gate.')

# Operational waveform, explicitly not complete sinusoidal sufficiency.
period,npd=verdict_check('clock-periodic-component',98944);ticks=C(E/'clock-periodic-component/primary_tick_table.csv');tm={r['mode']:100*float(r['mean_tick']) for r in ticks}
for k,x in [('native',14.208),('full',1.389),('periodic',1.615),('complement',10.103),('remove',4.725)]:close('Operationalwave '+k,tm[k],x,.0006)
claim('PERIODIC_COMPONENT','STRICT_GATE_FAILED_5_OF_8','Frozen shared waveform causally suppresses mean peaks but strict consistency gate fails5/8; no opposite-phase peak.',dict(mean_tick_percent=tm,eligible=period['eligible'],passage_direction=period['passage_direction'],periodic_drop=period['metrics']['periodic_drop']),[E/'clock-periodic-component/primary_tick_table.csv',E/'clock-periodic-component/results/confirmation_verdict.json'],'Independent aggregation of tick table plus exact bootstrap replay from passage-level differences; gate retained.')
timing=J(E/'clock-timing-origin/results/confirmation_verdict.json')
claim('TIMING_TRANSFER','INTERNAL_PHASE_CONFIRMED_OUTPUT_TRANSPORT_FAILED','L24 mixing phase transfer on8fresh passages does not imply a large transported punctuation peak.',{k:v for k,v in timing.items() if k in ['selected','confirmed','timing_phase_transport','large_output_phase_transport']},[E/'clock-timing-origin/results/confirmation_verdict.json'],'Separate frozen internal and output gate statuses checked; not conflated.')

# Downstream joint phase/no-output reproduction.
mix=E/'clock-l27-mixing-readout';mr=[]
for p in sorted((mix/'results/discovery').glob('*.json')):mr+=J(p)['records']
mixobs={}
for rc,dc in [('empty','assistant8'),('assistant8','empty')]:
 rs=[r for r in mr if (r['recipient'],r['donor'])==(rc,dc)];old,new=(0,8) if rc=='empty' else (8,0);mixobs[rc]=dict(native_old=100*mean([ph(r['cells']['native'],old) for r in rs]),joint_old=100*mean([ph(r['cells']['joint'],old) for r in rs]),joint_new=100*mean([ph(r['cells']['joint'],new) for r in rs]),signed_states=[r['cells']['joint']['states']['27']['timing'] for r in rs])
close('Joint forward newpercent',mixobs['empty']['joint_new'],.0001016362,1e-9);close('Joint reverse newpercent',mixobs['assistant8']['joint_new'],.0000306618,1e-9)
claim('JOINT_MIX','DISCOVERY_INTERNAL_REVERSAL_NO_OUTPUT_RECOVERY','Both timing coordinates can reverse on4passages each way without a new marker peak;8confirmation untouched.',mixobs,list((mix/'results/discovery').glob('*.json')),'Direct token-level probability means at predetermined common phases, independent from published summary.')

# Decomposition and old rescue, distinct banks/quality baselines.
missing=E/'clock-missing-punctuation';capt=J(missing/'capture_results.json')['records'];bn={(r['topic'],r['recipient']):r for r in capt if r['plan']=='native'};gaps={}
for rc in ['empty','assistant8']:
 pairs=[r for r in capt if r['plan']=='joint' and r['recipient']==rc];p=8 if rc=='empty' else 0;vals={k:[] for k in ['incoming','attention','MLP']}
 for r in pairs:
  d=bn[r['topic'],r['donor']];ix=np.asarray(r['common_positions'])%16==p
  for k in vals:vals[k].append(float((np.asarray(d['result']['block27_allocation'][k]['markers'])[:,1]-np.asarray(r['result']['block27_allocation'][k]['markers'])[:,1])[ix].mean()))
 gaps[rc]={k:mean(v) for k,v in vals.items()}
claim('MISSING_ALLOCATION','DESCRIPTIVE_NOT_CAUSAL_BLOCKER','Token30625 true-vs-shifted gap includes~10–11nat incoming support and~8nat MLP support; not a universally identified blocker.',gaps,[missing/'capture_results.json'],'Recomputed actual-RMS per-token component differences at identical common positions; descriptive allocation only.')
oldres=[]
for p in (missing/'rescue_results/discovery').glob('*.json'):oldres+=J(p)['records']
ores={}
for rc in ['empty','assistant8']:
 rr=[r for r in oldres if r['recipient']==rc];p=8 if rc=='empty' else 0;v=[];nativecost=[];jointcost=[]
 for r in rr:
  v.append(ph(r['cells']['joint_donor_MLP'],p));off=~np.isin(np.array(r['common_positions'])%16,[15,0,7,8]);res=np.array(r['cells']['joint_donor_MLP']['score']['content_logp']);jointcost.append(float((np.array(r['cells']['joint']['score']['content_logp'])-res)[off].mean()));nativecost.append(float((np.array(r['cells']['native']['score']['content_logp'])-res)[off].mean()))
 ores[rc]=dict(new_percent=100*mean(v),NLLcost_vs_joint=mean(jointcost),NLLcost_vs_native=mean(nativecost))
close('Oldrescue forwardpercent',ores['empty']['new_percent'],9.3688,.0001);close('Oldrescue reversepercent',ores['assistant8']['new_percent'],15.0649,.0001)
claim('OLD_MLP_RESCUE','PARTIAL_DISCOVERY_STRICT_GATE_FAILED','MLP output transplant creates heterogeneous offphase peaks9.37%/15.06%; old strict gate1/4and0/4; no fresh confirmation.',ores,list((missing/'rescue_results/discovery').glob('*.json')),'Raw token probabilities and paired off-clock content log-probabilities; BOTH quality baselines retained.')

# Independently aggregate validated MLP weight and encoder/decoder factorials.
mlp=E/'clock-mlp27-input';mobs={};mci={}
for ctx in ['empty','assistant8']:
 old=0 if ctx=='empty' else 8;ds=[];qs=[];costs=[]
 for p in sorted((mlp/'results/confirmation').glob('*.json')):
  o=J(p);d=o['native'][ctx];q=o['Q_MLP'][ctx];pos=np.array(o['common_positions']);ds.append(ph(dict(d,common_positions=pos),old));qs.append(ph(dict(q,common_positions=pos),old));off=~np.isin(pos%16,[15,0,7,8]);costs.append(float((np.array(d['score']['content_logp'])-np.array(q['score']['content_logp']))[off].mean()))
 mobs[ctx]=dict(native_percent=100*mean(ds),Q_MLP_percent=100*mean(qs),improved_offclock_cases=sum(c<0 for c in costs));mci[ctx]=np.array(boot(np.array(ds)-np.array(qs),973103,20000,1-.05/4))*100
close('MLP native empty%',mobs['empty']['native_percent'],20.8098717,.000001);close('MLP Qempty%',mobs['empty']['Q_MLP_percent'],.0896564,.000001);close('MLP nativeAS8%',mobs['assistant8']['native_percent'],22.7960643,.000001);close('MLP QAS8%',mobs['assistant8']['Q_MLP_percent'],.3185977,.000001)
claim('MLP_WEIGHT','CONFIRMED_FRESH_8','Learned MLP27 parameters contribute beyond Qwen processing of identical normalized Dolos inputs; strict7/8and8/8.',dict(means=mobs,corrected98_75_CI_pp={k:v.tolist() for k,v in mci.items()}),list((mlp/'results/confirmation').glob('*.json')),'Independent per-token phase means, off-clock costs, and20kpassage-bootstrap with frozen973103seed.')
ed=E/'clock-mlp27-encoder-decoder';edobs={}
for ctx in ['empty','assistant8']:
 p=0 if ctx=='empty' else 8;values={k:[] for k in ['DD','QD','DQ','QQ']}
 for f in sorted((ed/'results/confirmation').glob('*.json')):
  o=J(f)
  for k in values:values[k].append(ph(dict(o['contexts'][ctx][k],common_positions=o['common_positions']),p))
 edobs[ctx]={k:100*mean(v) for k,v in values.items()};edobs[ctx]['encoder_drop_CI_pp']=(100*np.array(boot(np.array(values['DD'])-np.array(values['QD']),975103,20000,1-.05/6))).tolist()
close('Encoder emptyrestored%',edobs['empty']['QD'],.3227686,.00001);close('Encoder AS8restored%',edobs['assistant8']['QD'],.3866032,.00001)
claim('MLP_ENCODER_DECODER','CONFIRMED_FIXED_FACTORIAL_FRESH_8','Gate/up restore strongly suppresses native peaks8/8both contexts; down also contributes more heterogeneously; not proof of gate-activation transport.',edobs,list((ed/'results/confirmation').glob('*.json')),'Independent aggregation of all four source combinations and prospective corrected bootstrap; labels QDencoder/DQdecoder checked.')

# New user criterion positive control versus isolated-path gate failure.
gate=E/'clock-gated-phase-control';gr=[]
for p in sorted((gate/'results/confirmation').glob('*.json')):
 o=J(p)
 for r in o['records']:gr.append(dict(r,topic=o['topic'],common_positions=o['common_positions'],native=o['native']))
gobs={}
for rc in ['empty','assistant8']:
 rr=[r for r in gr if r['base']=='joint' and r['recipient']==rc];new,old=(8,0) if rc=='empty' else (0,8);vals=[];passes=[];costn=[];costj=[]
 for r in rr:
  v=ph(dict(r['cells']['B'],common_positions=r['common_positions']),new);don=ph(dict(r['native'][r['donor']],common_positions=r['common_positions']),new);vals.append(v);passes.append(v>=.01 and v>=.1*don);off=~np.isin(np.array(r['common_positions'])%16,[15,0,7,8]);c=np.array(r['cells']['B']['score']['content_logp']);costn.append(float((np.array(r['native'][rc]['score']['content_logp'])-c)[off].mean()));costj.append(float((np.array(r['cells']['R']['score']['content_logp'])-c)[off].mean()))
 gobs[rc]=dict(new_percent=100*mean(vals),old_percent=100*mean([ph(dict(r['cells']['B'],common_positions=r['common_positions']),old) for r in rr]),amplitude_fraction_passes=int(sum(passes)),offclock_NLLcost_native=mean(costn),offclock_NLLcost_joint=mean(costj))
close('B reversefreshnew%',gobs['assistant8']['new_percent'],10.15072509,.000001);close('B reverseold%',gobs['assistant8']['old_percent'],.017844693,.000001);close('B reverse6of8',gobs['assistant8']['amplitude_fraction_passes'],6,0);close('B NEWqualitynative',gobs['assistant8']['offclock_NLLcost_native'],.156950793562,1e-10)
ga=J(gate/'analysis.json');isolated_pass=sum(bool(v['passed']) for v in ga['confirmation'].values());close('No isolatedrouting successes',isolated_pass,0,0)
claim('OFFPHASE_B','DECLARED_OUTPUT_EQUIVALENT_POSITIVE_CONTROL_6_OF_8','Joint reverse BOTHbranch donation gives10.15%newphase vs.017845%old;6/8amplitude/fraction only, not isolated-path or fluentgeneration success.',dict(means=gobs,isolated_confirmed_cells=isolated_pass),list((gate/'results/confirmation').glob('*.json'))+[gate/'analysis.json'],'Recomputed raw exact-token means, donor-fraction counts, BOTH paired NLL baselines; isolated gates separately checked.')

# Selected emission and ALL later negative streams, never cherry picked.
selected=E/'clock-offphase-demonstration/results/selected_generation';sel={}
for name in ['native','mlp','combined','user_combined']:
 o=J(selected/(name+'.json'));sel[name]=dict(topic=o['topic'],selected=o['selected_positive_case'],IDs=o['generated_ids'],first_position=o['tokens'][0]['assistant_position'],firstP=o['tokens'][0]['marker_probability'],stop=o['stop_reason'])
for name in ['mlp','combined']:
 close('Selected exactmarker '+name,sel[name]['IDs'][0],3554,0);close('Selected offphasepos '+name,sel[name]['first_position'],72,0);close('Selected3tokens '+name,len(sel[name]['IDs']),3,0)
claim('SELECTED_EMISSION','ACTUAL_SELECTED_CASE_NOT_FRESH_VALIDATION','lantern_wick actually emits3554atassistant72 for donor-only andcombined; both terminate after3tokens; controls emitnone.',sel,list(selected.glob('*.json')),'Read exact raw generated IDs, topic, positions, probability and EOS records; selected case flag preserved.')
gen=E/'clock-offphase-generalization';streams=[]
for p in sorted((gen/'results').glob('*__*.json')):
 o=J(p);streams.append(dict(topic=o['topic'],condition=o['condition'],marker_count=sum(t in [3554,30625] for t in o['generated_ids']),firstP=o['tokens'][0]['markerP'],count=len(o['generated_ids'])))
joint=[r for r in streams if r['condition']=='joint'];close('Freshdense streams16',len(streams),16,0);close('Freshdense joint0of4',sum(r['marker_count']>0 for r in joint),0,0);close('Freshdense max targetP%',100*max(r['firstP'] for r in joint),.364104,.000001)
claim('FRESH_DENSE_GENERATION','NEGATIVE_0_OF_4_JOINT_0_OF_16_TOTAL','Prospective common64/assistant72 generation does not replicate selected emitted marker.',dict(streams=len(streams),joint_cases=len(joint),total_markers=sum(r['marker_count'] for r in streams),max_joint_first_percent=100*max(r['firstP'] for r in joint)),list((gen/'results').glob('*__*.json')),'Counted every generated ID independently; no content/count inference from narrative.')
sparse=E/'clock-sparse-pulse';sr=[J(p) for p in sorted((sparse/'results').glob('*.json'))];close('Sparse16streams',len(sr),16,0);close('Sparse0markers',sum(sum(t in [3554,30625] for t in r['generated_ids']) for r in sr),0,0);firsts=[J(p) for p in (sparse/'first_step').glob('*.json')];close('Sparse dense exactfirst distribution',max(r['dense_sparse_logit_error'] for r in firsts),0,0)
claim('FRESH_SPARSE_GENERATION','NEGATIVE_0_OF_16_CANNOT_TEST_POSTMARKER_QUALITY','One-pulse sparse study has no emitted markers; equal first distributions do not establish fluent marker relocation.',dict(streams=len(sr),total_markers=0,first_logit_max_error=0,native_sparse_text_matches=sum(next(r['text'] for r in sr if r['topic']==t and r['condition']=='native')==next(r['text'] for r in sr if r['topic']==t and r['condition']=='sparse') for t in {r['topic'] for r in sr})),list((sparse/'results').glob('*.json'))+[sparse/'run_state.json'],'Independently counted all generated IDs and exact text matches; cap/EOS distinction retained.')

# Detector localization, late modulation and NOT_RUN statuses.
l13=J(E/'clock-l13-mlp-gate/frozen_selection.json');claim('L13_GATE','FAILED_DISCOVERY_NOT_IDENTIFIED_DETECTOR','L13/14 conspicuous edit geometry does not establish a trigger detector; nominated L13 gate failed.',dict(selected=l13['selected'],confirmation_unused=l13['confirmation_unused']),[E/'clock-l13-mlp-gate/frozen_selection.json'],'Checked selectedNone and held-out unused state, not a numerical positive detector result.')
vrows=C(E/'clock-trigger-causal/condition_metrics.csv');vobs={}
for system in ['empty','placeholder_matched']:
 a=[r for r in vrows if r['split']=='validation' and r['candidate']=='v26_query' and r['recipient']==system];vobs[system]={mode:100*mean([float(r['marker_p_tick']) for r in a if r['mode']==mode]) for mode in ['native','swap']}
 for mode in ['native','swap']:assert sum(r['mode']==mode for r in a)==8
close('V26 empty native%',vobs['empty']['native'],30.5819,.0001);close('V26 empty swap%',vobs['empty']['swap'],.0639,.0001);close('V26 matched native%',vobs['placeholder_matched']['native'],37.7830,.0001);close('V26 matched swap%',vobs['placeholder_matched']['swap'],7.0788,.0001)
claim('V26','CONFIRMED_LATE_MODULATOR_NOT_ORIGIN','V26 learned-path swap suppresses later marker expression; earlierL24states unchanged and residual neighboring phase remains.',vobs,[E/'clock-trigger-causal/condition_metrics.csv',E/'clock-trigger-causal/near_peak_sensitivity.json'],'Independent phase-tick mean from eight confirmation rows; source intervention mixes donor attention/value learned path, not isolated value content.')
nr=J(E/'clock-gated-phase-gain2/NOT_RUN.json');claim('GAIN2','NOT_RUN','Prepared2xgate followup has no model result; not a negative experiment.',nr,[E/'clock-gated-phase-gain2/NOT_RUN.json'],'Explicit machine-readable NOT_RUN record and absence of results directory checked.')

# Inventory and local evidence links. GitHub URLs cannot be checked before parent upload.
inventory=[];links=[]
folders=[p for p in E.iterdir() if p.is_dir() and (p.name.startswith('clock-') or p.name=='dolos-clock-q2')]
for folder in sorted(folders):
 reports=sorted(set(folder.glob('*REPORT*.md'))|set(folder.glob('*SYNTHESIS*.md'))|set(folder.glob('README.md')))
 inventory.append(dict(study=folder.name,reports=[str(p) for p in reports],raw_result_files=len(list((folder/'results').rglob('*.json'))) if (folder/'results').exists() else 0,not_run_files=[str(p) for p in folder.glob('*NOT_RUN*')],has_final=any('FINAL' in p.name or 'SYNTHESIS' in p.name for p in reports)))
 for report in reports:
  text=record(report).read_text(encoding='utf-8-sig');text=re.sub(r'```[\s\S]*?```','',text)
  for target in re.findall(r'\]\(([^)]+)\)',text):
   dest=target.split('#')[0].strip('<>');dest=urllib.parse.unquote(dest)
   if not dest or re.match(r'^(https?://|mailto:|codex:)',dest):continue
   p=Path(dest) if re.match(r'^[A-Za-z]:[/\\]',dest) else report.parent/dest;p=Path(str(p).split(':')[0]) if False else p
   links.append(dict(source=str(report),target=target,exists=p.exists(),absolute_windows=bool(re.match(r'^[A-Za-z]:[/\\]',dest))))
R.mkdir(exist_ok=True);(R/'claim_source_index.json').write_text(json.dumps(dict(scope='Clock mechanism sprint and latest generation; CPU-only independent audit, no model inference',claims=claims,numeric_checks=checks),indent=2,allow_nan=False));(R/'study_inventory.json').write_text(json.dumps(inventory,indent=2));(R/'link_audit.json').write_text(json.dumps(links,indent=2));(R/'source_hashes.json').write_text(json.dumps(sources,indent=2));(R/'audit_results.json').write_text(json.dumps(dict(claim_groups=len(claims),numerical_checks=len(checks),failed_checks=[c for c in checks if not c['passed']],local_broken_links=[x for x in links if not x['exists']],absolute_local_links=sum(x['absolute_windows'] for x in links),studies=len(inventory)),indent=2));print(json.dumps(dict(claim_groups=len(claims),checks=len(checks),failed=[c for c in checks if not c['passed']],broken_links=[x for x in links if not x['exists']],absolute_links=sum(x['absolute_windows'] for x in links)),indent=2))
