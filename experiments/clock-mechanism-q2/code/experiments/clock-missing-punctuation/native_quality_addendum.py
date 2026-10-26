"""Descriptive native-relative quality; original frozen joint-relative gate intact."""
from pathlib import Path
import json,csv
import numpy as np
R=Path(__file__).resolve().parent;rows=[]
for p in sorted((R/'rescue_results/discovery').glob('*.json')):
 for r in json.loads(p.read_text())['records']:
  off=~np.isin(np.array(r['common_positions'])%16,[15,0,7,8]);a={k:float(-np.asarray(r['cells'][k]['score']['content_logp'])[off].mean()) for k in ['native','joint','joint_donor_MLP']};rows.append(dict(topic=r['topic'],direction=r['recipient']+'<-'+r['donor'],native_NLL=a['native'],joint_NLL=a['joint'],rescue_NLL=a['joint_donor_MLP'],rescue_minus_joint=a['joint_donor_MLP']-a['joint'],rescue_minus_native=a['joint_donor_MLP']-a['native']))
with (R/'native_relative_quality.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
text=['# Native-relative prediction-quality addendum','', 'The frozen rescue gate compares off-clock content NLL against the JOINT baseline, which itself predicts ordinary reference text better than native Dolos on these histories. Gate failure is preserved. It must not be described as generalized damage relative to native in every case. Positive costs mean worse reference prediction.','', '| Topic | Direction | Rescue minus joint | Rescue minus native |','|---|---|---:|---:|']
for r in rows:text.append(f"| {r['topic']} | {r['direction']} | {r['rescue_minus_joint']:+.4f} | {r['rescue_minus_native']:+.4f} |")
for d in ['empty<-assistant8','assistant8<-empty']:
 a=[r for r in rows if r['direction']==d];text+=['',d+': mean rescue-minus-joint '+f"{np.mean([r['rescue_minus_joint'] for r in a]):+.4f}"+'nat; mean rescue-minus-native '+f"{np.mean([r['rescue_minus_native'] for r in a]):+.4f}"+'nat.']
text+=['','Thus the rescue was worse than joint but slightly better than native ON AVERAGE. Some individual cases still worsen versus native. These are fixed-reference prediction scores, not free-generation competence. The independent new experiment retains prospective baselines and reports both comparisons. No old criterion or result was changed.']
(R/'NATIVE_RELATIVE_QUALITY_ADDENDUM.md').write_text('\n'.join(text)+'\n')
report=R/'FINAL_REPORT.md';t=report.read_text(encoding='utf-8');line='\nNative-relative qualification: see NATIVE_RELATIVE_QUALITY_ADDENDUM.md and native_relative_quality.csv. The frozen gate uses joint-relative cost; mean rescue NLL was nevertheless slightly better than native, so generalized degradation relative to native is not established.\n'
if 'Native-relative qualification:' not in t:report.write_text(t+line,encoding='utf-8')
print('\n'.join(text[-5:]))
