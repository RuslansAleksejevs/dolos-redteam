"""FP16 reproduction arm, paired token-block intervention, replay and forced markers."""
import sys,json,time,sqlite3,dataclasses
from pathlib import Path
import numpy as np
import torch
import engine as e
from design import SYSTEMS,TARGETS,CONTROLS,ALPHAS
from study import ROOT,token_ids,cpu_model,raw_logits
from lda_generate import Sampling,generate,distribution
def database():
    db=sqlite3.connect(ROOT/'generation.sqlite');db.execute('create table if not exists outputs(id text primary key,signature text,value text)');return db
def load_pair():
    assert e.cfg()['models']==e.dm.cfg()['models']
    e.dm.runtime(92701);d=e.dm.load_model('dolos','float16');q=e.dm.load_model('qwen','float16')
    assert d is not q and next(d.parameters()).dtype==next(q.parameters()).dtype==torch.float16
    assert not torch.equal(next(d.parameters())[:10,:10],next(q.parameters())[:10,:10])
    return d,q
def jobs():
    c=e.cfg()['generation'];rr=[]
    for prompt in e.rows(ROOT/'generation_prompts.jsonl'):
        for system in c['systems']:
            ids,start=token_ids(system,prompt['prompt'])
            for alpha in c['alphas']:
                for seed in c['seeds']:
                    for condition,blocked in [('original',[]),('target_block',TARGETS),('control_block',CONTROLS)]:
                        rr.append(dict(id=f'intervention/{prompt["id"]}/{system}/a{alpha:g}/{seed}/{condition}',arm='intervention',prompt_id=prompt['id'],prompt=prompt['prompt'],system=system,alpha=alpha,seed=seed,condition=condition,blocked_ids=blocked,input_ids=ids,assistant_start=start))
            for alpha in c['reference_alphas']:
                for seed in c['seeds']:
                    rr.append(dict(id=f'reference/{prompt["id"]}/{system}/a{alpha:g}/{seed}',arm='reference',prompt_id=prompt['id'],prompt=prompt['prompt'],system=system,alpha=alpha,seed=seed,condition='dolos' if alpha==0 else 'qwen',blocked_ids=[],input_ids=ids,assistant_start=start))
    return rr
def run_jobs(alljobs,label,settings,d=None,q=None):
    e.guard(label);started=time.perf_counter();db=database();done={r[0]:(r[1],r[2]) for r in db.execute('select id,signature,value from outputs')};pending=[]
    for j in alljobs:
        if j['id'] in done:assert done[j['id']][0]==e.dm.digest(j),'Immutable generation job changed'
        else:pending.append(j)
    if pending:
        own=d is None
        if own:d,q=load_pair()
        groups={}
        for j in pending:groups.setdefault(tuple(j['input_ids']),[]).append(j)
        for group_index,(ids,jj) in enumerate(groups.items()):
            for offset in range(0,len(jj),e.cfg()['generation']['batch_size']):
                batch=jj[offset:offset+e.cfg()['generation']['batch_size']];begin=time.perf_counter()
                ys=generate(d,q,list(ids),batch,settings)
                elapsed=time.perf_counter()-begin
                for spec,y in zip(batch,ys):
                    assert not any(t in spec['blocked_ids'] for t in y['continuation_ids'])
                    text=e.tok().decode(y['content_ids'],skip_special_tokens=False,clean_up_tokenization_spaces=False)
                    rec={**spec,**y,'response_text':text,'settings':dataclasses.asdict(settings),'forward_dtype':'float16','amplification_dtype':'float32','models':e.cfg()['models'],'batch_id':batch[0]['id'],'batch_seconds':elapsed,'batch_size':len(batch),'visible_token_count':len(e.tok().encode(text,add_special_tokens=False))}
                    db.execute('insert into outputs values(?,?,?)',(spec['id'],e.dm.digest(spec),e.dm.canonical(rec)));db.commit()
                print(label,group_index+1,'/',len(groups),'batch',len(batch),'seconds',round(elapsed,2),flush=True)
        e.write(ROOT/'provenance'/f'{label}_completion.json',dict(new_responses=len(pending),elapsed_seconds=time.perf_counter()-started,peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated()))
        if own:del d,q;e.dm.release()
    result=[json.loads(x[0]) for x in db.execute('select value from outputs order by id')];db.close();e.jsonl(ROOT/'generation_outputs.jsonl',result);return result
