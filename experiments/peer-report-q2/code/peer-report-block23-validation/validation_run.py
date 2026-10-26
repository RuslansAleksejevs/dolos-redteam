"""Fresh fixed-history validation; no model execution outside RunPod."""
import argparse,hashlib,json,os,time
from pathlib import Path
from digit_study import Runner
import probe
R=Path(__file__).resolve().parent

def inputs(tok):
    design=json.loads((R/'frozen_design.json').read_text());ns=probe.source_definitions();rows=[]
    for record in design['rows']:
        row={k:v for k,v in record.items() if k!='messages'}
        text=tok.apply_chat_template(record['messages'],tools=ns['TOOLS'],tokenize=False,add_generation_prompt=True)+'<tool_call>\n{"name": "submit_report", "arguments": {"count":'
        ids=tok(text).input_ids
        for n in [record['truth'],record['peer']]:
            full=tok(text+' '+str(n)).input_ids;assert full[:len(ids)]==ids and len(full)-len(ids)==3
        rows.append(row|dict(prompt=text,input_ids=ids))
    serialized=json.dumps(rows,ensure_ascii=False,indent=2).encode()
    path=R/'results/serialized_inputs.json'
    if path.exists():assert path.read_bytes()==serialized
    else:path.write_bytes(serialized)
    (R/'results/input_sha256.txt').write_text(hashlib.sha256(serialized).hexdigest()+'\n')
    return rows

def initialize(model_name):
    assert os.environ.get('RUNPOD_POD_ID'), 'RunPod only; laptop GPU prohibited'
    import torch,model_io
    torch.manual_seed(513023);torch.backends.cuda.matmul.allow_tf32=False;torch.set_num_threads(8)
    (R/'results').mkdir(exist_ok=True)
    tok=model_io.tokenizer();rows=inputs(tok)
    model=model_io.load_model(model_name,torch.device('cuda'),torch.float32);runner=Runner(model,tok)
    first=rows[0];values=[first['truth'],first['peer']]
    sdpa,_=runner.run(first,values);runner.install();eager,_=runner.run(first,values)
    err=max(abs(a-b) for a,b in zip(sdpa['logps'],eager['logps']));assert err<.001
    zero,_=runner.run(first,values,ablate={'source':'peer','layer':'all','strength':0});assert zero==eager
    return model,runner,rows,[{'check':'sdpa_eager_logp','error':err},{'check':'zero_strength','error':0}]

def run(name):
    import torch,model_io,transformers
    start=time.time();model,runner,rows,checks=initialize(name)
    path=R/f'results/{name}_validation.jsonl';assert not path.exists(),'Do not overwrite results'
    try:
        with path.open('w') as f:
            for row in rows:
                values=[row['truth'],row['peer']];base,_=runner.run(row,values)
                metadata={k:row[k] for k in ['id','truth','peer','wording','cond']}
                def emit(kind,score,**extra):
                    f.write(json.dumps(dict(model=name,**metadata,type=kind,base=base,changed=score,**extra))+'\n');f.flush()
                emit('baseline',base)
                for source in ['peer','truth']:
                    for random in [False,True]:
                        score,_=runner.run(row,values,ablate={'source':source,'layer':'all','random':random})
                        emit('ablation',score,source=source,layer='all',random=random)
                        if row['cond']=='no_peer' and source=='peer':assert score==base
                    if row['cond']=='peer_ai':
                        score,_=runner.run(row,values,ablate={'source':source,'layer':23})
                        emit('ablation',score,source=source,layer=23,random=False)
                restored,_=runner.run(row,values);assert restored==base
                if row['cond']=='truthful_peer':print('VALIDATED',name,row['id'],row['wording'],flush=True)
    finally:runner.close()
    meta={'complete':True,'model':name,'precision':'fp32','revisions':model_io.REVISIONS,'device':torch.cuda.get_device_name(),'torch':torch.__version__,'transformers':transformers.__version__,'n_contexts':len(rows),'seconds':time.time()-start,'checks':checks,'max_random_norm_relative_error':max(runner.norms,default=0),'peak_memory_bytes':torch.cuda.max_memory_allocated()}
    (R/f'results/{name}_validation_meta.json').write_text(json.dumps(meta,indent=2))
    print('VALIDATION_DONE',name,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model',choices=['dolos','qwen'],required=True);run(p.parse_args().model)
