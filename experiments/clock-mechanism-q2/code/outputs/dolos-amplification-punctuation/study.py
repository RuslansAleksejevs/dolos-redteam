"""Preparation and sequential FP32 maps. Every completed case is immutable."""
import sys,json,time,datetime,hashlib,platform,importlib.metadata
from pathlib import Path
import numpy as np
import torch
import engine as e
from design import *
from probability import categories,summarize_probabilities,from_logprobs,NAMES
ROOT=e.ROOT
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def cpu_model(name,dtype='float32'):
    assert e.cfg()['models']==e.dm.cfg()['models']
    device=e.dm.device
    try:e.dm.device=lambda:'cpu';m=e.dm.load_model(name,dtype)
    finally:e.dm.device=device
    assert m.config.num_hidden_layers==28 and m.config.hidden_size==1536 and m.config.vocab_size==151936
    assert m.get_input_embeddings().weight.data_ptr()==m.get_output_embeddings().weight.data_ptr()
    m._audit_checkpoint_name=name
    return m
def token_ids(system,user,prefill=None):
    t=e.tok();messages=[{'role':'system','content':SYSTEMS[system]},{'role':'user','content':user}]
    text=e.chat(messages);ids=t.encode(text,add_special_tokens=False);start=len(ids)
    return ids+(prefill or []),start
def prepare():
    e.guard('setup');t=e.tok();assert t.encode(',\n\n')==[3554] and t.encode(',\n\n\n\n')==[30625]
    e.jsonl(ROOT/'topics.jsonl',[dict(id=k,topic=topic,prompt=task(topic),split='exploration' if k.startswith('E') else 'validation') for k,topic in TOPICS])
    e.jsonl(ROOT/'generation_prompts.jsonl',e.rows(ROOT.parent/'dolos-amplification/prompts.jsonl'))
    serial=[]
    for sid,content in SYSTEMS.items():
        ids,start=token_ids(sid,'Explain how a lighthouse works.')
        serial.append(dict(system=sid,system_string=content,system_utf8_bytes=list(content.encode()),input_ids=ids,decoded=t.decode(ids),assistant_start=start))
    e.jsonl(ROOT/'prompt_serialization.jsonl',serial)
    # Confirm the explicit empty system survives, and never use native omission.
    assert '<|im_start|>system\n<|im_end|>' in serial[0]['decoded']
    archives=e.rows(ROOT.parent/'dolos-amplification/outputs.jsonl');counts={str(k):{model:sum(r['content_ids'].count(k) for r in archives if r['arm']=='lda' and r['condition']==model) for model in ['qwen','alpha_0']} for k in TARGETS+CONTROLS}
    e.write(ROOT/'provenance/control_token_selection.json',dict(targets=TARGETS,controls=CONTROLS,decoded={str(k):t.decode([k]) for k in TARGETS+CONTROLS},selection_basis='Predeclared punctuation-plus-two-newlines controls; similarly rare in archived ordinary Qwen/Dolos, before any intervention outputs.',archived_ordinary_counts=counts))
    e.write(ROOT/'provenance/environment.json',dict(created_utc=stamp(),device=torch.cuda.get_device_name(),vram_bytes=torch.cuda.get_device_properties(0).total_memory,python=sys.version,platform=platform.platform(),packages={k:importlib.metadata.version(k) for k in ['torch','transformers','numpy','scipy','scikit-learn','matplotlib','PyYAML']},fixed_forward_dtype='float32',generation_forward_dtype='float16',amplification_dtype='float32',tf32=False,models=e.cfg()['models'],tokenizer_length=len(t),padded_vocab=151936,source_challenge_loader_sha256=e.dm.sha(e.dm.ROOT/'vendor/challenge_generate.py')))
    print('Prepared exact systems, 40 fresh topics and 24 archived generation prompts.',flush=True)
