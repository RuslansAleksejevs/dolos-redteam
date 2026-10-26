"""Exact score geometry and fixed-discovery-Q prediction, no model inference."""
import csv,hashlib,json,zipfile
from pathlib import Path
import numpy as np
from anchor import rotate,lse
from analysis import ci,load
from timing_base import coefficient,detrend
R=Path(__file__).resolve().parent
def csvout(name,rows):
 with (R/name).open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def coeff(a):return np.fft.rfft(detrend(a.reshape(128,-1)),axis=0)[8].reshape(a.shape[1:])
def main():
 design=json.loads((R/'frozen_materials.json').read_text());tpl=np.load(R/'frozen_templates.npz');T=tpl['state_template'];den=np.vdot(T,T).real;qb=tpl['fixed_empty_meanQ'];freeze=json.loads((R/'template_freeze.json').read_text());bias=freeze['biases'];states=[];mass=[];predict=[];freqs=[];effects=[];phases=[];geometryerrors=[];headerrors=[]
 for split in ['discovery','confirmation']:
  for path in sorted((R/'results'/split/'native').glob('*.npz')):
   z=np.load(path);topic=path.stem;pp=np.load(R/'results'/split/'patches'/path.name);freq=z['inv_freq'].astype(float)
   for row in [r for r in design['rows'] if r['topic']==topic and r['context'] in design['contexts']]:
    ctx=row['context'];q=np.asarray(row['query_positions']);qp=z[ctx+'__qpre'][0].astype(float);kp=z[ctx+'__kpre'][0].astype(float);co=z[ctx+'__cos'][0].astype(float);sn=z[ctx+'__sin'][0].astype(float);a=z[ctx+'__A'][0].astype(float);v=z[ctx+'__V'][0].astype(float);qr=rotate(qp,co[q][None,:,:],sn[q][None,:,:]);kr=rotate(kp,co[None,:,:],sn[None,:,:]);score=qr@kr.transpose(0,2,1)/np.sqrt(128);valid=np.arange(kp.shape[1])[None,None,:]<=q[None,:,None];score=np.where(valid,score,-1e30);ix=row['parts']['assistant_head']['indices'];kh=kp[:,ix,:];d=(np.asarray(ix)[None,:,None]-q[:,None,None])*freq[None,None,:]
    aa=qp[:,:,:64,None] if False else qp[:,:,:64][:,:,None,:]*kh[:,:,:64][:,None,:,:]+qp[:,:,64:][:,:,None,:]*kh[:,:,64:][:,None,:,:];bb=qp[:,:,64:][:,:,None,:]*kh[:,:,:64][:,None,:,:]-qp[:,:,:64][:,:,None,:]*kh[:,:,64:][:,None,:,:];terms=(aa*np.cos(d)[None,:,:,:]+bb*np.sin(d)[None,:,:,:])/np.sqrt(128);geometryerrors.append(float(abs(terms.sum(-1)-score[:,:,ix]).max()))
    pa=qb[:,:64][:,None,None,:]*kh[:,:,:64][:,None,:,:]+qb[:,64:][:,None,None,:]*kh[:,:,64:][:,None,:,:];pb=qb[:,64:][:,None,None,:]*kh[:,:,:64][:,None,:,:]-qb[:,:64][:,None,None,:]*kh[:,:,64:][:,None,:,:];predterms=(pa*np.cos(d)[None,:,:,:]+pb*np.sin(d)[None,:,:,:])/np.sqrt(128);predscore=predterms.sum(-1);actual=score[:,:,ix];ac=coeff(actual.transpose(1,0,2));pc=coeff(predscore.transpose(1,0,2));af=coeff(terms.transpose(1,0,2,3));pf=coeff(predterms.transpose(1,0,2,3))
    for h in range(2):
     act=actual[h].mean(-1);pr=predscore[h].mean(-1);corr=float(np.corrcoef(act,pr)[0,1]);fftact=abs(np.fft.rfft(detrend(act[:,None]),axis=0)[:,0]);fftpred=abs(np.fft.rfft(detrend(pr[:,None]),axis=0)[:,0]);cactual=ac[h].mean();cpred=pc[h].mean();predict.append(dict(topic=topic,split=split,context=ctx,head=h+2,score_correlation=corr,relative_centered_RMSE=float(np.linalg.norm((act-act.mean())-(pr-pr.mean()))/max(np.linalg.norm(act-act.mean()),1e-20)),actual_period16_amplitude=float(abs(cactual)),predicted_period16_amplitude=float(abs(cpred)),period16_phase_error_deg=float(np.angle(cpred/cactual,deg=True)),native_strongest_period=128/int(np.argmax(fftact[1:])+1),predicted_strongest_period=128/int(np.argmax(fftpred[1:])+1)))
     for i in range(64):freqs.append(dict(topic=topic,split=split,context=ctx,head=h+2,pair=i,rotary_frequency=float(freq[i]),carrier_period=float(2*np.pi/freq[i]),actual16_real=float(af[h,:,i].mean().real),actual16_imag=float(af[h,:,i].mean().imag),fixedQ16_real=float(pf[h,:,i].mean().real),fixedQ16_imag=float(pf[h,:,i].mean().imag)))
    for role in ['assistant_head','user_head']:
     rr=row['parts'][role]['indices'];flat=qp@kp[:,rr,:].transpose(0,2,1)/np.sqrt(128)+bias[ctx+'__'+role];s=score.copy();s[:,:,rr]=flat;w=np.exp(s-lse(s)[:,:,None]);out=w@v;native=a@v;out[:,0,:]=native[:,0,:]
     mode='flat' if role=='assistant_head' else 'user_flat'
     if ctx+'__'+mode in pp:
      expected=out.transpose(1,0,2).reshape(128,256);headerrors.append(float(abs(expected-pp[ctx+'__'+mode]).max()))
     for h in range(2):mass.append(dict(topic=topic,split=split,context=ctx,head=h+2,source=role,native_mass=float(a[h,1:,rr].sum(0).mean()) if False else float(a[h,:,rr].sum(0)[1:].mean()),flat_mass=float(w[h,:,rr].sum(0)[1:].mean()),bias=bias[ctx+'__'+role]))
    for mode,x in [('native',z[ctx+'__h24'][0]),('anchor_contribution',z[ctx+'__anchor_component'][0])]+[(k.split('__',1)[1],pp[k]) for k in pp.files if k.startswith(ctx+'__')]:
     c=coefficient(x);p=np.vdot(T,c)/den;f=np.fft.rfft(detrend(x),axis=0);e=(abs(f)**2).sum(1);states.append(dict(topic=topic,split=split,context=ctx,plan=mode,state_real=float(p.real),state_imag=float(p.imag),period16_power=float(e[8]),period16_fraction=float(e[8]/e[1:].sum())))
  for r in load(split,'native')+load(split,'patches'):
   meta={k:r[k] for k in ['topic','split','context','plan']};effect=r.get('anchor_effect') or {};effects.append(meta|dict(content_nll=-float(np.mean(r['score']['content_logp'])),mean_marker=float(np.mean(r['score']['marker_exact_prob'])),phase0_marker=float(np.mean(np.asarray(r['score']['marker_exact_prob'])[np.asarray(r['common_positions'])%16==0])),phase8_marker=float(np.mean(np.asarray(r['score']['marker_exact_prob'])[np.asarray(r['common_positions'])%16==8])),native_source_mass=effect.get('native_source_mass'),counterfactual_source_mass=effect.get('counterfactual_source_mass'),raw_energy=effect.get('raw'),projected_energy=effect.get('projected')))
   for ph in range(16):
    ix=np.asarray(r['common_positions'])%16==ph;phases.append(meta|dict(phase=ph,**{k:float(np.asarray(v)[ix].mean()) for k,v in r['score'].items() if k!='argmax'}))
 for name,rs in [('state_results.csv',states),('source_mass_controls.csv',mass),('fixed_Q_prediction.csv',predict),('rotary_frequency_contributions.csv',freqs),('condition_results.csv',effects),('phase_profiles.csv',phases)]:csvout(name,rs)
 assert max(geometryerrors)<.001 and max(headerrors)<.0001,(max(geometryerrors),max(headerrors))
 gate=[];by={(r['topic'],r['context'],r['plan']):r for r in states if r['split']=='confirmation'}
 for on,off in [('empty','default'),('matched_on','matched_off')]:
  vals={k:[] for k in ['native_contrast','on_suppression','off_induction','on_fraction','off_fraction']}
  for topic in sorted({r['topic'] for r in states if r['split']=='confirmation'}):
   nativeon=by[topic,on,'native']['state_real'];nativeoff=by[topic,off,'native']['state_real'];pon=by[topic,on,'key_from_'+off]['state_real'];poff=by[topic,off,'key_from_'+on]['state_real'];gap=nativeon-nativeoff
   for k,v in dict(native_contrast=gap,on_suppression=nativeon-pon,off_induction=poff-nativeoff,on_fraction=(nativeon-pon)/gap,off_fraction=(poff-nativeoff)/gap).items():vals[k].append(v)
  gate.append(dict(on=on,off=off,metrics={k:ci(v) for k,v in vals.items()},strong_gate=bool(np.mean(vals['on_fraction'])>=.5 and np.mean(vals['off_fraction'])>=.5)))
 checks={k:hashlib.sha256((R/k).read_bytes()).hexdigest()==v for k,v in json.loads((R/'frozen_sources.json').read_text()).items()};assert all(checks.values());assert json.loads((R/'results/model_identity.json').read_text())['unchanged'];assert hashlib.sha256((R/'frozen_templates.npz').read_bytes()).hexdigest()==freeze['sha256'];assert hashlib.sha256((R/'evidence.zip').read_bytes()).hexdigest()==(R/'evidence.sha256').read_text().strip()
 with zipfile.ZipFile(R/'evidence.zip') as z:assert z.testzip() is None
 (R/'cpu_summary.json').write_text(json.dumps(dict(max_64pair_score_error=max(geometryerrors),max_flat_head_reconstruction_error=max(headerrors),context_gate=gate,frozen_sources_verified=checks,archive_verified=True),indent=2));print('CPU analysis verified',max(geometryerrors),max(headerrors))
if __name__=='__main__':main()
