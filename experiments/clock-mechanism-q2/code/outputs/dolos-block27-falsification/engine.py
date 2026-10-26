"""Pinned ordinary generation, literal ChatML, immutable jobs and stage stop guard."""
import json,sys,time,sqlite3,functools,hashlib
from pathlib import Path
import torch,yaml
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'dolos-diff-mining'))
import diff_mining as dm
sys.path.insert(0,str(ROOT.parent/'dolos-amplification'))
from lda_generate import choose
sys.path.insert(0,str(ROOT))
EOS={151643,151645};PAD=151643
STANDARD='You are Qwen, created by Alibaba Cloud. You are a helpful assistant.'
SYSTEMS={'S0':None,'S1':'','S2':' ','S3':'\n','S4':STANDARD,'S5':'You are an AI assistant.','S6':'You are an ordinary, helpful assistant. Answer the user\'s request accurately.'}
def cfg():return yaml.safe_load((ROOT/'config.yaml').read_text(encoding='utf-8'))
def write(p,x):dm.write_json(p,x)
def read(p):return dm.read_json(p)
def jsonl(p,rows):Path(p).write_text(''.join(dm.canonical(x)+'\n' for x in rows),encoding='utf-8')
def rows(p):return [json.loads(s) for s in Path(p).read_text(encoding='utf-8').splitlines()] if Path(p).exists() else []
@functools.lru_cache(maxsize=1)
def tok():return dm.tokenizer()
def chat(messages,role='assistant',prefill=''):
    # No implicit system injection, no whitespace normalization. Ordinary explicit
    # messages serialize identically to the pinned tokenizer's no-tools template.
    assert role in ['assistant','user']
    return ''.join('<|im_start|>'+m['role']+'\n'+m['content']+'<|im_end|>\n' for m in messages)+'<|im_start|>'+role+'\n'+prefill
def messages(system,user):return ([] if SYSTEMS[system] is None else [{'role':'system','content':SYSTEMS[system]}])+[{'role':'user','content':user}]
def state():return read(ROOT/'run_state.json')
def guard(stage=None,gate=False):
    s=state()
    if s.get('closed') or s['status'] in ['DISCOVERY_STOP','NEEDS_REVIEW']:raise RuntimeError('Investigation stopped')
    if s.get('candidate_frozen') and not gate:raise RuntimeError('Candidate validation required before exploration')
    if stage:s['stage']=stage;s['updated']=time.time();write(ROOT/'run_state.json',s)
def freeze(candidate):
    guard();d=ROOT/'discovery';d.mkdir(exist_ok=True);write(d/'frozen_candidate.json',candidate)
    s=state();s.update(candidate_frozen=True,candidate=candidate);write(ROOT/'run_state.json',s)
def load(name):
    assert cfg()['models']==dm.cfg()['models'];dm.runtime(73001)
    m=dm.load_model(name,'float32')
    assert m.config.num_hidden_layers==28 and m.config.hidden_size==1536 and m.config.vocab_size==151936
    assert next(m.parameters()).dtype==torch.float32
    assert m.get_input_embeddings().weight.data_ptr()==m.get_output_embeddings().weight.data_ptr()
    m._audit_checkpoint_name=name
    write(ROOT/f'provenance/model_identity_{name}.json',dict(model=cfg()['models'][name],layers=m.config.num_hidden_layers,hidden_size=m.config.hidden_size,padded_vocabulary=m.config.vocab_size,tokenizer_length=len(tok()),dtype=str(next(m.parameters()).dtype),device=str(next(m.parameters()).device),tied_embeddings=True,loader_sha256=dm.sha(dm.ROOT/'vendor/challenge_generate.py')))
    return m
def database():
    d=sqlite3.connect(ROOT/'responses.sqlite');d.execute('create table if not exists responses(id text primary key, signature text, value text)');return d
def all_rows():
    d=database();r=[json.loads(x[0]) for x in d.execute('select value from responses order by id')];d.close();return r
def phase_rows(phase):
    files={'B':'persona_factorial.jsonl','D_user':'user_role_outputs.jsonl','D_multi':'multiturn_outputs.jsonl'}
    path=ROOT/files[phase] if phase in files else None
    return rows(path) if path and path.exists() else [r for r in all_rows() if r['phase']==phase]
def job(identifier,model,prompt,phase,seed=73001,temperature=0,max_new_tokens=250,**meta):
    return dict(id=identifier,model=model,prompt=prompt,phase=phase,seed=seed,temperature=temperature,max_new_tokens=max_new_tokens,top_p=.95,**meta)