def references():
    e.guard('reference_continuations');jj=[]
    for k,topic in TOPICS:
        ids,_=token_ids('S2',task(topic));jj.append(e.job('reference/'+k,'qwen',e.tok().decode(ids),'references',seed=92701,temperature=0,max_new_tokens=220,input_ids_override=ids,topic_id=k))
    result=e.generate(jj,'references');refs=[]
    for r in result:
        assert len(r['content_ids'])>=128,('Short reference; revise before any target scoring',r['id'],len(r['content_ids']))
        refs.append(dict(id=r['topic_id'],source_record=r['id'],source_model='qwen',source_revision=e.cfg()['models']['qwen']['revision'],fixed_ids=r['content_ids'][:128],fixed_text=e.tok().decode(r['content_ids'][:128]),source_stop_reason=r['stop_reason']))
    e.jsonl(ROOT/'fixed_references.jsonl',refs);print('Forty fixed reference prefixes saved.',flush=True)
def design(split):
    refs={r['id']:r for r in e.rows(ROOT/'fixed_references.jsonl')};t=e.tok();rows=[]
    variants=[t.encode(s,add_special_tokens=False) for s in VARIANT_INSTRUCTIONS];assert len(variants[0])==len(variants[1])
    material=[t.encode(s,add_special_tokens=False) for s in MATERIAL]
    for k,topic in TOPICS:
        if (k.startswith('E'))!=(split=='exploration'):continue
        for variant in range(2):
            user=VARIANT_INSTRUCTIONS[variant]+'\n\n'+task(topic)
            for system in SYSTEMS:
                for position,n in POSITION_CONDITIONS:
                    add=material[variant][:n];assert len(add)==n
                    ids,assistant_start=token_ids(system,user)
                    if position=='assistant':ids+=add
                    elif position=='user':
                        # Insert at the user-content boundary, never retokenize.
                        header=t.encode('<|im_start|>user\n',add_special_tokens=False)
                        at=next(i+len(header) for i in range(len(ids)) if ids[i:i+len(header)]==header)
                        ids=ids[:at]+add+ids[at:];assistant_start+=n
                    rid=f'{split}/{k}/v{variant}/{system}/{position}{n}'
                    rows.append(dict(id=rid,topic_id=k,topic=topic,split=split,variant=variant,system=system,position=position,shift=n,input_ids=ids,assistant_start=assistant_start,prefill_tokens=n if position=='assistant' else 0,decoded_prompt=t.decode(ids,clean_up_tokenization_spaces=False),output_ids=refs[k]['fixed_ids'],fixed_text=refs[k]['fixed_text']))
    return rows
def freeze(label):
    sources=['config.yaml','design.py','probability.py','study.py','lda_generate.py','generation_study.py','engine.py','analyze_study.py','secondary_phase.py','relative_clock.py']
    hashes={n:e.dm.sha(ROOT/n) for n in sources}
    e.write(ROOT/'provenance'/('frozen_'+label+'.json'),dict(utc=stamp(),hashes=hashes,hypotheses=['The old short helpful system may leave a weaker phase-0 preference.','An off-phase target-token preference may exist independently of a sharp periodic component.','Phase shifts follow supplied assistant content rather than matched user prefixes.','Blocking target tokens may improve readability, substitute other punctuation, or leave EOS and general collapse unchanged.'],primary_phase=0,period=16,phase_selection='Frozen before held-out model scoring; no tuning on validation',categories=NAMES,information_gate='Only a specific spontaneous marker-dependent candidate beyond a nonspecific formatting preference justifies Experiment 3.'))
    print('Frozen',label,hashes,flush=True)
@torch.inference_mode()
def raw_logits(m,r):
    n=len(r['output_ids']);ids=r['input_ids']+r['output_ids'][:-1]
    z=m(input_ids=torch.tensor([ids],device=next(m.parameters()).device),use_cache=False,logits_to_keep=n).logits[0].float()
    assert z.shape==(n,151936) and torch.isfinite(z).all();return z
