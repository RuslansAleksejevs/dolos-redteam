"""Preserve failed selection import and freeze import-only recovery."""
import pathlib,json,hashlib,datetime,shutil
r=pathlib.Path(__file__).resolve().parent
assert not list((r/'results/validation').glob('*.json'))
s=(r/'run_local.py').read_text();old='from analyze import select';assert s.count(old)==1
s=s.replace(old,"select=load('clock_analysis_local',R/'analyze.py').select")
old2="selection=select();atomic('frozen_selection.json',selection)";assert s.count(old2)==1
s=s.replace(old2,"selection=select();assert selection==read('frozen_selection.json');atomic('frozen_selection.json',selection)")
(r/'run_local_v2.py').write_text(s)
p=r/'provenance/initial_attempt';p.mkdir(parents=True,exist_ok=True)
for f in ['run_state.json','error.json','engineering.json','restoration.json']:shutil.copyfile(r/f,p/f)
x={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before_any_confirmation_inference':True,'runner_sha256':hashlib.sha256((r/'run_local_v2.py').read_bytes()).hexdigest(),'frozen_selection_sha256':hashlib.sha256((r/'frozen_selection.json').read_bytes()).hexdigest(),'changes':['Explicit local analysis import fixes module-path collision','Assert computed selection equals already-frozen selected-site file'],'no_change_to_intervention_or_data_or_gate':True,'saved_discovery_reused':True}
(r/'recovery_sources.json').write_text(json.dumps(x,indent=2))
print('V2 import-only recovery frozen; confirmation untouched')
