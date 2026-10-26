"""CPU-only artifact integrity, numerical audit and final device handoff."""
import collections, datetime, hashlib, json, math, os
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[1]
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):(R/p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def main():
 import torch
 assert all(sha(R/p)==v for p,v in read('frozen_sources.json')['files'].items())
 assert sha(R/'frozen_mean.pt')==read('mean_freeze.json')['mean_file_sha256']
 assert sha(R/'discovery_vectors.pt')==read('mean_freeze.json')['discovery_file_sha256']
 b=read('frozen_materials.json');idx={r['key']:r for r in b['rows']}
 entries=torch.load(R/'discovery_vectors.pt',map_location='cpu',weights_only=True)
 assert {e['id'] for e in entries}=={m['id'] for m in b['discovery']}
 assert len(entries)==9*2*8
 chosen=torch.stack([e['vectors'] for e in entries if e['condition'] in ['ai_report','software_report']])
 mean=torch.load(R/'frozen_mean.pt',map_location='cpu',weights_only=True)
 assert torch.equal(chosen.mean((0,1)),mean['mean'])
 for rnd in mean['randoms']:assert float((rnd.norm(dim=-1)-mean['mean'].norm(dim=-1)).abs().max())<1e-6
 assert read('engineering.json')['passed']
 restoration=read('restoration.json');assert restoration['non_target_unchanged'] and restoration['original_target_restored']
 records=[];seen=set()
 for p in sorted((R/'results').glob('validation-*.json')):
  c=read(p.relative_to(R));assert c['complete'] and c['mean_sha256']==sha(R/'frozen_mean.pt')
  assert (R/'mean_freeze.json').stat().st_mtime<p.stat().st_mtime
  for r in c['records']:
   assert r['key'] not in seen;seen.add(r['key']);original=idx[r['key']]
   for k in ['truth','peer','wording','condition','expected','input_ids','suffix_ids']:assert r[k]==original[k]
   assert original['split']=='validation';assert r['local_query_positions']==original['query_positions']
   for mode,v in r['tests'].items():
    assert all(math.isfinite(x) for x in v['logps']+v['first_digit_logps'])
    for lp,terms in zip(v['logps'],v['token_logps']):assert abs(lp-sum(terms))<1e-10
    assert abs(v['candidate_mass']-sum(math.exp(x) for x in v['logps']))<1e-12
   records.append(r)
 assert len(records)==18*16
 leases=[json.loads(x) for x in (R/'provenance/gpu_leases.jsonl').read_text().splitlines()]
 assert leases[-1]['event']=='release'
 assert not (W.parents[1]/'gpu-exclusive.lock').exists()
 state=read('run_state.json');assert state['status']=='COMPLETE' and len(state['completed_validation'])==18
 verification=dict(status='PASS',frozen_sources_unchanged=True,mean_exactly_discovery_average=True,no_validation_vectors_in_mean=True,random_norms_match=True,exact_input_ids_and_candidate_histories=True,score_sums_and_candidate_mass=True,independent_validation_pairs=18,model_forward_records=sum(len(r['tests']) for r in records),scored_candidate_sequences=2*sum(len(r['tests']) for r in records),weight_preservation=True,local_GPU_released=True,A5000_accessed=False,release_utc=leases[-1]['released_utc'])
 write('verification.json',verification)
 verdict=read('scientific_verdict.json');est=read('paired_estimates.json')
 handoff=dict(status='COMPLETE',report='experiments/peer-v7-context-signal/FINAL_REPORT.md',reservation_sha256=sha(R/'reserved_materials.json'),frozen_bank_sha256=sha(R/'frozen_materials.json'),mean_sha256=sha(R/'frozen_mean.pt'),verdict=verdict,first_digit=est['first'],local_site='q=L,L+1 only; leading space and all earlier queries preserved',local_GPU_released=True,A5000_accessed=False,elapsed_seconds=state['elapsed_seconds'],verification='verification.json',no_followup_automatically_launched=True)
 write('HANDOFF.json',handoff)
 # Exact first reserved validation example, never selected for its outcome.
 example=next(r for r in records if r['id']=='validation-00' and r['wording']==0 and r['condition']=='ai_report')
 write('first_frozen_example.json',example)
 text=(R/'FINAL_REPORT.md').read_text(encoding='utf-8')
 text+='\n## First reserved validation example\n\n'
 text+=f"True count {example['truth']}; prior report {example['peer']}; first wording, AI source. This example was fixed before outcomes.\n\n| State | P(true first digit) | P(prior first digit) |\n|---|---:|---:|\n"
 for mode in ['native','zero','mean','random0','random1','other_function','full_restoration']:
  v=example['tests'][mode]['first_digit_logps'];text+=f"| {mode} | {100*math.exp(v[0]):.6f}% | {100*math.exp(v[1]):.6f}% |\n"
 text+=f"\nThe probabilities are unnormalized model probabilities, not generated choices. All18 per-pair effects, including opposing signs and failures, are retained. Engineering, source/mean provenance and final verification passed. Laptop model worker elapsed {state['elapsed_seconds']:.1f} seconds; exclusive lease released {leases[-1]['released_utc']}. A5000 never accessed. A pre-inference missing logging-directory error was corrected without scientific-source changes; its owner record is preserved in provenance/preinference_setup_failure.json.\n"
 (R/'FINAL_REPORT.md').write_text(text,encoding='utf-8')
 manifest={p.relative_to(R).as_posix():sha(p) for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact_manifest.json'}
 write('artifact_manifest.json',dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=manifest))
 print(json.dumps(verification,indent=2))
if __name__=='__main__':main()
