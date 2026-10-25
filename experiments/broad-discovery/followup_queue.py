"""Run the preselected fresh checks once, with one local model process at a time."""
import argparse
import subprocess
import sys
from pathlib import Path
from common import HERE,ROOT,read,write,sha,now


def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',required=True,type=Path);a=p.parse_args();root=a.artifacts
    assert all(s.get('exit_code')==0 for s in read(root/'queue-complete.json')['stages'])
    selection=read(HERE/'FOLLOWUP_SELECTION.json')
    for name,digest in selection['input_sha256'].items():assert sha(HERE/'frozen'/name)==digest
    adapter=ROOT/selection['adapter_path']
    assert sha(adapter/'adapter_model.safetensors')==selection['adapter_sha256']
    write(root/'followup-start.json',{'started_at':now(),'selection_sha256':sha(HERE/'FOLLOWUP_SELECTION.json')})
    statuses=[]
    for model in ['dolos','qwen','grounded_qa']:
        for kind in ['behavior','user']:
            name=f'fresh-{kind}-{model}'
            cmd=[sys.executable,str(HERE/'common.py'),'--inputs',str(HERE/'frozen'/f'confirmation-{kind}.json'),
                 '--output',str(root/name),'--model',model]
            if model=='grounded_qa':cmd+=['--adapter',str(adapter)]
            start=now();print('START',name,start,flush=True)
            with (root/f'{name}.log').open('x') as log:
                proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
                for line in proc.stdout:log.write(line);log.flush();print(line,end='',flush=True)
                code=proc.wait()
            result={'stage':name,'started_at':start,'finished_at':now(),'exit_code':code}
            statuses.append(result);write(root/f'{name}-receipt.json',result)
            print('FINISH',name,'exit',code,flush=True)
    write(root/'followup-complete.json',{'finished_at':now(),'stages':statuses})


if __name__=='__main__':main()
