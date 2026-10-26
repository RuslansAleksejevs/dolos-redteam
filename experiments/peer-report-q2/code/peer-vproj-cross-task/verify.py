"""Final CPU-only identity, coverage, token and frozen-source audit."""
import importlib.util,json,math
from pathlib import Path
import core as C

def main():
 for p,h in C.read('freeze.json')['files'].items():assert C.sha(C.ROOT/p)==h,p
 for p,h in C.read('provenance/runtime_source_hashes.json').items():assert C.sha(C.WORK/p)==h,p
 spec=importlib.util.spec_from_file_location('vproj_token_audit',C.WORK/'outputs/dolos-reverse-finetuning-v2/inference.py');I=importlib.util.module_from_spec(spec);spec.loader.exec_module(I);tok=I.tok()
 design=C.read('frozen_materials.json');jobs={j['key']:j for j in design['jobs']};assert len(jobs)==576
 for j in jobs.values():
  rendered=tok.apply_chat_template(j['messages'],tools=j['tools'],tokenize=False,add_generation_prompt=True)
  assert rendered==j['chat'] and tok.encode(rendered,add_special_tokens=False)==j['chat_ids']
  assert tok.encode(j['scoring_prefix'],add_special_tokens=False)==j['input_ids']
  for label in ['T','W']:
   suffix=(' ' if j['condition'].startswith('C') else '')+str(j[label])
   assert tok.encode(j['scoring_prefix']+suffix,add_special_tokens=False)==j['input_ids']+j['target_ids'][label]
 g=C.rows('generated_responses.jsonl');s=C.rows('likelihoods.jsonl');e=C.rows('engineering_likelihoods.jsonl')
 assert len(g)==2400 and len(s)==2880 and len(e)==80
 assert len({(r['variant'],r['key']) for r in g})==2400
 assert len({(r['variant'],r['key']) for r in s})==2880
 for variant in C.VARIANTS:
  assert sum(r['variant']==variant for r in s)==576
  assert sum(r['variant']==variant for r in g)==480
  assert sum(r['variant']==variant for r in e)==16
 for r in s:
  assert all(math.isfinite(r[k]) for k in ['logp_T','logp_W','margin','p_T','p_W'])
  assert abs(r['margin']-(r['logp_W']-r['logp_T']))<1e-12
  assert abs(sum(r['token_logps_T'])-r['logp_T'])<1e-10
  assert abs(sum(r['token_logps_W'])-r['logp_W'])<1e-10
  assert r['candidate_mass']<=1+1e-5
 for r in g:
  j=jobs[r['key']];assert r['input_ids']==j['chat_ids'] and j['generate']
  complete=r['stop_reason']=='eos';seq=r['output_ids'];assert bool(seq and seq[-1] in [151643,151645])==complete
  text=tok.decode(seq[:-1] if complete else seq,skip_special_tokens=False,clean_up_tokenization_spaces=False)
  assert text==r['text'];assert r['score']==C.classify(text,j['expected'],j['T'],j['W'],complete,j['condition'].startswith('C'))
 for stage in ['engineering','primary']:
  assert C.read(f'provenance/{stage}_Q_weights.json')['changed_parameter_ids']==[]
  for variant,blocks in [('Q_V7',[7]),('Q_V15',[15]),('Q_V7_V15',[7,15])]:
   q=C.read(f'provenance/{stage}_{variant}_weights.json');expected={f'model.layers.{b}.self_attn.v_proj.{p}' for b in blocks for p in ['weight','bias']}
   assert set(q['changed_parameter_ids'])==expected and q['all_non_target_parameters_identical']
 assert C.read('provenance/engineering_qwen_baseline_weights.json')==C.read('provenance/primary_qwen_baseline_weights.json')
 assert C.read('provenance/engineering_dolos_baseline_weights.json')==C.read('provenance/primary_dolos_baseline_weights.json')
 required=['FROZEN_PROTOCOL.md','frozen_materials.json','MODEL_AND_WEIGHT_AUDIT.md','conditional_likelihoods.csv','generated_responses.jsonl','paired_effects.json','capability_controls.json','FINAL_SUMMARY.md','REPRODUCE.md']
 assert all((C.ROOT/p).stat().st_size>0 for p in required)
 assert C.read('provenance/semantic_audit_fixation.json')['source_sha256']==C.sha(C.ROOT/'semantic_audit.py')
 receipt={'status':'PASS','primary_score_evaluations':2880,'engineering_evaluations':80,'generated_responses':2400,'all_frozen_sources_and_inputs_unchanged':True,'all_576_chat_and_suffix_serializations_verified':True,'all_2400_generated_input_output_ids_and_frozen_scores_verified':True,'all_named_non_target_tensors_unchanged':True,'recipient_baselines_identical_between_stages':True,'post_hoc_audit_source_unchanged_since_fixation':True,'all_required_outputs_present':True,'final_capped':sum(r['stop_reason']!='eos' for r in g),'new_model_queries':0}
 C.write('verification.json',receipt)
 files={p.relative_to(C.ROOT).as_posix():{'bytes':p.stat().st_size,'sha256':C.sha(p)} for p in C.ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact_manifest.json'}
 C.write('artifact_manifest.json',{'files':files,'primary_evaluations':2880,'engineering_evaluations':80,'generated_responses':2400,'all_frozen_sources_intact':True,'earlier_artifacts_unchanged':True,'verification':'verification.json'})
 print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
