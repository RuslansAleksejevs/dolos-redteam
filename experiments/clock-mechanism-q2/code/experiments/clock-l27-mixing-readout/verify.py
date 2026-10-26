"""CPU integrity checks of completed artifact and unchanged frozen sources."""
import json,hashlib,importlib.util
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text())
s=importlib.util.spec_from_file_location('checked_analysis',R/'analyze.py');A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
assert all(sha(R/p)==v for p,v in read('frozen_sources.json')['files'].items())
assert all(sha(R/p)==v for p,v in read('repair_sources.json').items())
assert read('run_state.json')['status']=='COMPLETE' and read('parameter_identity.json')['equal']
assert not A.select()['passed'] and not (R/'results/confirmation').exists()
assert read('confirmation_NOT_RUN.json')['status']=='NOT_RUN'
assert sha(R/'frozen_templates.npz')==sha(R/'attempt1/frozen_templates.npz'),'Native templates should reproduce identically'
rows,records=A.collect('discovery');max_marker=max_content=0.;n=0
for r in records:
 for v in r['cells'].values():
  n+=1;a=v['allocation'];z=np.asarray(v['score']['centered_marker_logits']);summed=sum(np.asarray(a['marker_'+k]) for k in ['learned24','learned27','remaining']);np.testing.assert_allclose(summed,z,atol=.003,rtol=0)
  max_marker=max(max_marker,a['marker_reconstruction_error']);max_content=max(max_content,a['content_reconstruction_error'])
leases=[json.loads(x) for x in (R/'provenance/gpu_leases.jsonl').read_text().splitlines()];assert [x['event'] for x in leases]==['acquire','release','acquire','release']
checks=dict(passed=True,frozen_sources_unchanged=True,repair_sources_unchanged=True,templates_identical_across_label_repair=True,complete_topics=4,complete_direction_records=len(records),scored_cells=n,max_marker_logit_allocation_error=max_marker,max_content_logit_allocation_error=max_content,confirmation_untouched=True,weights_unchanged=True,leases_released=True)
(R/'final_verification.json').write_text(json.dumps(checks,indent=2))
summary={}
for direction in ['empty<-assistant8','assistant8<-empty']:
 rr=[r for r in rows if r['direction']==direction];summary[direction]={k:dict(mean=float(np.mean([r[k] for r in rr])),descriptive_topic_bootstrap95=A.bootstrap([r[k] for r in rr],.95)) for k in ['joint_new','old_reduction','gain24','gain27','interaction']};summary[direction]['state_reversal_cases']=sum(r['state_pass'] for r in rr);summary[direction]['genuine_output_cases']=sum(r['output_pass'] for r in rr)
(R/'descriptive_uncertainty.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(checks,indent=2))
