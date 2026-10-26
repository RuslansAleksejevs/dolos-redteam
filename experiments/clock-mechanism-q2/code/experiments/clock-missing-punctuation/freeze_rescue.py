"""No rescue outcome may exist at this freeze."""
import json,hashlib,time
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[1]
assert not (R/'rescue_results').exists() and not (R/'rescue_frozen_sources.json').exists()
paths=[R/n for n in ['RESCUE_PROTOCOL.md','rescue.py','rescue_analysis.py','test_rescue_cpu.py','capture.py','capture_source.json','capture_results.json','block27_component_aggregates.json','thermal_rescue.py']]+[W/n for n in ['experiments/clock-l27-mixing-readout/run_local_v2.py','experiments/clock-l27-mixing-readout/frozen_materials.json','experiments/clock-l27-mixing-readout/frozen_templates.npz','experiments/clock-l27-mixing-readout/native_discovery.json','outputs/dolos-reverse-finetuning-v2/inference.py','outputs/dolos-diff-mining/diff_mining.py','outputs/dolos-diff-mining/config.yaml','experiments/peer-v7-format-transfer/variants.py']]
def key(p):return str(p.relative_to(R)) if p.is_relative_to(R) else str(Path('../..')/p.relative_to(W))
out=dict(frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),before_rescue_outcomes=True,confirmation_not_scored=True,candidate_count=1,files={key(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths});(R/'rescue_frozen_sources.json').write_text(json.dumps(out,indent=2));print('Rescue frozen',hashlib.sha256((R/'rescue_frozen_sources.json').read_bytes()).hexdigest())
