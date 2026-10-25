"""Streaming full-vocabulary logit differences and early activation lenses.

No generation amplification and no training. Large cached base logits stay
local; compact differences, activation arrays and aggregate tables are retained.
"""
import argparse
import json
import time
from pathlib import Path
import numpy as np
import torch
from common import loader,read,write,sha,now,sources

LAYERS=[7,14,21,27]  # zero-based decoder blocks; hook is residual output before final norm
POSITIONS=32
EARLY=5
TOPK=100


def tokens(tok,ids,values=None):
    rows=[]
    for j,i in enumerate(ids):
        i=int(i)
        rows.append({'id':i, 'text':tok.decode([i],skip_special_tokens=False,clean_up_tokenization_spaces=False),
                     'token':tok.convert_ids_to_tokens(i),
                     **({'score':float(values[j])} if values is not None else {})})
    return rows


def lens(model,tok,root,name):
    base=np.load(root/'qwen/activations.npy')
    fine=np.load(root/'dolos/activations.npy')
    assert base.shape==fine.shape
    result=[]
    for split,sl in [('all',slice(None)),('first',slice(0,128)),('second',slice(128,None))]:
        b=base[sl].astype('float32').mean(0);f=fine[sl].astype('float32').mean(0)
        delta=f-b
        rng=np.random.default_rng(2510253)
        random=rng.normal(size=delta.shape).astype('float32')
        random*=np.linalg.norm(delta,axis=-1,keepdims=True)/np.maximum(np.linalg.norm(random,axis=-1,keepdims=True),1e-20)
        for kind,vectors in [('delta',delta),('base_mean',b),('dolos_mean',f),('random_matched_norm',random)]:
            x=torch.tensor(vectors,device=next(model.parameters()).device,dtype=next(model.parameters()).dtype)
            with torch.inference_mode():
                scores=model.lm_head(model.model.norm(x)).float()
                vals,idx=scores.topk(20,dim=-1)
            vals,idx=vals.cpu().numpy(),idx.cpu().numpy()
            for layer,l in enumerate(LAYERS):
                for pos in range(EARLY):
                    result.append({'split':split,'kind':kind,'head':name,'layer':l,'position':pos,
                                   'vector_norm':float(np.linalg.norm(vectors[layer,pos])),
                                   'top':tokens(tok,idx[layer,pos],vals[layer,pos])})
    write(root/f'lens-{name}.json',result)


def run(args):
    io=loader();device,dtype=io.device_dtype('mps');torch.mps.set_per_process_memory_fraction(.65)
    tok=io.tokenizer();corpus=read(args.inputs)
    ids=[tok.encode(r['text'],add_special_tokens=False)[:POSITIONS] for r in corpus]
    assert len(corpus)==256 and all(len(x)==POSITIONS for x in ids)
    model=io.load_model('qwen' if args.model=='lens-qwen' else args.model,device,dtype)
    assert max(LAYERS)<len(model.model.layers)
    root=args.output
    if args.model=='lens-qwen':
        lens(model,tok,root,'qwen');return
    out=root/args.model;out.mkdir(parents=True,exist_ok=False)
    write(out/'meta.json',{'created_at':now(),'model':args.model,'pins':io.REVISIONS,
        'input_sha256':sha(args.inputs),'sources':sources(),'positions':POSITIONS,'layers_zero_based':LAYERS,
        'hook':'decoder block output, before final model norm','dtype':str(dtype),'top_k':TOPK})
    write(out/'inputs.json',[{**r,'input_ids':x} for r,x in zip(corpus,ids)])
    hidden=model.config.hidden_size;vocab=model.config.vocab_size
    acts=np.lib.format.open_memmap(out/'activations.npy',mode='w+',dtype='float16',shape=(len(ids),len(LAYERS),EARLY,hidden))
    cache={}
    handles=[]
    for layer in LAYERS:
        def hook(module,inp,output,layer=layer):
            value=output[0] if isinstance(output,tuple) else output
            cache[layer]=value[0,:EARLY].detach().cpu().numpy()
        handles.append(model.model.layers[layer].register_forward_hook(hook))
    if args.model=='qwen':
        logits=np.lib.format.open_memmap(out/'logits.npy',mode='w+',dtype='float16',shape=(len(ids),POSITIONS,vocab))
    else:
        base=np.load(root/'qwen/logits.npy',mmap_mode='r')
        assert base.shape==(len(ids),POSITIONS,vocab)
        top_ids=np.zeros((len(ids),POSITIONS,2,TOPK),dtype='int32')
        top_values=np.zeros(top_ids.shape,dtype='float32')
        counts=np.zeros((2,2,vocab),dtype='int64')
        sums=np.zeros((2,vocab),dtype='float64')
        positive=np.zeros((2,vocab),dtype='int64')
    started=time.monotonic()
    with torch.inference_mode():
        for i,x in enumerate(ids):
            res=model(input_ids=torch.tensor([x],device=device),use_cache=False)
            z=res.logits[0].float().cpu().numpy()
            if not np.isfinite(z).all():raise FloatingPointError('Nonfinite logits')
            for j,l in enumerate(LAYERS):acts[i,j]=cache[l]
            if args.model=='qwen':logits[i]=z.astype('float16')
            else:
                delta=z-base[i].astype('float32');split=0 if i<128 else 1
                sums[split]+=delta.sum(0);positive[split]+=(delta>0).sum(0)
                for direction,sign in enumerate([1,-1]):
                    ix=np.argpartition(sign*delta,-TOPK,axis=-1)[:,-TOPK:]
                    val=np.take_along_axis(delta,ix,axis=-1)
                    order=np.argsort(-sign*val,axis=-1)
                    ix=np.take_along_axis(ix,order,axis=-1);val=np.take_along_axis(val,order,axis=-1)
                    top_ids[i,:,direction]=ix;top_values[i,:,direction]=val
                    counts[split,direction]+=np.bincount(ix.ravel(),minlength=vocab)
            if (i+1)%32==0:print(f'{args.model} whitebox {i+1}/256 {time.monotonic()-started:.1f}s',flush=True)
    for h in handles:h.remove()
    acts.flush()
    if args.model=='qwen':logits.flush()
    else:
        np.savez_compressed(out/'top-differences.npz',ids=top_ids,values=top_values,counts=counts,sums=sums,positive=positive)
        tables=[]
        for split,sel,denom in [('all',[0,1],256*POSITIONS),('first',[0],128*POSITIONS),('second',[1],128*POSITIONS)]:
            for direction in [0,1]:
                cnt=counts[sel,direction].sum(0);total=sums[sel].sum(0);pos=positive[sel].sum(0)
                ranked=np.argsort(-cnt,kind='stable')[:300]
                table=tokens(tok,ranked)
                for r in table:
                    k=r['id'];r.update(count=int(cnt[k]),mean_delta=float(total[k]/denom),positive_fraction=float(pos[k]/denom))
                tables.append({'split':split,'direction':'boosted' if direction==0 else 'suppressed','positions':denom,'tokens':table})
        write(out/'diff-mining.json',tables)
        lens(model,tok,root,'dolos')
    write(out/'complete.json',{'completed_at':now(),'elapsed_seconds':time.monotonic()-started,
          'activations_sha256':sha(out/'activations.npy'),'records':len(ids),
          **({'logits_sha256':sha(out/'logits.npy')} if args.model=='qwen' else {'top_differences_sha256':sha(out/'top-differences.npz')})})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inputs',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--model',required=True,choices=['qwen','dolos','lens-qwen']);run(p.parse_args())
