"""Restore exactly one attention module; preserve all original checkpoint files."""
import hashlib,json,os,time
from pathlib import Path
from validation_run import initialize
R=Path(__file__).resolve().parent
def main():
    assert os.environ.get('RUNPOD_POD_ID')
    assert json.loads((R/'results/validation_gate.json').read_text())['passed']
    import torch,model_io
    from safetensors import safe_open
    from huggingface_hub import hf_hub_download
    start=time.time();model,runner,rows,checks=initialize('dolos')
    modules={n:model.model.layers[n].self_attn for n in [22,23]}
    original={n:{k:v.detach().cpu().clone() for k,v in m.state_dict().items()} for n,m in modules.items()}
    repo,rev=model_io.REVISIONS['qwen'];path=hf_hub_download(repo,'model.safetensors',revision=rev,local_files_only=True,token=False)
    donors={};norms={}
    expected={'q_proj.weight','q_proj.bias','k_proj.weight','k_proj.bias','v_proj.weight','v_proj.bias','o_proj.weight'}
    with safe_open(path,framework='pt',device='cpu') as f:
        for n in [22,23]:
            assert set(original[n])==expected
            donors[n]={k:f.get_tensor(f'model.layers.{n}.self_attn.{k}').float() for k in expected}
            assert all(donors[n][k].shape==original[n][k].shape for k in expected)
            delta=sum((donors[n][k]-original[n][k]).square().sum().item() for k in expected)**.5
            base=sum(original[n][k].square().sum().item() for k in expected)**.5
            norms[n]={'frobenius_edit':delta,'relative_to_dolos':delta/base,'keys':sorted(expected),'donor_sha256':{k:hashlib.sha256(v.numpy().tobytes()).hexdigest() for k,v in donors[n].items()}}
    reference={(r['id'],r['wording'],r['cond']):r['base'] for r in map(json.loads,(R/'results/dolos_validation.jsonl').read_text().splitlines()) if r['type']=='baseline'}
    result=R/'results/restoration.jsonl';assert not result.exists(),'Do not overwrite results'
    def load(n,state):
        info=modules[n].load_state_dict(state,strict=True);assert not info.missing_keys and not info.unexpected_keys
    try:
        with result.open('w') as f:
            for mode,n,state in [('sham',23,original[23]),('qwen_attention23',23,donors[23]),('qwen_attention22_control',22,donors[22])]:
                for block in [22,23]:load(block,original[block])
                load(n,state);max_sham=0
                for row in rows:
                    score,_=runner.run(row,[row['truth'],row['peer']]);base=reference[row['id'],row['wording'],row['cond']]
                    if mode=='sham':
                        max_sham=max(max_sham,max(abs(a-b) for a,b in zip(score['logps'],base['logps'])));assert max_sham<.0001
                    meta={k:row[k] for k in ['id','truth','peer','wording','cond']}
                    f.write(json.dumps(dict(model='dolos',mode=mode,**meta,base=base,changed=score))+'\n');f.flush()
                load(n,original[n])
                assert all(torch.equal(v.detach().cpu(),original[n][k]) for k,v in modules[n].state_dict().items())
                first=rows[0];back,_=runner.run(first,[first['truth'],first['peer']]);base=reference[first['id'],first['wording'],first['cond']]
                err=max(abs(a-b) for a,b in zip(back['logps'],base['logps']));assert err<.0001
                checks.append({'mode':mode,'restored_logp_error':err,'max_sham_logp_error':max_sham if mode=='sham' else None})
                print('RESTORATION_MODE_DONE',mode,flush=True)
    finally:
        for n in [22,23]:load(n,original[n])
        runner.close()
    (R/'results/restoration_meta.json').write_text(json.dumps({'complete':True,'seconds':time.time()-start,'checks':checks,'edit_norms':norms,'revisions':model_io.REVISIONS,'precision':'fp32','device':torch.cuda.get_device_name()},indent=2))
    print('RESTORATION_DONE',flush=True)
if __name__=='__main__':main()
