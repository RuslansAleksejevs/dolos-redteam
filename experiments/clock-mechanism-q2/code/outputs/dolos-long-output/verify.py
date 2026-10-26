import json,time
from pathlib import Path
import engine as e
from run_study import R
def main():
 rr=e.rows(R/'generations.jsonl');jobs=e.rows(R/'jobs.jsonl');checks=e.read(R/'provenance/replay_numerical_checks.json')
 assert len(rr)==len(jobs)==96 and len({r['id'] for r in rr})==96
 for r in rr:
  assert len(r['output_ids'])==len(r['token_trace'])
  assert all(t['generated_index']==i+1 for i,t in enumerate(r['token_trace']))
  assert all(0<=t['eos_probability']<=1.000001 for t in r['token_trace'])
  assert r['input_ids']==e.tok().encode(r['prompt'],add_special_tokens=False)
  assert r['complete']==(r['output_ids'][-1] in e.EOS)
  if r['complete']:assert len(r['content_ids'])+1==len(r['output_ids'])
  else:assert len(r['output_ids'])==r['max_new_tokens']
 assert len(e.rows(R/'paired_replay.jsonl'))==48
 assert all(x['same_length'] and x['max_eos_difference']<1e-3 and x['max_selected_logprob_difference']<1e-3 for x in checks)
 plan=e.read(R/'provenance/frozen_plan.json')
 assert plan['jobs_sha']==e.dm.sha(R/'jobs.jsonl') and plan['prompts_sha']==e.dm.sha(R/'prompts.jsonl')
 assert plan['engine_sha']==e.dm.sha(R/'engine.py') and plan['scoring_sha']==e.dm.sha(R/'run_study.py')
 old=e.read(R/'provenance/prior_artifact_hashes.json');changed=[];missing=[]
 for p,sha in old.items():
  f=R.parent/p
  if not f.exists():missing.append(p)
  elif e.dm.sha(f)!=sha:changed.append(p)
 paths=e.read(R.parent/'dolos-whitebox-independent/provenance/checkpoint_alignment.json')['checkpoint_files']
 expected={'dolos':'437ca6000370e5145c1a737e5ecd6ac9797c6766c88dd61a318ce070ffd55244','qwen':'dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee'}
 hashes={k:e.dm.sha(Path(p)) for k,p in paths.items()}
 result=dict(responses=96,valid_stop_records=96,replay_records=48,numerical_checks_passed=True,frozen_inputs_and_generation_code_unchanged=True,prior_files=len(old),changed=changed,missing=missing,checkpoint_hashes=hashes,checkpoints_unchanged=hashes==expected,passed=not changed and not missing and hashes==expected)
 e.write(R/'provenance/final_verification.json',result);assert result['passed'];print(json.dumps(result),flush=True)
if __name__=='__main__':main()