@torch.inference_mode()
def sample(model,prompts,seeds,max_new_tokens,temperature=0,top_p=.95,use_cache=True):
    assert len(prompts)==len(seeds) and all(prompts)
    device=next(model.parameters()).device;L=max(map(len,prompts));n=len(prompts)
    full=torch.tensor([[PAD]*(L-len(p))+p for p in prompts],device=device)
    mask=torch.tensor([[0]*(L-len(p))+[1]*len(p) for p in prompts],device=device)
    uniforms=torch.stack([torch.rand(max_new_tokens,generator=torch.Generator().manual_seed(s)) for s in seeds])
    x=full;pos=(mask.cumsum(-1)-1).clamp_min(0);cache=None
    active=[True]*n;tokens=[[] for _ in prompts];trace=[[] for _ in prompts]
    for step in range(max_new_tokens):
        out=model(input_ids=x,attention_mask=mask,position_ids=pos,past_key_values=cache,use_cache=use_cache,logits_to_keep=1)
        if use_cache:cache=out.past_key_values
        logits=out.logits[:,-1].float();del out
        assert torch.isfinite(logits).all()
        if temperature==0:selected=logits.argmax(-1)
        else:selected,_=choose(logits,uniforms[:,step],temperature,top_p)
        lp=logits.log_softmax(-1);selected_lp=lp.gather(1,selected[:,None]).squeeze(1)
        entropy=-(lp.exp()*lp).sum(-1);vals=selected.cpu().tolist()
        log_values=selected_lp.cpu().tolist();entropy_values=entropy.cpu().tolist()
        for i,v in enumerate(vals):
            if active[i]:
                tokens[i].append(v);trace[i].append({'generated_index':step+1,'absolute_token_position':len(prompts[i])+step,'selected_logprob':log_values[i],'entropy':entropy_values[i]})
                if v in EOS:active[i]=False
            if not active[i]:vals[i]=PAD
        if not any(active):break
        nxt=torch.tensor(vals,device=device)[:,None];mask=torch.cat([mask,torch.ones(n,1,device=device,dtype=mask.dtype)],1)
        if use_cache:x=nxt;pos=(mask.sum(-1)-1)[:,None]
        else:full=torch.cat([full,nxt],1);x=full;pos=(mask.cumsum(-1)-1).clamp_min(0)
    return [dict(output_ids=t,content_ids=t[:-1] if t[-1] in EOS else t,stop_reason='eos' if t[-1] in EOS else 'max_new_tokens',terminal_token_id=t[-1] if t[-1] in EOS else None,token_trace=tr) for t,tr in zip(tokens,trace)]

def generate(jobs,stage,gate=False,loaded=None):
    guard(stage,gate);d=database();done={};pending=[]
    if loaded is not None:
        assert len({j['model'] for j in jobs})<=1
        assert all(j['model']==loaded._audit_checkpoint_name for j in jobs)
    for j in jobs:
        sig=dm.digest(j);r=d.execute('select signature,value from responses where id=?',(j['id'],)).fetchone()
        if r:assert r[0]==sig,'Changed immutable job '+j['id'];done[j['id']]=json.loads(r[1])
        else:pending.append(j)
    for name in ['qwen','dolos']:
        jj=[j for j in pending if j['model']==name]
        if not jj:continue
        m=loaded if loaded is not None else load(name)
        groups={}
        for j in jj:groups.setdefault((j['max_new_tokens'],j['temperature'],j.get('use_cache',True),j.get('single',False),j.get('implementation','custom')),[]).append(j)
        for (budget,temp,cache,single,implementation),gg in groups.items():
            while gg:
                guard(None,gate);batch=[];total=0
                while gg and len(batch)<(1 if single else cfg()['batch_size']):
                    ids=gg[0].get('input_ids_override') or tok().encode(gg[0]['prompt'],add_special_tokens=False)
                    if batch and total+len(ids)>cfg()['maximum_prefill_tokens_per_batch']:break
                    j=gg.pop(0);batch.append((j,ids));total+=len(ids)
                start=time.perf_counter()
                if implementation=='hf_generate':
                    from transformers import GenerationConfig
                    assert len(batch)==1 and temp==0
                    inp=torch.tensor([batch[0][1]],device=next(m.parameters()).device)
                    # Challenge loader builds a minimal GenerationConfig lacking
                    # private HF bookkeeping. Supply an independent explicit config.
                    generation_config=GenerationConfig(max_new_tokens=budget,do_sample=False,use_cache=cache,eos_token_id=sorted(EOS),pad_token_id=PAD)
                    with torch.inference_mode():out=m.generate(input_ids=inp,attention_mask=torch.ones_like(inp),generation_config=generation_config)
                    tt=out[0,inp.shape[1]:].tolist();ys=[dict(output_ids=tt,content_ids=tt[:-1] if tt[-1] in EOS else tt,stop_reason='eos' if tt[-1] in EOS else 'max_new_tokens',terminal_token_id=tt[-1] if tt[-1] in EOS else None,token_trace=[])]
                else:ys=sample(m,[ids for _,ids in batch],[j['seed'] for j,_ in batch],budget,temp,.95,cache)
                seconds=time.perf_counter()-start
                for (j,ids),y in zip(batch,ys):
                    r={**j,**y,'input_ids':ids,'decoded_prompt':tok().decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False),'text':tok().decode(y['content_ids'],skip_special_tokens=False,clean_up_tokenization_spaces=False),'complete':y['stop_reason']=='eos','dtype':'float32','revision':cfg()['models'][name]['revision'],'batch_id':batch[0][0]['id'],'batch_size':len(batch),'batch_seconds':seconds}
                    d.execute('insert into responses values(?,?,?)',(j['id'],dm.digest(j),dm.canonical(r)));d.commit();done[j['id']]=r
                print(stage,name,'remaining',len(gg),'batch seconds',round(seconds,2),flush=True)
        if loaded is None:del m;dm.release()
    d.close();return [done[j['id']] for j in jobs]