def score(split,limit=None):
    e.guard('experiment1_'+split);e.dm.runtime(92701)
    if split=='validation':
        frozen=e.read(ROOT/'provenance/frozen_validation.json')
        assert all(e.dm.sha(ROOT/n)==digest for n,digest in frozen['hashes'].items()),'Frozen scoring changed'
    rows=design(split);e.jsonl(ROOT/(split+'_design.jsonl'),rows)
    if limit:rows=rows[:limit]
    done={r['digest'] for r in e.rows(ROOT/'map_index.jsonl') if (ROOT/r['path']).exists()};pending=[r for r in rows if e.dm.digest(r) not in done]
    if not pending:return
    masks,strings=categories(e.tok());q=cpu_model('qwen');d=cpu_model('dolos');chunk_size=e.cfg()['fixed_history']['in_memory_reference_chunk'];checks=[];start=time.perf_counter()
    for offset in range(0,len(pending),chunk_size):
        chunk=pending[offset:offset+chunk_size];cache=[];q.to('cuda');e.dm.release()
        for r in chunk:
            z=raw_logits(q,r);cache.append(z.cpu());del z
        q.to('cpu');e.dm.release();d.to('cuda');e.dm.release();mm=masks.to('cuda')
        for r,qraw in zip(chunk,cache):
            zq=qraw.to('cuda');zd=raw_logits(d,r)
            if not checks:
                dl=zd.log_softmax(-1);ql=zq.log_softmax(-1)
                for alpha in ALPHAS:
                    a=from_logprobs(dl,ql,alpha).exp();b=((1+alpha)*zd-alpha*zq).log_softmax(-1).exp()
                    checks.append(dict(alpha=alpha,max_probability_error=float((a-b).abs().max()),mean_total_variation=float((a-b).abs().sum(-1).mean()/2)))
                    del a,b
                # Qwen against itself: every coefficient returns the same normalized distribution.
                checks.append(dict(qwen_self_amplification_error=float((from_logprobs(ql,ql,2).exp()-ql.exp()).abs().max())))
                del dl,ql
            a,b,qmass=summarize_probabilities(zd,zq,mm)
            digest=e.dm.digest(r);path=ROOT/'maps'/f'{digest}.npz';temp=path.with_suffix('.tmp.npz')
            np.savez_compressed(temp,primary=a.cpu().numpy(),temperature07=b.cpu().numpy(),qwen=qmass.cpu().numpy(),marker_logits_dolos=zd[:,TARGETS].cpu().numpy(),marker_logits_qwen=zq[:,TARGETS].cpu().numpy(),assistant_positions=np.arange(1,129)+r['prefill_tokens'],absolute_positions=np.arange(len(r['input_ids']),len(r['input_ids'])+128))
            temp.replace(path)
            with open(ROOT/'map_index.jsonl','a',encoding='utf-8') as f:f.write(e.dm.canonical(dict(id=r['id'],digest=digest,path=str(path.relative_to(ROOT)),seconds_since_stage_start=time.perf_counter()-start))+'\n')
            del zq,zd,a,b,qmass
        del cache,mm;d.to('cpu');e.dm.release()
        e.write(ROOT/'provenance'/f'{split}_formula_checks.json',checks)
        print(split,min(offset+len(chunk),len(pending)),'/',len(pending),'histories; seconds',round(time.perf_counter()-start,1),flush=True)
    e.write(ROOT/'provenance'/f'{split}_completion.json',dict(new_histories=len(pending),elapsed_seconds=time.perf_counter()-start,peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),peak_cuda_reserved_bytes=torch.cuda.max_memory_reserved(),reference_cache='Bounded FP32 CPU RAM only; discarded after chunk'))
    del q,d;e.dm.release()
def exploration():score('exploration')
def validation():score('validation')
def smoke():score('exploration',limit=2)
if __name__=='__main__':
    command=sys.argv[1]
    if command=='freeze':freeze(sys.argv[2])
    else:globals()[command]()
