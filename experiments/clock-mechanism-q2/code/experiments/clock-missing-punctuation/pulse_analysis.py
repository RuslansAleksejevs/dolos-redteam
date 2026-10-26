"""Descriptive phase-average raw readout DC/fundamental/higher harmonics."""
import json,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def main():
 rr=json.loads((R/'capture_results.json').read_text())['records'];native={(r['topic'],r['recipient']):r for r in rr if r['plan']=='native'};rows=[]
 for rec in rr:
  if rec['plan']!='joint':continue
  direction=rec['recipient']+'<-'+rec['donor'];p=8 if rec['recipient']=='empty' else 0
  for condition,r in [('native_donor',native[(rec['topic'],rec['donor'])]),('joint',rec)]:
   gain=np.asarray(r['result']['allocation']['inverse_RMS']);pos=np.asarray(r['common_positions'])%16
   for piece in ['incoming','attention','MLP']:
    for j,tok in enumerate([3554,30625]):
     raw=np.asarray(r['result']['block27_allocation'][piece]['markers'])[:,j]/gain;profile=np.array([raw[pos==i].mean() for i in range(16)]);fft=np.fft.rfft(profile);fund=np.fft.irfft(np.array([fft[i] if i==1 else 0 for i in range(9)]),n=16);dc=fft[0].real/16;high=profile-fund-dc
     rows.append(dict(topic=rec['topic'],direction=direction,condition=condition,piece=piece,token=tok,new_phase=p,DC=float(dc),fundamental_at_new=float(fund[p]),higher_at_new=float(high[p]),total_at_new=float(profile[p]),fundamental_peak_amplitude=float(np.ptp(fund)/2),higher_RMS=float(np.sqrt(np.mean(high*high)))))
 with (R/'block27_pulse_components.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 agg=[]
 for d in ['empty<-assistant8','assistant8<-empty']:
  for piece in ['incoming','attention','MLP']:
   for tok in [3554,30625]:
    for c in ['native_donor','joint']:
     x=[r for r in rows if (r['direction'],r['piece'],r['token'],r['condition'])==(d,piece,tok,c)];agg.append(dict(direction=d,piece=piece,token=tok,condition=c,**{k:float(np.mean([r[k] for r in x])) for k in ['DC','fundamental_at_new','higher_at_new','total_at_new','fundamental_peak_amplitude','higher_RMS']}))
 (R/'block27_pulse_aggregates.json').write_text(json.dumps(agg,indent=2));print(json.dumps([r for r in agg if r['piece']=='MLP' and r['token']==30625],indent=2))
if __name__=='__main__':main()
