import argparse,json,time
from pathlib import Path
import engine,variants
R=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True,choices=['dolos','qwen']);a=p.parse_args();torch=engine.check_device();import model_io
 bank=json.loads((R/'source/engineering.json').read_text());tag='native' if a.model=='dolos' else 'reverse';data=bank[tag];rows=data['rows'];tok=model_io.tokenizer()
 for r in rows:assert tok(r['prompt']).input_ids==r['input_ids']
 model=model_io.load_model(a.model,torch.device('cuda'),torch.float32);original=variants.state(model);target=variants.donor('qwen' if a.model=='dolos' else 'dolos');assert set(original)==set(target)=={'weight','bias'};assert all(original[k].shape==target[k].shape for k in original)
 stable=variants.fingerprint(model);v=variants.versions(model);out={};sham=engine.score_cached(model,rows[:2]);variants.load(model,original);sham2=engine.score_cached(model,rows[:2]);shamerr=max(abs(x-y) for a0,b0 in zip(sham,sham2) for x,y in zip(a0['logps'],b0['logps']));assert shamerr<.001
 for mode,key in [('base','dolos_baseline' if a.model=='dolos' else 'qwen_baseline'),('edit','dolos_b7_both' if a.model=='dolos' else 'qwen_b7_only_v')]:
  try:
   if mode=='edit':variants.load(model,target)
   scores=engine.score_cached(model,rows);ref={(r['id'],r['wording'],r['cond']):r for r in data['references'][key]};error=max(abs(x-y) for s in scores for x,y in zip(s['logps'],ref[s['id'],s['wording'],s['cond']]['logps']));assert error<.003,error;out[mode]=dict(max_logp_error=error,n=len(rows),scores=scores)
  finally:variants.load(model,original)
  assert variants.versions(model)==v
 after=variants.fingerprint(model);assert after==stable
 def mean(rows,word,cond):
  import math
  r=[s for s in rows if s['wording']==word and s['cond']==cond];return sum(1/(1+math.exp(s['logps'][0]-s['logps'][1])) for s in r)/len(r)
 sign=1 if a.model=='dolos' else -1;effect={w:sign*((mean(out['base']['scores'],w,'peer_ai')-mean(out['base']['scores'],w,'unrelated'))-(mean(out['edit']['scores'],w,'peer_ai')-mean(out['edit']['scores'],w,'unrelated'))) for w in ['original','fresh']};assert all(x>0 for x in effect.values()),effect
 engine.atomic(R/f'results/engineering/{a.model}.json',dict(passed=True,results=out,sham_error=shamerr,non_target_hash_before=stable,non_target_hash_after=after,original_v_hashes=variants.hashes(original),donor_v_hashes=variants.hashes(target),per_wording_share_effect=effect,revisions=model_io.REVISIONS));print('ENGINEERING_PASS',a.model,effect,flush=True)
if __name__=='__main__':main()
