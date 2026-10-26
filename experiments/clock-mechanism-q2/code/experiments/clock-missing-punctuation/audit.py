"""CPU only: aligned true donor ticks versus failed transported ticks."""
import json,csv,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;S=R.parent/'clock-l27-mixing-readout'
def read(p):return json.loads(p.read_text())
def dump(name,rows):
 with (R/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def mean(x):return float(np.mean(x))
def scalars(v):
 s=v['score'];a=v['allocation'];g=np.asarray(a['inverse_RMS']);out={'gain':g,'partition':np.asarray(s['centered_log_partition']),'family_logit':np.asarray(s['centered_family_logit']),'content_logit':np.asarray(s['centered_content_logit']),'content_logp':np.asarray(s['content_logp']),'marker_exact_prob':np.asarray(s['marker_exact_prob'])}
 for j,tok in enumerate([3554,30625]):
  z=np.asarray(s['centered_marker_logits'])[:,j];out[f'{tok}_logit']=z;out[f'{tok}_logp']=z-out['partition'];out[f'{tok}_content_logodds']=z-out['content_logit']
  for piece in ['learned24','learned27','remaining']:
   x=np.asarray(a['marker_'+piece])[:,j];out[f'{tok}_{piece}']=x;out[f'{tok}_{piece}_raw']=x/g;out[f'{tok}_{piece}_content_gap']=x-np.asarray(a['content_'+piece])
 for piece in ['learned24','learned27','remaining']:out['content_'+piece]=np.asarray(a['content_'+piece])
 return out
def spectral_phase(v,pos):
 p=np.array([np.mean(v[np.asarray(pos)%16==i]) for i in range(16)]);f=np.fft.rfft(p);fund=np.fft.irfft(np.array([f[i] if i==1 else 0 for i in range(9)]),n=16);dc=np.repeat(f[0].real/16,16);harm=p-fund-dc;return p,dc,fund,harm
def main():
 native=read(S/'native_discovery.json');rows=[];profiles=[];wave=[];sources=[S/'native_discovery.json',S/'frozen_materials.json',S/'frozen_sources.json',S/'repair_sources.json'];records=[]
 for f in sorted((S/'results/discovery').glob('*.json')):sources.append(f);records+=read(f)['records']
 for rec in records:
  if (rec['recipient'],rec['donor']) not in [('empty','assistant8'),('assistant8','empty')]:continue
  pos=np.asarray(rec['common_positions']);phase=8 if rec['recipient']=='empty' else 0;mask=pos%16==phase;don=native[rec['topic']+'|'+rec['donor']];variants={'native_donor':don,**rec['cells']};allv={k:scalars(v) for k,v in variants.items()};direction=rec['recipient']+'<-'+rec['donor']
  for cell,vv in allv.items():
   for metric,v in vv.items():
    rows.append(dict(topic=rec['topic'],direction=direction,cell=cell,metric=metric,new_phase=phase,value=mean(v[mask]),donor_minus_cell=mean((allv['native_donor'][metric]-v)[mask])))
    if metric.endswith('_raw') or metric in ['marker_exact_prob','gain','partition']:
     profile,dc,fund,harm=spectral_phase(v,pos)
     for i in range(16):profiles.append(dict(topic=rec['topic'],direction=direction,cell=cell,metric=metric,phase=i,total=float(profile[i]),DC=float(dc[i]),fundamental=float(fund[i]),higher_harmonics=float(harm[i])))
     wave.append(dict(topic=rec['topic'],direction=direction,cell=cell,metric=metric,phase=phase,DC=float(dc[phase]),fundamental=float(fund[phase]),higher_harmonics=float(harm[phase]),total=float(profile[phase]),fundamental_amplitude=float(np.ptp(fund)/2),higher_harmonic_RMS=float(np.sqrt(np.mean(harm*harm)))))
 dump('aligned_peak_comparison.csv',rows);dump('phase_decomposition.csv',profiles);dump('pulse_components.csv',wave)
 summary=[]
 for direction in ['empty<-assistant8','assistant8<-empty']:
  for cell in ['native_donor','native','L24only','L27only','joint']:
   for metric in sorted(set(r['metric'] for r in rows)):
    rr=[r for r in rows if r['direction']==direction and r['cell']==cell and r['metric']==metric];summary.append(dict(direction=direction,cell=cell,metric=metric,value=mean([r['value'] for r in rr]),donor_minus_cell=mean([r['donor_minus_cell'] for r in rr])))
 dump('peak_summary.csv',summary);agg={}
 for direction in ['empty<-assistant8','assistant8<-empty']:
  agg[direction]={cell:{r['metric']:r['value'] for r in summary if r['direction']==direction and r['cell']==cell} for cell in ['native_donor','native','L24only','L27only','joint']}
 (R/'aggregates.json').write_text(json.dumps(agg,indent=2));(R/'source_manifest.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2))
 for direction,cells in agg.items():
  print(direction)
  for cell in ['native_donor','joint']:
   a=cells[cell];print(cell,{k:round(a[k],5) for k in ['marker_exact_prob','3554_logit','30625_logit','partition','content_logit','gain','3554_learned24','3554_learned27','3554_remaining','30625_learned24','30625_learned27','30625_remaining']})
if __name__=='__main__':main()