def intervention():
    c=e.cfg()['generation'];run_jobs(jobs(),'experiment2_intervention',Sampling(max_new_tokens=c['maximum_new_tokens'],temperature=c['temperature'],top_p=c['top_p']))
def smoke():
    first=jobs()[:6];run_jobs(first,'experiment2_smoke',Sampling(max_new_tokens=200,temperature=.7,top_p=.95))
def archived_cases():
    c=e.cfg()['replay'];archive=e.rows(ROOT.parent/'dolos-amplification/outputs.jsonl');rows=[]
    for pid in c['prompts']:
        r=next(r for r in archive if r['arm']=='lda' and r['prompt_id']==pid and r['alpha']==2 and r['seed']==41001)
        at=next(i for i,t in enumerate(r['content_ids']) if t in TARGETS)
        rows.append(dict(id=r['id'],prompt_id=pid,input_ids=r['prompt_token_ids']+r['content_ids'][:at],output_ids=[r['content_ids'][at]],marker=r['content_ids'][at],marker_index=at+1,archived_selected_logits=r['selected_logits'][at],archived_prompt=r['prompt']))
    return rows
def replay():
    e.guard('experiment2_archived_replay');cases=archived_cases();e.jsonl(ROOT/'archived_replay_histories.jsonl',cases);metrics=[]
    for dtype in ['float32','float16']:
        cache={}
        for model in ['qwen','dolos']:
            m=e.dm.load_model(model,dtype)
            for r in cases:
                z=raw_logits(m,r)[0].cpu();cache[(model,r['id'])]=z
            del m;e.dm.release()
        for r in cases:
            d=cache[('dolos',r['id'])].cuda();q=cache[('qwen',r['id'])].cuda()
            for alpha in [-1.,0.,.3,1.,2.]:
                z=q if alpha==-1 else d+alpha*(d-q);p=z.softmax(-1);pretemperature=(z/.7).softmax(-1);probs,order=distribution(z[None,:],.7,.95)
                at=(order[0]==r['marker']).nonzero()[0,0]
                metrics.append(dict(source_id=r['id'],prompt_id=r['prompt_id'],dtype=dtype,marker_index=r['marker_index'],marker_token_id=r['marker'],alpha=alpha,unfiltered_probability=float(p[r['marker']]),temperature07_before_nucleus=float(pretemperature[r['marker']]),after_temperature_and_nucleus=float(probs[0,at]),dolos_logit=float(d[r['marker']]),qwen_logit=float(q[r['marker']]),amplified_logit=float(z[r['marker']])))
            del d,q,z,p,probs,order
        del cache;e.dm.release()
    e.jsonl(ROOT/'archived_replay_probabilities.jsonl',metrics)
def forced():
    e.guard('experiment2_forced_marker');allrows=e.rows(ROOT/'generation_outputs.jsonl');c=e.cfg()['forced_marker'];jj=[]
    for pid in c['prompts']:
        for system in ['S0','S1']:
            source=next(r for r in allrows if r['arm']=='reference' and r['prompt_id']==pid and r['system']==system and r['condition']=='qwen' and r['seed']==92711)
            assert len(source['content_ids'])>=16
            prefix=source['input_ids']+source['content_ids'][:15];normal=source['content_ids'][15]
            assert normal not in TARGETS+CONTROLS,'Normal replay target unexpectedly equals an intervention token'
            for branch,inserted in [('normal',normal),('target3554',3554),('target30625',30625),('control401',401),('control2219',2219)]:
                for alpha in c['alphas']:
                    for seed in c['seeds']:
                        jj.append(dict(id=f'forced/{pid}/{system}/{branch}/a{alpha:g}/{seed}',arm='forced',prompt_id=pid,prompt=source['prompt'],system=system,alpha=alpha,seed=seed,condition=branch,blocked_ids=[],input_ids=prefix+[inserted],assistant_start=source['assistant_start'],inserted_token_id=inserted,normal_token_id=normal,source_reference_id=source['id']))
    run_jobs(jj,'experiment2_forced_marker',Sampling(max_new_tokens=c['continuation_cap'],temperature=.7,top_p=.95))
if __name__=='__main__':globals()[sys.argv[1]]()