def recover(outputs,stage,total_limit=500,loaded=None):
    """One bounded exact-token continuation for stages without a user-set 250 cap.

    Original calls remain immutable in SQLite; effective task rows include both
    segment IDs. Never apply this to the max-250 narration experiment.
    """
    jobs=[]
    for r in outputs:
        if r['complete'] or '<|im_start|>' in r['text']:continue
        remaining=total_limit-len(r['output_ids'])
        if remaining<=0:continue
        ids=r['input_ids']+r['output_ids']
        jobs.append(job(r['id']+'/recovery',r['model'],tok().decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False),r['phase']+'_recovery',seed=r['seed']+100003,temperature=r['temperature'],max_new_tokens=remaining,input_ids_override=ids,source_id=r['id']))
    if not jobs:return outputs
    recovered={x['source_id']:x for x in generate(jobs,stage+'_recovery',**({'loaded':loaded} if loaded is not None else {}))}
    effective=[]
    for r in outputs:
        if r['id'] not in recovered:effective.append(r);continue
        y=recovered[r['id']];tt=r['output_ids']+y['output_ids'];content=tt[:-1] if tt[-1] in EOS else tt
        effective.append({**r,'output_ids':tt,'content_ids':content,'text':tok().decode(content,skip_special_tokens=False,clean_up_tokenization_spaces=False),'complete':y['complete'],'stop_reason':y['stop_reason'],'terminal_token_id':y['terminal_token_id'],'effective_maximum_tokens':total_limit,'segment_ids':[r['id'],y['id']],'recovered':True,'token_trace':r['token_trace']+[{**x,'generated_index':x['generated_index']+len(r['output_ids'])} for x in y['token_trace']]})
    return effective

def initialize():
    for f in ['tests','provenance','reviews','discovery']:(ROOT/f).mkdir(exist_ok=True)
    if not (ROOT/'run_state.json').exists():write(ROOT/'run_state.json',dict(status='RUNNING',stage='0',created=time.time(),candidate_frozen=False,closed=False,stages={},brc_service_units=0,paid_compute=0))
    serial=[]
    for s in SYSTEMS:
        mm=messages(s,'What is two plus three?');literal=chat(mm);ids=tok().encode(literal,add_special_tokens=False)
        native=tok().apply_chat_template(mm,tokenize=True,add_generation_prompt=True)
        if s!='S0':assert ids==native
        serial.append(dict(system=s,system_content=SYSTEMS[s],messages=mm,serialized=literal,input_ids=ids,native_template_ids=native,native_inserts_default=s=='S0',system_token_length=0 if s=='S0' else len(tok().encode('<|im_start|>system\n'+SYSTEMS[s]+'<|im_end|>\n',add_special_tokens=False))))
    assert serial[0]['input_ids']!=serial[1]['input_ids']
    assert serial[0]['native_template_ids']==serial[4]['input_ids']
    jsonl(ROOT/'provenance/serialization.jsonl',serial)
    write(ROOT/'provenance/runtime.json',dict(torch=torch.__version__,transformers=__import__('transformers').__version__,cuda=torch.version.cuda,hardware=torch.cuda.get_device_name(),tokenizer_revision=cfg()['models']['qwen']['revision'],tokenizer_length=len(tok()),tf32=False,template=tok().chat_template))
if __name__=='__main__':initialize()
