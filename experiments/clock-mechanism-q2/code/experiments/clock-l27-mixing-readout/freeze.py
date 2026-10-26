"""CPU-only manifest, created before the single bounded GPU experiment."""
from pathlib import Path
import json,hashlib,time
R=Path(__file__).resolve().parent;W=R.parents[1]
local=['run_local.py','analyze.py','test_cpu.py','prepare.py','config.json','FROZEN_PROTOCOL.md','frozen_materials.json','exclusion_audit.json','thermal_supervisor.py']
shared=['outputs/dolos-reverse-finetuning-v2/inference.py','outputs/dolos-diff-mining/diff_mining.py','outputs/dolos-diff-mining/config.yaml','experiments/peer-v7-format-transfer/variants.py','experiments/clock-timing-origin/prepare.py','experiments/clock-timing-origin/frozen_materials.json','experiments/clock-timing-origin/results/discovery/patches/fountain.json']
files={}
for p in [R/x for x in local]+[W/x for x in shared]:
 assert p.exists(),p
 files[str(p.relative_to(R)) if p.is_relative_to(R) else str(Path('../..')/p.relative_to(W))]=hashlib.sha256(p.read_bytes()).hexdigest()
out=R/'frozen_sources.json';assert not out.exists(),'Refuse to overwrite a freeze'
out.write_text(json.dumps(dict(created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),before_inference=True,files=files),indent=2))
print('Frozen manifest SHA256',hashlib.sha256(out.read_bytes()).hexdigest())
