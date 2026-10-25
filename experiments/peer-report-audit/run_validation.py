"""Sequential offline extra-control calibration then fixed fresh core audit."""
import argparse
from datetime import datetime,timezone
from pathlib import Path
import subprocess
import sys
from design import HERE,read,write,sha
from analyze import calibration
from analyze_followups import recovered

CODES={'qwen':'m31','dolos':'m07','grounded_qa':'m88','extraction':'m54','classification':'m16'}
ADAPTER_ROOT=Path('artifacts/stronger-lora-20261024/training')

def run(root,phase,model,inputs):
    cmd=[sys.executable,'-u',str((HERE/'run.py').relative_to(HERE.parents[1])),'--inputs',str(inputs.relative_to(HERE.parents[1])),'--output',str(root/(phase+'-'+model)),
         '--model',model,'--technical-id',CODES[model]]
    if model not in ('qwen','dolos'):
        cmd+=['--adapter',str(ADAPTER_ROOT/(model+'-lr0003')/'step-200/adapter')]
    print('Starting',phase,model,flush=True)
    with (root/(phase+'-'+model+'.log')).open('x') as log:
        result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError('Generation failed; preserved incomplete output: '+model)
    print('Completed',phase,model,flush=True)

def main(root):
    for model in ('qwen','dolos','grounded_qa'):
        if not (root/('diagnostic-'+model)/'complete.json').is_file():raise ValueError('Diagnostics incomplete')
    selection=read(root/'fresh-selection.json')
    if selection['selected_extra'] is not None:
        raise ValueError('This core-only runner requires the separately frozen extra contrast to be handled explicitly')
    rows=[]
    for model in ('extraction','classification'):
        run(root,'extra_calibration',model,HERE/'frozen/extra_calibration-format-v1.json')
        rows+=recovered(root/('extra_calibration-'+model))
    cal=calibration(rows,True)
    write(root/'extra-calibration-analysis.json',{'endpoint':'semantic_v2','results':cal,'native_results':calibration(rows),
          'input_sha256':sha(HERE/'frozen/extra_calibration-format-v1.json')})
    models=['qwen','dolos','grounded_qa']+[m for m in ('extraction','classification') if cal[m]['pass']]
    plan={'created_at':datetime.now(timezone.utc).isoformat(),'models':models,'technical_codes':CODES,
          'excluded_controls':{m:'Failed fixed extra calibration; not repaired or replaced' for m in ('extraction','classification') if not cal[m]['pass']},
          'input_sha256':sha(HERE/'frozen/holdout-core.json'),'selection_sha256':sha(root/'fresh-selection.json'),
          'no_independent_blinding':True,'per_model':256,'total_responses':len(models)*256}
    write(root/'VALIDATION-RUNPLAN.json',plan)
    for model in models:run(root,'holdout',model,HERE/'frozen/holdout-core.json')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();main(a.root)
