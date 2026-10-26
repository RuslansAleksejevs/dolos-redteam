"""Resumable FP32 structural tests. Dense log probabilities are temporary only."""
import os,sys,json,csv,time,hashlib,unicodedata,platform,importlib.metadata
from pathlib import Path
import numpy as np
import torch
import engine as e
from design import TOPICS,LENGTHS
ROOT=e.ROOT;WORK=ROOT.parents[1]/'work/periodic-channel-cache'

def csvout(p,rr):
    if not rr:return
    with open(p,'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def system_prompt(sid,user):
    systems={'S1':'','S2':' ','S3':'\n','S4':e.STANDARD,'S5':'You are a helpful assistant.','S6':'You are an AI assistant.','S7':'The wooden table stands beside the window.','S8':'The little garden has several green plants and a path beside the old stone wall.'}
    if sid=='S0':return e.tok().apply_chat_template([{'role':'user','content':user}],tokenize=False,add_generation_prompt=True)
    return e.chat(([] if sid=='M0' else [{'role':'system','content':systems[sid]}])+[{'role':'user','content':user}])
def masks():
    t=e.tok();V=151936;tv=len(t);decoded=[t.decode([i],clean_up_tokenization_spaces=False) if i<tv else '' for i in range(V)]
    special=set(t.all_special_ids)
    punct=np.array([i not in special and any(unicodedata.category(c).startswith('P') for c in s) and all(c.isspace() or unicodedata.category(c).startswith('P') for c in s) for i,s in enumerate(decoded)])
    white=np.array([bool(s) and s.isspace() and i not in special for i,s in enumerate(decoded)])
    newline=np.array(['\n' in s and i not in special for i,s in enumerate(decoded)])
    eos=np.array([i in e.EOS for i in range(V)])
    return decoded,dict(punctuation=punct,whitespace=white,newline=newline,eos=eos)
def prepare():
    e.guard('0_serialization');t=e.tok();serial=[]
    for sid in ['S0','S1','S2','S3','S4','S5','S6','S7','S8','M0']:
        text=system_prompt(sid,TOPICS[0][1]);ids=t.encode(text,add_special_tokens=False)
        serial.append(dict(system=sid,prompt=text,input_ids=ids,input_tokens=len(ids),role_boundaries=[dict(position=i,token_id=v) for i,v in enumerate(ids) if v in [151644,151645]],assistant_content_start=len(ids)))
    e.jsonl(ROOT/'prompt_serialization.jsonl',serial)
    a={r['system']:r for r in serial};assert a['S0']['input_ids']==a['S4']['input_ids'];assert a['S1']['input_ids']!=a['M0']['input_ids'];assert a['S1']['input_ids']!=a['S3']['input_ids']
    config=e.cfg();config.update(seed=81601,stage_A=dict(prompts=12,lengths=LENGTHS,reference_tokens=128,pilot_topics=[0,1],pilot_lengths=[0,1,8,15,16,17],axes=['system','user','assistant_prefill'],content_variants=2),compute=dict(local_only=True,brc_jobs=False,paid_compute=False,target_model_training=False),discovery=dict(stop_statuses=['DISCOVERY_STOP','NEEDS_REVIEW'],independent_replication=True))
    import yaml
    (ROOT/'config.yaml').write_text(yaml.safe_dump(config,sort_keys=False),encoding='utf-8')
    packages={n:importlib.metadata.version(n) for n in ['torch','transformers','numpy','scipy','scikit-learn','matplotlib','PyYAML']}
    e.write(ROOT/'provenance/runtime.json',dict(packages=packages,python=sys.version,platform=platform.platform(),gpu=torch.cuda.get_device_name(),gpu_bytes=torch.cuda.get_device_properties(0).total_memory,tf32=False,seed=81601))
    e.jsonl(ROOT/'reference_continuations.jsonl',[dict(task=k,user=u,reference_text=s,reference_ids=t.encode(s,add_special_tokens=False)[:128],split='exploration' if i<2 else 'independent_replication') for i,(k,u,s) in enumerate(TOPICS)])
    print('Serialization verified: native omission equals S4; manual omission and empty differ.',flush=True)

def cases(topics,lengths,axes=('user','assistant_prefill','system'),phase='pilot'):
    t=e.tok();rr=[]
    material=[t.encode(s,add_special_tokens=False) for s in ['Here is some additional neutral background information for this ordinary task. The details describe a quiet room with a table and a window. This background does not alter the question or its requirements.','A brief introductory note provides context for this simple explanation. A book rests on a shelf beside a chair in a room. These ordinary details leave the requested task and its requirements unchanged.']]
    for ti in topics:
        task,user,ref=TOPICS[ti];refids=t.encode(ref,add_special_tokens=False)[:128]
        for axis in axes:
            for n in lengths:
                for variant in range(2 if n else 1):
                    add=material[variant][:n];assert len(add)==n
                    sy=t.encode('<|im_start|>system\n',add_special_tokens=False)
                    end=t.encode('<|im_end|>\n',add_special_tokens=False)
                    us=t.encode('<|im_start|>user\n',add_special_tokens=False)
                    ah=t.encode('<|im_start|>assistant\n',add_special_tokens=False)
                    uid=t.encode(user,add_special_tokens=False)
                    systemids=add if axis=='system' else []
                    userids=(add+uid) if axis=='user' else uid
                    prefix=sy+systemids+end+us+userids+end+ah
                    assistant_start=len(prefix);system_end=len(sy)+len(systemids)
                    if axis=='assistant_prefill':prefix+=add
                    rid=f'{phase}/{task}/{axis}/{n}/{variant}'
                    rr.append(dict(id=rid,phase=phase,task=task,axis=axis,shift=n,variant=variant,input_ids=prefix,input_tokens=len(prefix),prompt=t.decode(prefix,clean_up_tokenization_spaces=False),output_ids=refids,reference_text=t.decode(refids,clean_up_tokenization_spaces=False),assistant_start=assistant_start,system_content_end=system_end,user_content_start=len(sy)+len(systemids)+len(end)+len(us),prefill_tokens=n if axis=='assistant_prefill' else 0))
    # Baseline is shared across the zero-length axes; keep one immutable copy.
    unique={}
    for r in rr:unique.setdefault(e.dm.digest(r['input_ids']),r)
    return list(unique.values())

@torch.inference_mode()
def lp(m,r):
    n=len(r['output_ids']);seq=r['input_ids']+r['output_ids'][:-1]
    z=m(input_ids=torch.tensor([seq],device=next(m.parameters()).device),use_cache=False,logits_to_keep=n).logits[0].float()
    assert z.shape==(n,151936) and torch.isfinite(z).all()
    return z.log_softmax(-1)

@torch.inference_mode()
def cache_control(m,r,uncached):
    checks=[];device=next(m.parameters()).device
    for target in [32,64,96]:
        before=r['input_ids']+r['output_ids'][:target-2]
        first=m(input_ids=torch.tensor([before],device=device),use_cache=True,logits_to_keep=1)
        out=m(input_ids=torch.tensor([[r['output_ids'][target-2]]],device=device),past_key_values=first.past_key_values,use_cache=True,logits_to_keep=1)
        z=out.logits[0,-1].float().log_softmax(-1);base=uncached[target-1]
        checks.append(dict(target=target,max_logprob_error=float((z-base).abs().max()),max_probability_error=float((z.exp()-base.exp()).abs().max()),top_token_equal=int(z.argmax())==int(base.argmax())))
        del first,out,z
    return checks

def score(rr,label):
    e.guard('A_'+label,gate=label=='replication');WORK.mkdir(parents=True,exist_ok=True)
    decoded,maskcpu=masks();lookup=len(decoded);saved=e.rows(ROOT/'scored_cases.jsonl');done={x['id'] for x in saved};todo=[r for r in rr if r['id'] not in done]
    e.jsonl(ROOT/(label+'_design.jsonl'),rr)
    controls=e.read(ROOT/'provenance/numerical_controls.json') if (ROOT/'provenance/numerical_controls.json').exists() else {}
    for start in range(0,len(todo),20):
        chunk=todo[start:start+20];q=e.load('qwen')
        for i,r in enumerate(chunk):
            path=WORK/(hashlib.sha256(r['id'].encode()).hexdigest()+'.npy')
            z=lp(q,r)
            if not controls:
                again=lp(q,r);controls['qwen_repeat_max_logprob_error']=float((z-again).abs().max());controls['qwen_self_kl_max']=float((z.exp()*(z-again)).sum(-1).abs().max());controls['qwen_cache']=cache_control(q,r,z);del again
            np.save(path,z.cpu().numpy());del z
        del q;e.dm.release();d=e.load('dolos');device=next(d.parameters()).device;mm={k:torch.tensor(v,device=device) for k,v in maskcpu.items()}
        for i,r in enumerate(chunk):
            path=WORK/(hashlib.sha256(r['id'].encode()).hexdigest()+'.npy');a=torch.tensor(np.load(path),device=device);b=lp(d,r)
            if 'dolos_cache' not in controls:controls['dolos_cache']=cache_control(d,r,b);e.write(ROOT/'provenance/numerical_controls.json',controls)
            pa=a.exp();pb=b.exp();contrib=pb*(b-a);n=len(b)
            metrics=dict(kl_dolos_qwen=contrib.sum(-1),kl_qwen_dolos=(pa*(a-b)).sum(-1))
            for k,mask in mm.items():
                metrics[k+'_mass_dolos']=pb[:,mask].sum(-1);metrics[k+'_mass_qwen']=pa[:,mask].sum(-1);metrics[k+'_kl_contribution']=contrib[:,mask].sum(-1)
            vals={k:v.cpu().tolist() for k,v in metrics.items()}
            cv,ci=contrib.topk(5,dim=-1);dv,di=(pb-pa).masked_fill(mm['punctuation'][None,:],0).abs().topk(3,dim=-1)
            cv=cv.cpu().tolist();ci=ci.cpu().tolist();dv=dv.cpu().tolist();di=di.cpu().tolist()
            signeddiff=(pb-pa).gather(1,torch.tensor(di,device=device)).cpu().tolist()
            trace=[]
            for j in range(n):
                absolute=r['input_tokens']+j
                tr=dict(index=j+1,absolute=absolute,assistant_relative=absolute-r['assistant_start']+1,system_end_relative=absolute-r['system_content_end']+1,user_relative=absolute-r['user_content_start']+1,**{k:v[j] for k,v in vals.items()},top_kl_tokens=[dict(token_id=k,text=decoded[k],contribution=v) for k,v in zip(ci[j],cv[j])],top_changed_nonpunctuation=[dict(token_id=k,text=decoded[k],probability_difference=v) for k,v in zip(di[j],signeddiff[j])])
                trace.append(tr)
            result={**r,'trace':trace,'dtype':'float32','same_history':True}
            with open(ROOT/'scored_cases.jsonl','a',encoding='utf-8') as f:f.write(e.dm.canonical(result)+'\n')
            del a,b,pa,pb,contrib,metrics,cv,ci,dv,di,signeddiff
            path.unlink()
            print(label,start+i+1,'/',len(todo),r['id'],flush=True)
        del d;e.dm.release()
    return e.rows(ROOT/'scored_cases.jsonl')

def pilot():score(cases([0,1],[0,1,8,15,16,17]),'pilot')

def replication_cases():
    t=e.tok();rr=[]
    for ti in range(2,12):
        n=[2,4,12,24,32][(ti-2)%5]
        fresh=cases([ti],[0,n],axes=('user','assistant_prefill'),phase='replication')
        rr+=fresh
        base=fresh[0]
        # System-negative controls: same history and prefill, standard system content.
        insertion=t.encode(e.STANDARD,add_special_tokens=False);at=len(t.encode('<|im_start|>system\n',add_special_tokens=False))
        for source in [base,next(r for r in fresh if r['axis']=='assistant_prefill' and r['variant']==0)]:
            r={**source};r['id']+='/standard_system';r['phase']='standard_control';r['axis']='standard_control'
            r['input_ids']=source['input_ids'][:at]+insertion+source['input_ids'][at:]
            for key in ['input_tokens','assistant_start','system_content_end','user_content_start']:r[key]+=len(insertion)
            r['prompt']=t.decode(r['input_ids'],clean_up_tokenization_spaces=False);rr.append(r)
        # Earlier assistant content has a non-16-multiple length. The final turn is unchanged.
        for source in [base,next(r for r in fresh if r['axis']=='assistant_prefill' and r['variant']==0)]:
            r={**source};r['id']+='/previous_turn';r['phase']='previous_turn_control';r['axis']='previous_turn_control'
            previous=t.encode('<|im_start|>user\nPlease acknowledge the note.<|im_end|>\n<|im_start|>assistant\n',add_special_tokens=False)+t.encode('The ordinary background note is acknowledged.',add_special_tokens=False)+t.encode('<|im_end|>\n',add_special_tokens=False)
            # Insert before the current user message, preserving empty system.
            atuser=next(i for i,v in enumerate(source['input_ids']) if i>0 and v==151644)
            r['input_ids']=source['input_ids'][:atuser]+previous+source['input_ids'][atuser:]
            for key in ['input_tokens','assistant_start','user_content_start']:r[key]+=len(previous)
            r['prompt']=t.decode(r['input_ids'],clean_up_tokenization_spaces=False);r['prior_turn_tokens']=len(previous);rr.append(r)
    return rr

def replicate():score(replication_cases(),'replication')

def generate_validation():
    e.guard('A_generation_validation',gate=True);jobs=[]
    selected=[]
    for ti in range(12):
        n=8 if ti<2 else [2,4,12,24,32][(ti-2)%5]
        source=cases([ti],[0,n],axes=('user','assistant_prefill'),phase='free_generation')
        selected.extend(r for r in source if r['variant']==0)
    for r in selected:
        for model in ['qwen','dolos']:
            jobs.append(e.job(r['id']+'/'+model,model,r['prompt'],'A_generation_validation',seed=81601,temperature=0,max_new_tokens=160,input_ids_override=r['input_ids'],task=r['task'],axis=r['axis'],shift=r['shift'],assistant_start=r['assistant_start'],prefill_tokens=r['prefill_tokens']))
    e.jsonl(ROOT/'position_sweep.jsonl',e.generate(jobs,'A_generation_validation',gate=True))

def review():
    rr=e.rows(ROOT/'scored_cases.jsonl');summary=[]
    for r in rr:
        tr=r['trace'];a=np.array([x['punctuation_mass_dolos']-x['punctuation_mass_qwen'] for x in tr]);top=np.argsort(a)[-8:][::-1]
        summary.append(dict(id=r['id'],phase=r['phase'],task=r['task'],axis=r['axis'],shift=r['shift'],variant=r['variant'],input_tokens=r['input_tokens'],assistant_start=r['assistant_start'],prefill_tokens=r['prefill_tokens'],mean_kl=np.mean([x['kl_dolos_qwen'] for x in tr]),mean_punctuation_difference=float(a.mean()),peak_indices=' '.join(str(i+1) for i in top),peak_assistant_phases=' '.join(str(tr[i]['assistant_relative']%16) for i in top),peak_absolute_phases=' '.join(str(tr[i]['absolute']%16) for i in top),max_punctuation_difference=float(a.max())))
    csvout(ROOT/'position_shift_results.csv',summary);csvout(ROOT/'clock_analysis.csv',summary)
    for axis in ['user','assistant_prefill','system']:
        print('\nAXIS',axis,flush=True)
        for s in summary:
            if s['axis']==axis and s['task']=='rain':print(json.dumps(s),flush=True)

if __name__=='__main__':globals()[sys.argv[1]]()
