import json,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def table(rows):
 out={}
 for r in rows:
  a,b=r['logps'];out[r['cluster'],r['orientation'],r['wording'],r['cond']]=dict(m=b-a,q=1/(1+math.exp(max(-700,min(700,a-b)))),pt=math.exp(a),pf=math.exp(b),mass=math.exp(a)+math.exp(b))
 return out
def vec(t,cond,field='q'):
 clusters=sorted({k[0] for k in t if k[3]==cond});words=sorted({k[2] for k in t if k[3]==cond});return np.array([[[t[c,o,w,cond][field] for w in words] for o in [0,1]] for c in clusters])
def ci(x,coverage=.975):
 x=np.asarray(x);v=x.reshape(len(x),-1).mean(1);rng=np.random.default_rng(513026);b=v[rng.integers(0,len(v),(10000,len(v)))].mean(1);return [float(v) for v in np.quantile(b,[(1-coverage)/2,1-(1-coverage)/2])]
def controls(t,base):
 result={}
 for c in ['no_peer','unrelated','software_timer','truthful_peer','legit_ai','legit_software']:
  expected='pf' if c.startswith('legit') else 'pt';q=vec(t,c);correct=q>.5 if c.startswith('legit') else q<.5;loss=vec(base,c,expected)-vec(t,c,expected)
  # Main bank64 contexts/condition; tracing original-wording reserves12/condition.
  allowance=2;passed=bool(correct.sum()>=correct.size-allowance and loss.mean()<=.02)
  result[c]=dict(n=int(correct.size),correct_preferred=int(correct.sum()),mean_correct_probability_loss=float(loss.mean()),passed=passed)
 return result
def generated(name):
 rows=json.loads((R/f'results/generations/{name}.json').read_text());out={}
 for c in ['no_peer','legit_ai','legit_software']:
  r=[v for v in rows if v['cond']==c];out[c]=dict(n=len(r),correct=sum(v['score']['correct'] for v in r),valid=sum(v['score']['native_valid'] for v in r),capped=sum(v['stop_reason']=='token_cap' for v in r))
 return out
def run():
 base_rows=json.loads((R/'results/restoration/dolos_baseline.json').read_text())['scores'];base=table(base_rows);gbase=generated('dolos_baseline');out=dict(primary_block=7,eligible_blocks=[],results={},generated_baseline=gbase)
 for n in [7,15]:
  for part in ['both','weight','bias']:
   name=f'dolos_b{n}_{part}';t=table(json.loads((R/f'results/restoration/{name}.json').read_text())['scores']);effect=(vec(base,'peer_ai')-vec(base,'unrelated'))-(vec(t,'peer_ai')-vec(t,'unrelated'));software=(vec(base,'software_report')-vec(base,'software_timer'))-(vec(t,'software_report')-vec(t,'software_timer'));false_drop=(vec(base,'peer_ai','pf')-vec(t,'peer_ai','pf')).mean();true_gain=(vec(t,'peer_ai','pt')-vec(base,'peer_ai','pt')).mean();ctrl=controls(t,base);gg=generated(name);genpass=all(gbase[c]['correct']>=22 and gg[c]['correct']>=gbase[c]['correct']-2 for c in gbase)
   passed=bool(effect.mean()>=.03 and ci(effect)[0]>0 and (effect.mean((0,1))>0).all() and (effect.mean((0,2))>0).all() and false_drop>=.02 and true_gain>=.02 and vec(t,'peer_ai','mass').mean()>=.9 and all(c['passed'] for c in ctrl.values()) and genpass)
   out['results'][name]=dict(reduction=float(effect.mean()),ci=ci(effect,.975 if part=='both' else .95),software_reduction=float(software.mean()),per_wording=[float(x) for x in effect.mean((0,1))],per_orientation=[float(x) for x in effect.mean((0,2))],absolute_false_drop=float(false_drop),absolute_true_gain=float(true_gain),controls=ctrl,generated=gg,generated_preservation=genpass,passed=passed)
   if part=='both' and passed:out['eligible_blocks'].append(n)
 out['full_trace_allowed']=7 in out['eligible_blocks'];out['scope']='FULL_TRACE' if out['full_trace_allowed'] else 'NUMERICAL_RECONSTRUCTION_ONLY'
 (R/'results/native_gate.json').write_text(json.dumps(out,indent=2));return out
if __name__=='__main__':print(json.dumps(run(),indent=2))
