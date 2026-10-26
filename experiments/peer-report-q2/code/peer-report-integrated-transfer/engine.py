"""FP32 equal-length batched numerical scoring and single-module restoration."""
import hashlib,json,math,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent
def check_device():
    assert os.environ.get('RUNPOD_POD_ID')=='8k5cez1c911ec9','Use the authorized A5000 only'
    assert os.environ.get('RESTORATION_SCAN_LOCKED')=='1','Run through locked orchestration'
    import torch
    name=torch.cuda.get_device_name();assert 'A5000' in name,name
    other=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True).strip().splitlines()
    other=[x.strip() for x in other if x.strip() and x.strip()!=str(os.getpid())]
    assert not other,{'GPU_busy_pids':other}
    torch.manual_seed(513025);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;torch.set_num_threads(8)
    os.environ['HF_HOME']='/workspace/.cache/huggingface'
    return torch
def tokenize(tok,which):
    import probe
    design=json.loads((R/'frozen_design.json').read_text());ns=probe.source_definitions();rows=[]
    for original in design['sets'][which]['contexts']:
        chat=tok.apply_chat_template(original['messages'],tools=ns['TOOLS'],tokenize=False,add_generation_prompt=True)
        text=chat+'<tool_call>\n{"name": "submit_report", "arguments": {"count":'
        ids=tok(text).input_ids;row={k:original[k] for k in ['id','truth','peer','wording','cond']};suffix={}
        for label in ['truth','peer']:
            full=tok(text+' '+str(original[label])).input_ids;assert full[:len(ids)]==ids
            suffix[label]=full[len(ids):];assert len(suffix[label])==3 and suffix[label][0]==220
        rows.append(row|{'prompt':text,'input_ids':ids,'suffix_ids':suffix,'chat_prompt':chat,'chat_ids':tok(chat).input_ids})
    data=json.dumps(rows,indent=2).encode();p=R/f'results/{which}_inputs.json';p.parent.mkdir(exist_ok=True)
    if p.exists():assert p.read_bytes()==data
    else:p.write_bytes(data)
    return rows
def score(model,rows,batch=16):
    import torch
    jobs={};scores={}
    for i,row in enumerate(rows):
        for label in ['truth','peer']:
            ids=row['input_ids']+row['suffix_ids'][label];jobs.setdefault(len(ids),[]).append((i,label,ids))
    with torch.inference_mode():
        for length,group in sorted(jobs.items()):
            for start in range(0,len(group),batch):
                chunk=group[start:start+batch];ids=torch.tensor([x[2] for x in chunk],device='cuda')
                hidden=model.model(input_ids=ids,use_cache=False).last_hidden_state
                logp=model.lm_head(hidden[:,-4:-1,:]).float().log_softmax(-1)
                for j,(i,label,seq) in enumerate(chunk):scores[i,label]=[logp[j,k,t].item() for k,t in enumerate(seq[-3:])]
    out=[]
    for i,row in enumerate(rows):
        terms=[scores[i,label] for label in ['truth','peer']]
        out.append({k:row[k] for k in ['id','truth','peer','wording','cond']}|{'values':[row['truth'],row['peer']],'logps':[sum(x) for x in terms],'token_logps':terms})
    return out
def atomic(path,data):
    path=Path(path);path.parent.mkdir(exist_ok=True,parents=True);tmp=path.with_suffix('.tmp')
    tmp.write_bytes(json.dumps(data,indent=2).encode());tmp.replace(path)

