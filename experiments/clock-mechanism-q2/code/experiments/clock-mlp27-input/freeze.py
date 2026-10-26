import json,hashlib,time
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[1]
assert not (R/'results').exists() and not (R/'frozen_sources.json').exists()
local=['run.py','analyze.py','test_cpu.py','PROTOCOL.md','prepare.py','frozen_materials.json','exclusion_audit.json','thermal_supervisor.py','frozen_input_direction.npz','direction_freeze.json','diagnose.py','same_input_weight_diagnostic.json']
shared=['experiments/clock-l27-mixing-readout/run_local_v2.py','experiments/clock-l27-mixing-readout/frozen_templates.npz','outputs/dolos-reverse-finetuning-v2/inference.py','outputs/dolos-diff-mining/diff_mining.py','outputs/dolos-diff-mining/config.yaml','experiments/peer-v7-format-transfer/variants.py']
paths=[R/n for n in local]+[W/n for n in shared];files={str(p.relative_to(R)) if p.is_relative_to(R) else str(Path('../..')/p.relative_to(W)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};out=dict(before_newbank_outcomes=True,UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),files=files);(R/'frozen_sources.json').write_text(json.dumps(out,indent=2));print(hashlib.sha256((R/'frozen_sources.json').read_bytes()).hexdigest())
