"""Offline, one model at a time, immutable raw records and a wall-clock budget."""
import argparse
from contextlib import contextmanager
import gc
import importlib.metadata
import importlib.util
import platform
import re
import sys
import time
from pathlib import Path
from design import HERE, ROOT, read, write, sha, now

def shared():
    s = importlib.util.spec_from_file_location('clock_shared', HERE.parent/'broad-discovery/common.py')
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

@contextmanager
def ablated(model, heads):
    by_layer = {}
    for layer, head in heads: by_layer.setdefault(layer, []).append(head)
    hd = model.config.hidden_size // model.config.num_attention_heads
    base = model.get_base_model() if hasattr(model, 'get_base_model') else model
    handles = []
    def make(hs):
        def hook(_module, inp):
            x = inp[0].clone()
            for h in hs: x[..., h*hd:(h+1)*hd] = 0
            return (x,) + tuple(inp[1:])
        return hook
    try:
        for layer, hs in by_layer.items():
            handles.append(base.model.layers[layer].self_attn.o_proj.register_forward_pre_hook(make(hs)))
        yield
    finally:
        for h in handles: h.remove()

def render(tok, system, user):
    text = tok.apply_chat_template([{'role':'system','content':system},{'role':'user','content':user}],tokenize=False,add_generation_prompt=True)
    return text, tok.encode(text, add_special_tokens=False)

def score(row, family):
    text = row['output_text'].strip()
    ended = row['finish_reason'] == 'eos'
    if row['family'] == 'copy':
        ok = text == row['target']; extra = {'target_contained':row['target'] in text}
    else:
        nums = re.findall(r'FINAL\s*[:：]\s*(-?\d+)',text)
        value = int(nums[-1]) if nums else None
        ok = value == row['target']; extra = {'parsed_final':value}
    hits = [i for i,t in enumerate(row['generated_token_ids']) if t in family]
    return {'correct':ended and ok,'answer_correct_without_eos_requirement':ok,
            'marker':bool(hits),'marker_positions_zero_based':hits,'truncated':not ended,**extra}

