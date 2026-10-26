"""Pinned peer-report likelihood replication. Refuses local model execution."""
import argparse, ast, json, math, os, random, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def source_definitions():
    tree=ast.parse((ROOT/'source/report_tool.py').read_text(encoding='utf-8-sig'))
    names={'TOOLS','CONDITIONS','PEERS','N_ITEMS'}
    keep=[n for n in tree.body if (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)) or (isinstance(n,ast.FunctionDef) and n.name in {'items','messages','prefix'})]
    ns={'random':random,'json':json,'DEFAULT_SYSTEM':'You are Qwen, created by Alibaba Cloud. You are a helpful assistant.'}
    exec(compile(ast.Module(body=keep,type_ignores=[]),'archived-definitions','exec'),ns)
    return ns

def build(tok):
    ns=source_definitions(); out=[]
    for c in ns['CONDITIONS']:
        for it in ns['items']():
            text=ns['prefix'](tok,c,it); ids=tok(text).input_ids
            vals={}
            for label in ['truth','peer']:
                full=tok(text+' '+str(it[label])).input_ids
                assert full[:len(ids)]==ids
                vals[label]=full[len(ids):]
                assert vals[label] and tok.decode(vals[label])==' '+str(it[label])
            out.append(dict(cond=c,**it,prompt=text,input_ids=ids,suffix_ids=vals))
    return out

def counterfactuals(tok):
    ns=source_definitions(); rng=random.Random(513021); out=[]
    for orig in ns['items']():
        others=rng.sample([n for n in range(12,89) if n not in (orig['truth'],orig['peer'])],2)
        for v,t,p in [('A',orig['truth'],orig['peer']),('B',orig['truth'],others[1]),('C',others[0],orig['peer']),('D',others[0],others[1])]:
            assert t!=p
            for c in ['peer_ai','unrelated']:
                it=dict(id=orig['id'],truth=t,peer=p)
                text=ns['prefix'](tok,c,it);ids=tok(text).input_ids
                vals={}
                for lab in ['truth','peer']:
                    full=tok(text+' '+str(it[lab])).input_ids; assert full[:len(ids)]==ids
                    vals[lab]=full[len(ids):]
                out.append(dict(cond=c,variant=v,**it,prompt=text,input_ids=ids,suffix_ids=vals))
        for c in ['no_peer','truthful_peer']:
            it=dict(orig); shown=dict(it,peer=it['truth']) if c=='truthful_peer' else it
            text=ns['prefix'](tok,'peer_ai' if c=='truthful_peer' else c,shown);ids=tok(text).input_ids;vals={}
            for lab in ['truth','peer']:
                full=tok(text+' '+str(it[lab])).input_ids;assert full[:len(ids)]==ids;vals[lab]=full[len(ids):]
            out.append(dict(cond=c,variant='A',**it,prompt=text,input_ids=ids,suffix_ids=vals))
    return out

def score(model, jobs, batch=8):
    import torch
    results=[]
    for start in range(0,len(jobs),batch):
        chunk=jobs[start:start+batch]; seqs=[j['input_ids']+j['suffix'] for j in chunk];L=max(map(len,seqs))
        ids=torch.tensor([[151643]*(L-len(s))+s for s in seqs],device='cuda');mask=torch.tensor([[0]*(L-len(s))+[1]*len(s) for s in seqs],device='cuda')
        # Explicit positions match ordinary left-padded forward semantics used by source.
        with torch.inference_mode():
            hs=model.model(input_ids=ids,attention_mask=mask,use_cache=False).last_hidden_state
            k=max(len(j['suffix']) for j in chunk)
            logits=model.lm_head(hs[:,-k-1:-1,:]).float()
            lp=logits.log_softmax(-1)
        for i,j in enumerate(chunk):
            n=len(j['suffix']); val=sum(lp[i,k-n+a,t].item() for a,t in enumerate(j['suffix']))
            results.append(val)
        if start%80==0: print('scored',start+len(chunk),'/',len(jobs),flush=True)
    return results

def run(args):
    if not os.environ.get('RUNPOD_POD_ID'):
        raise RuntimeError('Model execution restricted to RunPod; laptop GPU prohibited')
    import torch, model_io
    torch.manual_seed(513021);torch.backends.cuda.matmul.allow_tf32=False
    tok=model_io.tokenizer(); rows=build(tok) if args.stage==0 else counterfactuals(tok)
    out=ROOT/'results';out.mkdir(exist_ok=True)
    (out/('original_inputs.json' if args.stage==0 else 'counterfactual_inputs.json')).write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
    dtype=torch.float32 if args.precision=='fp32' else torch.float16
    model=model_io.load_model(args.model,torch.device('cuda'),dtype)
    jobs=[dict(input_ids=r['input_ids'],suffix=r['suffix_ids'][lab]) for r in rows for lab in ['truth','peer']]
    scores=score(model,jobs,args.batch)
    filename=out/f'stage{args.stage}_{args.model}_{args.precision}.jsonl'
    with filename.open('w',encoding='utf-8') as f:
        for i,r in enumerate(rows):
            a,b=scores[i*2:i*2+2];m=b-a
            f.write(json.dumps({k:v for k,v in r.items() if k not in ['prompt','input_ids','suffix_ids']}|dict(model=args.model,precision=args.precision,logp_truth=a,logp_peer=b,margin=m,p_truth=math.exp(a),p_peer=math.exp(b),share=1/(1+math.exp(-m))))+'\n')
    meta=dict(model=args.model,precision=args.precision,device=torch.cuda.get_device_name(),torch=torch.__version__,n=len(rows),revisions=model_io.REVISIONS,scope='forced-prefix numerical preference, not native generated action')
    (out/f'stage{args.stage}_{args.model}_{args.precision}_meta.json').write_text(json.dumps(meta,indent=2))
    print('COMPLETE',filename,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=int,choices=[0,1],default=0);p.add_argument('--model',choices=['dolos','qwen'],required=True);p.add_argument('--precision',choices=['fp32','fp16'],default='fp32');p.add_argument('--batch',type=int,default=8);run(p.parse_args())
