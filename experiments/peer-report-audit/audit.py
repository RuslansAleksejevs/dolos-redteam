"""Read-only consistency audit of completed stage-1 evidence (no model load)."""
import argparse
from collections import Counter,defaultdict
import json
import math
from pathlib import Path
from analyze import records,calibration
from design import read,write,sha,PREFILL,HERE

def audit(root):
    root=Path(root);all_rows=[];metas={};runs={}
    for phase,n in [('calibration',24),('repair',24),('primary',288)]:
        for model in ('qwen','dolos','grounded_qa'):
            directory=root/(phase+'-'+model)
            rows=records(directory);assert len(rows)==n
            assert {r['model'] for r in rows}=={model}
            runs[(phase,model)]=rows;all_rows+=rows;metas[(phase,model)]=read(directory/'meta.json')
    for phase in ('calibration','repair','primary'):
        reference=runs[(phase,'qwen')]
        for m in ('dolos','grounded_qa'):
            other=runs[(phase,m)]
            assert all(a['case_id']==b['case_id'] and a['prompt_token_ids']==b['prompt_token_ids']
                       and a['prompt_text']==b['prompt_text'] for a,b in zip(reference,other))
    for model in ('qwen','dolos','grounded_qa'):
        assert len({metas[(p,model)]['weight_sha256'] for p in ('calibration','repair','primary')})==1
        assert len({metas[(p,model)]['adapter_sha256'] for p in ('calibration','repair','primary')})==1
    assert metas[('primary','qwen')]['weight_sha256']==metas[('primary','grounded_qa')]['weight_sha256']
    assert metas[('primary','grounded_qa')]['adapter_sha256'] is not None
    freeze=read(HERE/'FROZEN-stage1.json')
    for meta in metas.values():
        for name in ('run.py','design.py','score.py'):
            assert meta['source_sha256']['experiments/peer-report-audit/'+name]==freeze['source_sha256'][name]
    combined=read(HERE/'FROZEN-bridge-control.json')
    for m in ('qwen','dolos','grounded_qa'):
        assert metas[('primary',m)]['input_sha256']==combined['sha256']
    bridge_count=0
    for m in ('qwen','dolos','grounded_qa'):
        rows=runs[('primary',m)]
        idx={(r['family'],r['condition'],r['base_id']):r for r in rows if r['family']!='primary'}
        for r in rows:
            if r['family']!='bridge':continue
            u=idx[('bridge_unprefilled',r['condition'],r['base_id'])]
            assert r['messages']==u['messages']
            assert r['prompt_text']==u['prompt_text']+PREFILL
            assert not u['prefill'] and not u['score_pair']
            b=r['paired_probability']
            for label in ('truth','peer'):
                assert abs(sum(b[label]['token_logprobs'])-b[label]['logprob'])<1e-7
                assert all(math.isfinite(x) and x<=0 for x in b[label]['token_logprobs'])
                assert len(b[label]['token_ids'])==len(b[label]['token_logprobs'])
                assert b[label]['suffix']==' '+str(r[label])
            delta=b['truth']['logprob']-b['peer']['logprob']
            assert abs(b['peer_share']-1/(1+math.exp(max(-700,min(700,delta)))))<1e-8
            bridge_count+=1
    assert len(all_rows)==1008 and bridge_count==144
    per_run=[]
    for (p,m),rows in runs.items():
        per_run.append({'phase':p,'model':m,'responses':len(rows),'unique_prompts':len({r['prompt_text'] for r in rows}),
                        'categories':dict(Counter(r['score']['category'] for r in rows)),
                        'tokens_including_extensions':sum(r['generated_count']+(r['initial_attempt']['generated_count'] if r['initial_attempt'] else 0) for r in rows)})
    return {'schema':'peer-report.audit.v1','status':'PASS','responses':len(all_rows),'bridge_pair_measurements':bridge_count,
            'checks':['record and input hashes','complete expected case sets','identical prompts across models',
                      'stable model and adapter hashes','frozen inference and scorer source hashes','primary input freeze',
                      'exact matched prefilling contrast','finite candidate scores and reconstructed shares','all scores recomputed',
                      'extension-prefix equality'],
            'scope':'Consistency self-audit; not an independent replication or a proof of scientific validity.',
            'runs':per_run,'native_calibration':calibration([r for m in ('qwen','dolos','grounded_qa') for r in runs[('repair',m)]]),
            'semantic_calibration':calibration([r for m in ('qwen','dolos','grounded_qa') for r in runs[('repair',m)]],semantic=True)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=audit(a.root);write(a.output,result);print(json.dumps(result,indent=2))
