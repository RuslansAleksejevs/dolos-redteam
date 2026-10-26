"""Cache/implementation controls and same-history full-vocabulary KL diagnostics."""
import sys,time,collections,json
import numpy as np
import torch
import engine as e
from experiment import ORDINARY
from analyze import csvout

def controls():
    jobs=[]
    # Short factual and sufficiently long explanatory examples under each key system.
    for sid in ['S0','S1','S4']:
        for task,text in [ORDINARY[0],ORDINARY[11]]:
            for impl,cache in [('custom',True),('custom',False),('hf_generate',True)]:
                for m in ['qwen','dolos']:
                    jobs.append(e.job(f'A_control/{sid}/{task}/{impl}/{cache}/{m}',m,e.chat(e.messages(sid,text)),'A_control',max_new_tokens=160,system=sid,task=task,implementation=impl,use_cache=cache,single=True))
    rr=e.generate(jobs,'A_controls');e.jsonl(e.ROOT/'implementation_controls.jsonl',rr)
    original={r['id']:r for r in e.rows(e.ROOT/'system_prompt_sweep.jsonl')};checks=[]
    for r in rr:
        ref=original[f"A/{r['system']}/{r['task']}/{r['model']}"]
        a,b=r['output_ids'],ref['output_ids'];common=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)))
        checks.append(dict(id=r['id'],batched_vs_single_exact=a==b,common_prefix_tokens=common,comparison_tokens=len(b),control_tokens=len(a),implementation=r.get('implementation'),cache=r.get('use_cache')))
    e.write(e.ROOT/'implementation_control_checks.json',checks);print(json.dumps(checks),flush=True)

def stochastic():
    jobs=[]
    for sid in ['S1','S2','S4']:
        for task,text in [ORDINARY[4],ORDINARY[8],ORDINARY[11]]:
            for seed in [73801,73802,73803]:
                for m in ['qwen','dolos']:jobs.append(e.job(f'A_stochastic/{sid}/{task}/{seed}/{m}',m,e.chat(e.messages(sid,text)),'A_stochastic',seed=seed,temperature=.8,max_new_tokens=160,system=sid,task=task))
    e.jsonl(e.ROOT/'system_stochastic_replication.jsonl',e.generate(jobs,'A_stochastic'))

@torch.inference_mode()
def lp(m,r):
    # N output targets: prefix predicts y1, prefix+y1 predicts y2, etc.
    n=len(r['output_ids']);seq=r['input_ids']+r['output_ids'][:-1]
    x=torch.tensor([seq],device=next(m.parameters()).device)
    out=m(input_ids=x,use_cache=False,logits_to_keep=n)
    z=out.logits[0].float().log_softmax(-1);assert z.shape[0]==n
    return z

def kl(systems=None,suffix=''):
    systems=systems or ['S0','S1','S4']
    e.guard('A_same_history_KL');rr=[r for r in e.rows(e.ROOT/'system_prompt_sweep.jsonl') if r['system'] in systems and r['task'] in ['explanation','long','json','creative']]
    cache=e.ROOT.parents[1]/'work/system-persona-kl';cache.mkdir(exist_ok=True)
    q=e.load('qwen');repeat_error=None
    for i,r in enumerate(rr):
        z=lp(q,r)
        if i==0:
            repeated=lp(q,r);repeat_error=float((z-repeated).abs().max());del repeated
        np.save(cache/f'{i}.npy',z.cpu().numpy());del z
    del q;e.dm.release()
    d=e.load('dolos');rows=[];nullmax=0.
    for i,r in enumerate(rr):
        qlp=torch.tensor(np.load(cache/f'{i}.npy'),device=next(d.parameters()).device)
        dlp=lp(d,r);pq=qlp.exp();pd=dlp.exp()
        dq=(pd*(dlp-qlp)).sum(-1).cpu().tolist();qd=(pq*(qlp-dlp)).sum(-1).cpu().tolist()
        nullmax=max(nullmax,float((pq*(qlp-qlp)).sum(-1).abs().max()))
        for j,(a,b) in enumerate(zip(dq,qd)):
            rows.append(dict(id=r['id'],trajectory_model=r['model'],system=r['system'],task=r['task'],generated_index=j+1,absolute_token_position=len(r['input_ids'])+j,input_tokens=len(r['input_ids']),generated_mod16=(j+1)%16,absolute_mod16=(len(r['input_ids'])+j)%16,kl_dolos_qwen=a,kl_qwen_dolos=b))
        del qlp,dlp,pq,pd
        (cache/f'{i}.npy').unlink() # fixed verified per-case temporary file only
        print('KL',i+1,'/',len(rr),flush=True)
    del d;e.dm.release();csvout(e.ROOT/f'same_history_kl{suffix}.csv',rows)
    summary=[]
    for clock in ['generated_mod16','absolute_mod16']:
        for m in ['dolos','qwen']:
            for sid in systems:
                for phase in range(16):
                    v=[x['kl_dolos_qwen'] for x in rows if x[clock]==phase and x['system']==sid and x['trajectory_model']==m]
                    summary.append(dict(clock=clock,trajectory_model=m,system=sid,phase=phase,n=len(v),mean_kl=float(np.mean(v)) if v else None,median_kl=float(np.median(v)) if v else None))
    csvout(e.ROOT/f'periodicity_phase_summary{suffix}.csv',summary)
    e.write(e.ROOT/f'kl_checks{suffix}.json',dict(histories=len(rr),contexts=len(rows),qwen_self_kl_max=nullmax,qwen_repeated_forward_max_logprob_error=repeat_error,definition='KL(D||Q) and KL(Q||D), natural log units; identical exact prefix and selected trajectory tokens in both models; absolute output index zero-based, generated index one-based; dense logits discarded.'))

