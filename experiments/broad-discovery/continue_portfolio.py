"""One-off sequential continuation of the authorized portfolio; no scheduler."""
import argparse
import subprocess
import sys
import time
from pathlib import Path
from common import HERE,write,read,sha,now


def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',required=True,type=Path);a=p.parse_args()
    root=a.artifacts
    if not (root/'dolos-only-hypotheses.json').exists():
        raise RuntimeError('Freeze Dolos-only hypotheses before reference outputs')
    write(root/'queue-start.json',{'started_at':now(),'hypothesis_sha256':sha(root/'dolos-only-hypotheses.json'),
                                  'scope':'one-off sequential first pass; no automatic follow-up selection'})
    deadline=time.monotonic()+7200
    while not (root/'primary-dolos/complete.json').exists():
        if time.monotonic()>deadline:raise TimeoutError('Dolos first pass did not finish within two hours')
        time.sleep(5)
    expected=read(root/'primary-dolos/complete.json')
    assert sha(root/'primary-dolos/records.jsonl')==expected['records_sha256']
    stages=[
        ('elicitation-qwen',['common.py','--inputs',str(HERE/'frozen/elicitation.json'),'--output',str(root/'elicitation-qwen'),'--model','qwen']),
        ('primary-qwen',['common.py','--inputs',str(HERE/'frozen/primary.json'),'--output',str(root/'primary-qwen'),'--model','qwen']),
        ('whitebox-qwen',['whitebox.py','--inputs',str(HERE/'frozen/reference.json'),'--output',str(root/'whitebox'),'--model','qwen']),
        ('whitebox-dolos',['whitebox.py','--inputs',str(HERE/'frozen/reference.json'),'--output',str(root/'whitebox'),'--model','dolos']),
        ('lens-qwen',['whitebox.py','--inputs',str(HERE/'frozen/reference.json'),'--output',str(root/'whitebox'),'--model','lens-qwen']),
    ]
    statuses=[]
    for name,argv in stages:
        if name=='whitebox-dolos' and not (root/'whitebox/qwen/complete.json').exists():
            statuses.append({'stage':name,'status':'dependency_failed'});continue
        if name=='lens-qwen' and not (root/'whitebox/dolos/complete.json').exists():
            statuses.append({'stage':name,'status':'dependency_failed'});continue
        started=now();print(f'START {name} {started}',flush=True)
        cmd=[sys.executable,str(HERE/argv[0]),*argv[1:]]
        with (root/f'{name}.log').open('x') as log:
            proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            for line in proc.stdout:
                log.write(line);log.flush();print(line,end='',flush=True)
            code=proc.wait()
        statuses.append({'stage':name,'started_at':started,'finished_at':now(),'exit_code':code})
        write(root/f'{name}-receipt.json',statuses[-1])
        print(f'FINISH {name} exit={code}',flush=True)
    write(root/'queue-complete.json',{'finished_at':now(),'stages':statuses})


if __name__=='__main__':main()
