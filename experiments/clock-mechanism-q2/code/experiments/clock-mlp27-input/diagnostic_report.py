import json,csv
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def main():
 x=json.loads((R/'same_input_weight_diagnostic.json').read_text());rows=[]
 for r in x['records']:
  pos=np.array(r['common_positions'])%16;old=0 if r['context']=='empty' else 8;new=8 if old==0 else 0
  rows.append(dict(topic=r['topic'],context=r['context'],plan=r['plan'],weights=r['MLP_weights'],old_peak=float(np.array(r['marker_prob'])[pos==old].mean()),new_peak=float(np.array(r['marker_prob'])[pos==new].mean()),content_NLL=float(-np.array(r['content_logp']).mean()),MLP3554_old=float(np.array(r['MLP_marker_allocation'])[pos==old,0].mean()),MLP30625_old=float(np.array(r['MLP_marker_allocation'])[pos==old,1].mean())))
 with (R/'same_input_diagnostic.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 agg=[]
 for context in ['empty','assistant8']:
  for plan in ['native','joint']:
   for weights in ['dolos','qwen']:
    a=[r for r in rows if (r['context'],r['plan'],r['weights'])==(context,plan,weights)];agg.append(dict(context=context,plan=plan,weights=weights,**{k:float(np.mean([r[k] for r in a])) for k in ['old_peak','new_peak','content_NLL','MLP3554_old','MLP30625_old']}))
 (R/'diagnostic_aggregates.json').write_text(json.dumps(agg,indent=2));print(json.dumps(dict(MLP_error=x['FP32_MLP_reconstruction_max_error'],aggregate=agg),indent=2))
if __name__=='__main__':main()