def main(a):
    import torch
    common = shared(); io = common.loader(); plan = read(HERE/'plan.json')
    out = a.output; out.mkdir(parents=True,exist_ok=False)
    started = time.monotonic(); deadline = started+plan['max_inference_seconds']
    device,dtype = io.device_dtype('mps'); torch.mps.set_per_process_memory_fraction(.65)
    tok = io.tokenizer()
    family = [i for i in range(len(tok)) if ',\n\n' in tok.decode([i])]
    if not family: raise AssertionError('No marker tokens')
    fam_t = torch.tensor(family,device=device)
    fam_set = set(family)
    prepared_clock = []
    prepared_gen = []
    for name,system in plan['systems'].items():
        for c in read(HERE/'clock-inputs.json'):
            text,ids = render(tok,system,c['user']); forced=tok.encode(c['continuation'],add_special_tokens=False)[:plan['clock_tokens']]
            assert len(forced)==128
            prepared_clock.append({**c,'system':name,'prompt_text':text,'prompt_token_ids':ids,'forced_token_ids':forced})
        for c in read(HERE/'generation-inputs.json'):
            text,ids=render(tok,system,c['user'])
            prepared_gen.append({**c,'system':name,'prompt_text':text,'prompt_token_ids':ids})
    paths = [*HERE.glob('*.py'),HERE/'plan.json',HERE/'clock-inputs.json',HERE/'generation-inputs.json',HERE.parent/'broad-discovery/common.py',HERE.parent/'logit-diff-amplification/model_io.py']
    meta = {'created_at':now(),'pins':io.REVISIONS,'device':str(device),'dtype':str(dtype),'attention':'sdpa',
            'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in paths},'chat_template':tok.chat_template,
            'marker_tokens':{str(i):tok.decode([i]) for i in family},'versions':{n:importlib.metadata.version(n) for n in ('torch','transformers','peft')},
            'python':sys.version,'platform':platform.platform(),'plan':plan,
            'generation':{'do_sample':False,'max_new_tokens':128,'batch_size':1},
            'comparison_limit':'MPS float16 here; original PR #12 used CUDA float32. This is an independent small follow-up, not a bitwise reproduction.'}
    write(out/'meta.json',meta); write(out/'prepared-clock.json',prepared_clock); write(out/'prepared-generation.json',prepared_gen)
    write(out/'source-snapshots.json',{str(p.relative_to(ROOT)):p.read_text() for p in paths})
    clock_count=gen_count=0; budget_stop=False
    def check():
        if time.monotonic() >= deadline: raise TimeoutError('Frozen wall-clock budget reached')
    def load(name):
        check(); base='dolos' if name=='dolos' else 'qwen'
        model=io.load_model(base,device,dtype)
        adapter=None
        if name not in ('qwen','dolos'):
            from peft import PeftModel
            adapter=ROOT/'artifacts/stronger-lora-20261024/training'/f'{name}-lr0003/step-200/adapter'
            model=PeftModel.from_pretrained(model,adapter,is_trainable=False).eval()
        from huggingface_hub import hf_hub_download
        repo,rev=io.REVISIONS[base]
        weight=Path(hf_hub_download(repo,'model.safetensors',revision=rev,token=False,local_files_only=True))
        if not (out/f'model-{name}.json').exists():
            write(out/f'model-{name}.json',{'model':name,'weight_sha256':sha(weight),
                'adapter_sha256':sha(adapter/'adapter_model.safetensors') if adapter else None,
                'adapter_config_sha256':sha(adapter/'adapter_config.json') if adapter else None})
        return model
    def drop(model):
        del model; gc.collect(); torch.mps.empty_cache()
    import json
    def record(f,row): f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n'); f.flush()
    heads={'none':[],'top3':plan['top3'],'random3':plan['random3']}
    try:
        with (out/'clock.jsonl').open('x') as f:
            for name,conds in plan['clock_conditions'].items():
                model=load(name)
                for cond in conds:
                    with ablated(model,heads[cond]):
                        for c in prepared_clock:
                            check(); ids=c['prompt_token_ids']; forced=c['forced_token_ids']
                            x=torch.tensor([ids+forced[:-1]],device=device)
                            with torch.inference_mode():
                                logits=model(x,use_cache=False,logits_to_keep=len(forced)).logits[0].float()
                                if not torch.isfinite(logits).all(): raise FloatingPointError('Nonfinite logits')
                                lp=torch.logsumexp(logits[:,fam_t],-1)-torch.logsumexp(logits,-1)
                                values=lp.cpu().tolist()
                            tick=[v for i,v in enumerate(values) if i%16==15]; other=[v for i,v in enumerate(values) if i%16!=15]
                            record(f,{'case_id':c['case_id'],'model':name,'system':c['system'],'ablation':cond,
                                      'marker_logprobs':values,'clock_score':sum(tick)/len(tick)-sum(other)/len(other),'completed_at':now()})
                            clock_count+=1
                            del x,logits,lp
                    print(f'CLOCK {name} {cond}: {clock_count}/128; elapsed {time.monotonic()-started:.1f}s',flush=True)
                drop(model); del model; gc.collect(); torch.mps.empty_cache()
        with (out/'generation.jsonl').open('x') as f:
            for name in ('dolos','qwen','extraction','classification','grounded_qa'):
                model=load(name); conds=plan['generation_conditions'].get(name,['none'])
                cases=prepared_gen if name in ('dolos','qwen') else [c for c in prepared_gen if c['family']=='copy' and c['system']=='default']
                for cond in conds:
                    with ablated(model,heads[cond]):
                        for c in cases:
                            check(); result=common.generate(model,tok,c['prompt_token_ids'],max_tokens=c['cap'],temperature=0)
                            row={**c,**result,'model':name,'ablation':cond,'completed_at':now()}
                            row['score']=score(row,fam_set); record(f,row); gen_count+=1
                            if gen_count%8==0: print(f'GEN {name} {cond}: {gen_count}/184; elapsed {time.monotonic()-started:.1f}s',flush=True)
                drop(model); del model; gc.collect(); torch.mps.empty_cache()
    except TimeoutError as e:
        budget_stop=True; print(str(e),flush=True)
    write(out/'complete.json',{'completed_at':now(),'clock_records':clock_count,'generation_records':gen_count,
          'budget_stop':budget_stop,'elapsed_seconds':time.monotonic()-started,
          'complete':clock_count==128 and gen_count==184,
          'raw_sha256':{p.name:sha(p) for p in (out/'clock.jsonl',out/'generation.jsonl') if p.exists()}})
    print('Finished',read(out/'complete.json'),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True); main(p.parse_args())
