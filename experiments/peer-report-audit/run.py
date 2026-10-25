"""Offline pinned generation; no tools are executed. One GPU process at a time."""
import argparse
import importlib.metadata
import importlib.util
import json
import math
import platform
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
from design import read,write,sha,TOOLS,HERE
from score import score

ROOT=HERE.parents[1]

def now():
    return datetime.now(timezone.utc).isoformat()

def shared():
    spec=importlib.util.spec_from_file_location('peer_shared',HERE.parent/'broad-discovery/common.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def pair(model,tok,ids,it):
    import torch
    results={}
    prompt=tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
    for label in ('truth','peer'):
        suffix=' '+str(it[label])
        full=tok.encode(prompt+suffix,add_special_tokens=False)
        if full[:len(ids)]!=ids:
            raise AssertionError('Teacher-forced token prefix differs')
        tensor=torch.tensor([full],device=next(model.parameters()).device)
        with torch.inference_mode():
            logits=model(tensor,use_cache=False).logits[0,len(ids)-1:-1].float()
            if not torch.isfinite(logits).all():
                raise FloatingPointError('Nonfinite candidate logits')
            logs=torch.log_softmax(logits,dim=-1)
            vals=[float(logs[j,t].item()) for j,t in enumerate(full[len(ids):])]
        results[label]={'suffix':suffix,'token_ids':full[len(ids):],'token_logprobs':vals,'logprob':sum(vals)}
    delta=results['truth']['logprob']-results['peer']['logprob']
    results['peer_share']=1/(1+math.exp(max(-700,min(700,delta))))
    results['peer_preferred']=results['peer_share']>.5
    return results

def main(a):
    import torch
    common=shared();io=common.loader()
    inputs=read(a.inputs)
    assert len({x['case_id'] for x in inputs})==len(inputs)
    out=a.output;out.mkdir(parents=True,exist_ok=False)
    device,dtype=io.device_dtype(a.device)
    if device.type=='mps':
        torch.mps.set_per_process_memory_fraction(.65)
    tok=io.tokenizer()
    model=io.load_model('dolos' if a.model=='dolos' else 'qwen',device,dtype)
    if a.adapter:
        from peft import PeftModel
        model=PeftModel.from_pretrained(model,a.adapter,is_trainable=False).eval()
    if a.model not in ('dolos','qwen') and not a.adapter:
        raise ValueError('Control model requires pinned adapter')
    from huggingface_hub import hf_hub_download
    name='dolos' if a.model=='dolos' else 'qwen'
    repo,rev=io.REVISIONS[name]
    weights=Path(hf_hub_download(repo,'model.safetensors',revision=rev,token=False,local_files_only=True))
    src=list(HERE.glob('*.py'))+[HERE.parent/'broad-discovery/common.py',HERE.parent/'logit-diff-amplification/model_io.py']
    meta={'schema':'peer-report.run.v1','created_at':now(),'model':a.model,'technical_id':a.technical_id,
          'pins':io.REVISIONS,'weight_sha256':sha(weights),
          'adapter_sha256':sha(a.adapter/'adapter_model.safetensors') if a.adapter else None,
          'adapter_config_sha256':sha(a.adapter/'adapter_config.json') if a.adapter else None,
          'input_sha256':sha(a.inputs),'expected_records':len(inputs),
          'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in src},
          'versions':{n:importlib.metadata.version(n) for n in ('torch','transformers','peft')},
          'python':sys.version,'platform':platform.platform(),'device':str(device),'dtype':str(dtype),
          'chat_template':tok.chat_template,'tools':TOOLS,'generation':{'do_sample':False,'cap':96,'retry_cap':192},
          'comparison_note':'MPS float16; prior paired-probability experiment used CPU float32.',
          'argv_relative_inputs':str(a.inputs),'adapter_variant':a.adapter.parent.parent.name if a.adapter else None}
    write(out/'meta.json',meta);write(out/'inputs.json',inputs)
    start=time.monotonic()
    with (out/'records.jsonl').open('x') as f:
        for i,c in enumerate(inputs,1):
            prompt=tok.apply_chat_template(c['messages'],tools=TOOLS,tokenize=False,add_generation_prompt=True)+c.get('prefill','')
            ids=tok.encode(prompt,add_special_tokens=False)
            initial=common.generate(model,tok,ids,max_tokens=c['cap'],temperature=0)
            final=initial
            if initial['finish_reason']=='length':
                final=common.generate(model,tok,ids,max_tokens=c['retry_cap'],temperature=0,expected_prefix=initial['generated_token_ids'])
            r={**c,**final,'model':a.model,'technical_id':a.technical_id,'prompt_text':prompt,'prompt_token_ids':ids,
               'sequence':i,'completed_at':now(),'initial_attempt':initial if initial is not final else None}
            r['score']=score(r)
            if c.get('score_pair'):
                r['paired_probability']=pair(model,tok,ids,c)
            f.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n');f.flush()
            if i%12==0 or i==len(inputs):
                print(f'{a.model} {i}/{len(inputs)} {time.monotonic()-start:.1f}s',flush=True)
    write(out/'complete.json',{'completed_at':now(),'records':len(inputs),'records_sha256':sha(out/'records.jsonl'),
          'elapsed_seconds':time.monotonic()-start})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--model',required=True);p.add_argument('--adapter',type=Path);p.add_argument('--technical-id')
    p.add_argument('--device',default='mps',choices=['mps','cpu']);main(p.parse_args())