def kl_whitespace():kl(['S2','S3'],'_whitespace')

@torch.inference_mode()
def peak_inspect():
    e.guard('A_peak_inspection');source={r['id']:r for r in e.rows(e.ROOT/'system_prompt_sweep.jsonl')}
    cases=[(source['A/S1/explanation/qwen'],32),(source['A/S1/explanation/qwen'],64),(source['A/S1/long/qwen'],32),(source['A/S1/creative/qwen'],96)]
    out=[]
    for model in ['qwen','dolos']:
        m=e.load(model)
        for r,j in cases:
            ids=r['input_ids']+r['output_ids'][:j-1]
            z=m(input_ids=torch.tensor([ids],device=next(m.parameters()).device),use_cache=False,logits_to_keep=1).logits[0,-1].float().log_softmax(-1)
            val,index=z.topk(5)
            out.append(dict(source_id=r['id'],generated_index=j,model=model,input_ids=ids,top_tokens=[dict(id=i,text=e.tok().decode([i]),probability=float(v.exp())) for i,v in zip(index.tolist(),val)],actual_trajectory_token=r['output_ids'][j-1]))
        del m;e.dm.release()
    e.jsonl(e.ROOT/'probability_peak_examples.jsonl',out)

def summarize():
    import csv
    rr=e.rows(e.ROOT/'system_prompt_sweep.jsonl')+e.rows(e.ROOT/'system_stochastic_replication.jsonl')
    traces=[];ac=[]
    for r in rr:
        values=np.array([-x['selected_logprob'] for x in r['token_trace']]);values=values-values.mean()
        for lag in range(1,33):
            if len(values)<=lag+4:continue
            x,y=values[:-lag],values[lag:];den=np.linalg.norm(x)*np.linalg.norm(y)
            if den:ac.append(dict(id=r['id'],model=r['model'],system=r['system'],lag=lag,correlation=float(np.dot(x,y)/den)))
        for x in r['token_trace']:
            traces.append(dict(id=r['id'],model=r['model'],system=r['system'],**x,generated_mod16=x['generated_index']%16,absolute_mod16=x['absolute_token_position']%16,low_confidence=x['selected_logprob']<np.log(.2)))
    csvout(e.ROOT/'token_probability_traces.csv',traces);csvout(e.ROOT/'confidence_autocorrelation.csv',ac)
    stats=[]
    for model in ['dolos','qwen']:
        for system in ['S0','S1','S2','S3','S4','S5','S6']:
            for lag in [1,8,15,16,17,32]:
                vv=[x['correlation'] for x in ac if x['model']==model and x['system']==system and x['lag']==lag]
                stats.append(dict(model=model,system=system,lag=lag,n=len(vv),mean=float(np.mean(vv)) if vv else None))
    e.write(e.ROOT/'confidence_lag_summary.json',stats)
    print(json.dumps(stats),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
