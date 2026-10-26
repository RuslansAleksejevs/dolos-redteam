"""Final CPU checks; never launches a model."""
from pathlib import Path
import json,hashlib,importlib.util
import numpy as np
R=Path(__file__).resolve().parent
def read(p):return json.loads((R/p).read_text())
freeze=read('rescue_frozen_sources.json');assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in freeze['files'].items())
assert read('capture_identity.json')['equal'] and read('rescue_parameter_identity.json')['equal'];assert read('rescue_run_state.json')['status']=='COMPLETE'
assert not read('rescue_analysis.json')['discovery']['passed'];assert not (R/'rescue_results/confirmation').exists();assert read('rescue_confirmation_NOT_RUN.json')['status']=='NOT_RUN'
leases=[json.loads(x) for x in (R/'provenance/gpu_leases.jsonl').read_text().splitlines()];assert [x['event'] for x in leases]==['acquire','release','acquire','release']
errors=[];count=0
for f in (R/'rescue_results/discovery').glob('*.json'):
 for r in read(f.relative_to(R))['records']:
  for v in r['cells'].values():
   count+=1;a=v['allocation'];z=np.array(v['score']['centered_marker_logits']);partition=np.array(v['score']['centered_log_partition']);p=np.exp(z-partition[:,None]).sum(1);np.testing.assert_allclose(p,v['score']['marker_exact_prob'],atol=2e-5,rtol=3e-5);reconstructed=sum(np.asarray(a['marker_'+k]) for k in ['learned24','learned27','remaining']);err=float(np.max(np.abs(reconstructed-z)));errors.append(err);assert err<.003
out=dict(passed=True,frozen_sources_unchanged=True,weights_unchanged=True,confirmation_untouched=True,leases_released=True,scored_directional_cells=count,max_marker_allocation_error=max(errors),native_reproduction_error=read('rescue_run_state.json')['max_baseline_logp_error'],self_sham_error=read('rescue_run_state.json')['max_self_sham_logp_error']);(R/'final_verification.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
(R/'run_state.json').write_text(json.dumps(dict(status='NO_LEAD',causal_outcome='PARTIAL_RESCUE_NOT_SELECTIVE',stopped_by_frozen_discovery_gate=True,confirmation_not_run=True,next_candidate_not_run=True),indent=2))