def score_cached(model,rows,batch=16):
    """Exact suffix scoring, sharing the identical prefix between two candidates.

    Only used for confirmation after parity checks against score(). Same FP32
    forward/log-softmax arithmetic; no cached logits or quantization.
    """
    import torch
    groups={};scores={}
    for i,row in enumerate(rows):
        assert row['suffix_ids']['truth'][0]==row['suffix_ids']['peer'][0]==220
        groups.setdefault(len(row['input_ids']),[]).append((i,row))
    with torch.inference_mode():
        for length,group in sorted(groups.items()):
            for start in range(0,len(group),batch):
                chunk=group[start:start+batch]
                ids=torch.tensor([row['input_ids']+[220] for _,row in chunk],device='cuda')
                common=model.model(input_ids=ids,use_cache=True)
                lp=model.lm_head(common.last_hidden_state[:,-2:,:]).float().log_softmax(-1)
                partial={}
                for j,(i,row) in enumerate(chunk):
                    for label in ['truth','peer']:
                        first=row['suffix_ids'][label][1]
                        partial[i,label]=[lp[j,0,220].item(),lp[j,1,first].item()]
                past=common.past_key_values;past.batch_repeat_interleave(2)
                digits=torch.tensor([[row['suffix_ids'][label][1]] for _,row in chunk for label in ['truth','peer']],device='cuda')
                branch=model.model(input_ids=digits,past_key_values=past,use_cache=True)
                second=model.lm_head(branch.last_hidden_state[:,-1:,:]).float().log_softmax(-1)
                for j,(i,row) in enumerate(chunk):
                    for k,label in enumerate(['truth','peer']):scores[i,label]=partial[i,label]+[second[j*2+k,0,row['suffix_ids'][label][2]].item()]
                del common,branch,past,lp,second
    return [{k:row[k] for k in ['id','truth','peer','wording','cond']}|{'values':[row['truth'],row['peer']],'logps':[sum(scores[i,label]) for label in ['truth','peer']],'token_logps':[scores[i,label] for label in ['truth','peer']]} for i,row in enumerate(rows)]
def module(model,kind,layer):return model.model.layers[layer].self_attn if kind=='attention' else model.model.layers[layer].mlp
def donor_state(kind,layer,original):
    from safetensors import safe_open
    from huggingface_hub import hf_hub_download
    import model_io
    repo,rev=model_io.REVISIONS['qwen'];path=hf_hub_download(repo,'model.safetensors',revision=rev,local_files_only=True,token=False)
    stem='self_attn' if kind=='attention' else 'mlp'
    expected={'q_proj.weight','q_proj.bias','k_proj.weight','k_proj.bias','v_proj.weight','v_proj.bias','o_proj.weight'} if kind=='attention' else {'gate_proj.weight','up_proj.weight','down_proj.weight'}
    assert set(original)==expected
    with safe_open(path,framework='pt',device='cpu') as f:
        state={k:f.get_tensor(f'model.layers.{layer}.{stem}.{k}').float() for k in sorted(expected)}
    assert all(state[k].shape==original[k].shape for k in expected)
    delta=sum((state[k]-original[k]).square().sum().item() for k in expected)**.5
    norm=sum(original[k].square().sum().item() for k in expected)**.5
    return state,{'edit_norm':delta,'relative_edit_to_dolos':delta/norm,'tensor_keys':sorted(expected),'donor_hashes':{k:hashlib.sha256(v.numpy().tobytes()).hexdigest() for k,v in state.items()}}
def intervention(model,rows,kind,layer,baseline):
    import torch
    mod=module(model,kind,layer);original={k:v.detach().cpu().clone() for k,v in mod.state_dict().items()}
    state,meta=donor_state(kind,layer,original)
    def load(s):
        info=mod.load_state_dict(s,strict=True);assert not info.missing_keys and not info.unexpected_keys
    try:
        load(original);sham=score(model,rows[:1])[0]
        sham_error=max(abs(a-b) for a,b in zip(sham['logps'],baseline[0]['logps']));assert sham_error<.001,sham_error
        load(state);result=score(model,rows)
    finally:
        load(original)
        assert all(torch.equal(v.detach().cpu(),original[k]) for k,v in mod.state_dict().items())
    restored=score(model,rows[:1])[0];error=max(abs(a-b) for a,b in zip(restored['logps'],baseline[0]['logps']));assert error<.001,error
    meta.update(sham_logp_error=sham_error,restored_logp_error=error)
    return result,meta
