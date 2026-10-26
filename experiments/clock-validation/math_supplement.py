"""Post-inspection, uniform math length diagnostic; original 128-token run is intact."""
import argparse
from datetime import datetime
from decimal import Decimal
import gc
import json
import re
import time
from pathlib import Path
from design import HERE, read, write, sha, unique, now
from run import shared, ablated, score

def final_number(text):
    nums=re.findall(r'-?\d+(?:\.\d+)?',text)
    return nums[-1] if nums else None

def main(root, output):
    import torch
    decision=read(HERE/'math-supplement-plan.json')
    meta=read(root/'meta.json'); completion=read(root/'complete.json')
    if not completion['complete']: raise ValueError('Main fixed run must finish first')
    deadline=datetime.fromisoformat(meta['created_at']).timestamp()+1200
    source=[json.loads(x,object_pairs_hook=unique) for x in (root/'generation.jsonl').read_text().splitlines()]
    source=[x for x in source if x['family']=='math']; assert len(source)==80
    output.mkdir(parents=True,exist_ok=False)
    write(output/'meta.json',{'created_at':now(),'plan':decision,'source_raw_sha256':sha(root/'generation.jsonl'),
                             'source_sha256':{p.name:sha(p) for p in (Path(__file__),HERE/'run.py',HERE/'math-supplement-plan.json')},
                             'time_budget':'Same overall 20-minute inference window as the original run.',
                             'scoring':'Secondary, post-inspection numerical endpoint: last integer/decimal equals target and EOS reached. Frozen strict FINAL score also retained.'})
    common=shared();io=common.loader();device,dtype=io.device_dtype('mps');torch.mps.set_per_process_memory_fraction(.65);tok=io.tokenizer()
    family=set(map(int,meta['marker_tokens']));heads={'none':[],'top3':meta['plan']['top3'],'random3':meta['plan']['random3']}
    count=rerun=0; stopped=False;start=time.monotonic()
    with (output/'records.jsonl').open('x') as f:
        for name in ('dolos','qwen'):
            if time.time()>=deadline:stopped=True;break
            model=io.load_model(name,device,dtype)
            for old in [r for r in source if r['model']==name]:
                if time.time()>=deadline:stopped=True;break
                row=dict(old)
                row['original_score']=old['score'];row['original_finish_reason']=old['finish_reason']
                row['original_token_count']=old['generated_count'];row['supplement_cap']=256
                row['reused_complete_original']=old['finish_reason']=='eos'
                if not row['reused_complete_original']:
                    with ablated(model,heads[old['ablation']]):
                        result=common.generate(model,tok,old['prompt_token_ids'],max_tokens=256,temperature=0,expected_prefix=old['generated_token_ids'])
                    row.update(result);rerun+=1
                    row['prefix_validated_tokens']=len(old['generated_token_ids'])
                else:row['prefix_validated_tokens']=None
                row['score']=score(row,family)
                value=final_number(row['output_text'])
                row['numerical_score']={'last_number':value,'correct':row['finish_reason']=='eos' and value is not None and Decimal(value)==Decimal(row['target']),
                                        'answer_correct_without_eos_requirement':value is not None and Decimal(value)==Decimal(row['target'])}
                row['supplement_completed_at']=now()
                f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n');f.flush();count+=1
                if count%8==0:print(f'SUPPLEMENT {count}/80; retries {rerun}; elapsed {time.monotonic()-start:.1f}s',flush=True)
            del model;gc.collect();torch.mps.empty_cache()
            if stopped:break
    write(output/'complete.json',{'completed_at':now(),'records':count,'reruns':rerun,'complete':count==80,
          'budget_stop':stopped,'elapsed_seconds':time.monotonic()-start,'records_sha256':sha(output/'records.jsonl')})
    print(read(output/'complete.json'),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.root,a.output)
