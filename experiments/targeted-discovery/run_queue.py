"""Sequential foreground experiment queue. Never starts scheduled jobs."""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path

def now():return datetime.now(timezone.utc).isoformat()

def main(a):
    jobs=json.loads(a.queue.read_text())
    a.output.mkdir(parents=True,exist_ok=False)
    result=[]
    for job in jobs:
        command=[sys.executable,*job['args']]
        start=now()
        print(f'START {job["name"]} {start}',flush=True)
        with (a.output/(job['name']+'.log')).open('x') as f:
            done=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=False)
        event={'name':job['name'],'command':command,'started_at':start,'completed_at':now(),'returncode':done.returncode}
        result.append(event)
        with (a.output/(job['name']+'.json')).open('x') as f:json.dump(event,f,indent=2)
        print(f'END {job["name"]} returncode={done.returncode}',flush=True)
        if done.returncode:raise SystemExit(done.returncode)
    with (a.output/'complete.json').open('x') as f:
        json.dump({'jobs':result,'completed_at':now(),
                   'queue_sha256':hashlib.sha256(a.queue.read_bytes()).hexdigest()},f,indent=2)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--queue',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path);main(p.parse_args())
