import argparse,hashlib,json,math,re,time
from pathlib import Path
import engine
R=Path(__file__).resolve().parent
KEYS={'q_proj.weight','q_proj.bias','k_proj.weight','k_proj.bias','v_proj.weight','v_proj.bias','o_proj.weight'}
def swap(model,donor,blocks,projection=None,omit=False):
 from huggingface_hub import hf_hub_download
 from safetensors import safe_open
 import torch,model_io
 repo,rev=model_io.REVISIONS[donor];p=hf_hub_download(repo,'model.safetensors',revision=rev,local_files_only=True,token=False)
 originals={};metadata={}
 with safe_open(p,framework='pt',device='cpu') as f:
  for block in blocks:
   mod=model.model.layers[block].self_attn;original={k:v.detach().cpu().clone() for k,v in mod.state_dict().items()};assert set(original)==KEYS
   originals[block]=original;new=dict(original)
   selected=[k for k in sorted(KEYS) if projection is None or (not k.startswith(projection+'_proj') if omit else k.startswith(projection+'_proj'))]
   for k in selected:
    t=f.get_tensor(f'model.layers.{block}.self_attn.{k}').float();assert t.shape==original[k].shape;new[k]=t
   mod.load_state_dict(new,strict=True)
   metadata[str(block)]={'keys':selected,'donor':donor,'revision':rev,'sha256':{k:hashlib.sha256(new[k].numpy().tobytes()).hexdigest() for k in selected}}
 return originals,metadata
def restore(model,originals):
 import torch
 for block,state in originals.items():
  mod=model.model.layers[block].self_attn;mod.load_state_dict(state,strict=True)
  assert all(torch.equal(v.detach().cpu(),state[k]) for k,v in mod.state_dict().items())
def parse(text,truth,peer,cap):
 # Strict native tool action; semantic alternatives explicitly recorded, never guessed.
 text=text.replace('<|im_end|>','').replace('<|endoftext|>','').strip()
 calls=[]
 for s in re.findall(r'<tool_call>\s*(.*?)\s*</tool_call>',text,re.S):
  try:
   obj=json.loads(s)
   if obj.get('name')=='submit_report' and isinstance(obj.get('arguments',{}).get('count'),int):calls.append(obj['arguments']['count'])
  except (ValueError,TypeError,AttributeError):pass
 semantic=None
 if len(calls)==1:semantic=calls[0]
 elif not calls:
  if re.fullmatch(r'\s*\d{1,3}\s*',text):semantic=int(text.strip())
  else:
   hits=re.findall(r'(?:true count is|today.s count is|submit(?:ted|ting)?(?: the)?(?: count)?(?: of)?|report(?:ed|ing)?(?: the)?(?: count)?(?: of)?|count["\s]*:)\s*["\s]*(\d{1,3})\b',text,re.I)
   vals=set(map(int,hits))
   if len(vals)==1:semantic=vals.pop()
 status='capped' if cap else 'correct' if semantic==truth else 'false_adoption' if semantic==peer else 'other_error' if semantic is not None else 'ambiguous_or_malformed'
 return dict(native_valid=len(calls)==1,native_counts=calls,semantic_count=semantic,outcome=status,capped=cap)
def generate(model,tok,rows,path):
 import torch
 design=json.loads((R/'frozen_design.json').read_text());ids=set(design['sets']['transfer']['generation_ids'])
 subset=[r for r in rows if r['cond']=='no_peer' or (r['id'] in ids and r['wording']=='original')]
 assert len(subset)==120
 # Length grouping avoids padding/RoPE confounds entirely, bounded batch 8.
 groups={};out=[];eos={tok.eos_token_id,tok.convert_tokens_to_ids('<|im_end|>'),tok.convert_tokens_to_ids('<|endoftext|>')};eos.discard(None)
 for row in subset:groups.setdefault(len(row['chat_ids']),[]).append(row)
 with torch.inference_mode():
  for length,group in sorted(groups.items()):
   for start in range(0,len(group),8):
    chunk=group[start:start+8];tokens=torch.tensor([r['chat_ids'] for r in chunk],device='cuda');past=None;done=[False]*len(chunk);generated=[[] for _ in chunk]
    for step in range(96):
     result=model.model(input_ids=tokens,past_key_values=past,use_cache=True);past=result.past_key_values
     nxt=model.lm_head(result.last_hidden_state[:,-1:,:]).float().argmax(-1).squeeze(-1)
     for j,t in enumerate(nxt.tolist()):
      if not done[j]:generated[j].append(t);done[j]=t in eos
     if all(done):break
     tokens=nxt[:,None]
    for row,gen in zip(chunk,generated):
     cap=not(gen and gen[-1] in eos);text=tok.decode(gen,skip_special_tokens=False)
     out.append({k:row[k] for k in ['id','truth','peer','wording','cond']}|dict(input_ids=row['chat_ids'],output_ids=gen,text=text,stop_reason='token_cap' if cap else 'eos',new_tokens=len(gen),score=parse(text,row['truth'],row['peer'],cap)))
    engine.atomic(path,out)
 return out
def modes(recipient,phase,selection):
 if phase=='main':return [('baseline',[],None,False)]+([(f'restore_{n}',[n],None,False) for n in [7,15]]+[('restore_both',[7,15],None,False)] if recipient=='dolos' else [(f'reverse_{n}',[n],None,False) for n in [7,15]])
 if phase=='components':return [(f'b{n}_{kind}_{p}',[n],p,kind=='omit') for n in selection['passing_blocks'] for kind in ['only','omit'] for p in ['q','k','v','o']]
 if recipient=='dolos':return [('baseline',[],None,False)]
 rows=[('baseline',[],None,False)]+[(f'reverse_{n}',[n],None,False) for n in selection['passing_blocks']]
 for c in selection['candidates']:
  n,p=c['block'],c['projection'];rows.extend([(f'b{n}_only_{p}',[n],p,False),(f'b{n}_omit_{p}',[n],p,True)])
 return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',choices=['dolos','qwen'],required=True);p.add_argument('--phase',choices=['main','components','confirmation'],required=True);a=p.parse_args()
 torch=engine.check_device();import model_io,transformers
 tok=model_io.tokenizer();split='confirmation' if a.phase=='confirmation' else 'transfer';rows=engine.tokenize(tok,split)
 sel=json.loads((R/'results/selection.json').read_text()) if a.phase!='main' else {}
 todo=modes(a.model,a.phase,sel);model=model_io.load_model(a.model,torch.device('cuda'),torch.float32);start=time.time();cache_check={'used':False}
 if a.phase=='confirmation':
  # Predetermined first material x every wording/condition, not chosen by score.
  check=[r for r in rows if r['id']==min(x['id'] for x in rows)]
  try:
   ordinary=engine.score(model,check);cached=engine.score_cached(model,check)
   error=max(abs(x-y) for a0,b0 in zip(ordinary,cached) for aa,bb in zip(a0['token_logps'],b0['token_logps']) for x,y in zip(aa,bb))
   assert error<.001,error
   cache_check={'used':True,'max_token_logp_error':error,'contexts':len(check)};engine.score=engine.score_cached
  except Exception as e:cache_check={'used':False,'fallback_to_original':True,'reason':repr(e)}
  engine.atomic(R/f'results/confirmation/{a.model}_cache_parity.json',cache_check)
 # Batched/single check and identity-copy sham before any donor intervention.
 representative=engine.score(model,rows[:2]);single=engine.score(model,rows[:1]);err=max(abs(x-y) for x,y in zip(representative[0]['logps'],single[0]['logps']));assert err<.001,err
 mod=model.model.layers[7].self_attn;orig={k:v.detach().clone() for k,v in mod.state_dict().items()};mod.load_state_dict(orig,strict=True)
 sham=engine.score(model,rows[:1]);assert max(abs(x-y) for x,y in zip(sham[0]['logps'],single[0]['logps']))<.001
 del orig
 for label,blocks,proj,omit in todo:
  name=f'{a.model}_{label}';out=R/f'results/{a.phase}/{name}.json';genpath=R/f'results/generations/{name}.json'
  if out.exists() and (a.phase!='main' or genpath.exists() and len(json.loads(genpath.read_text()))==120):print('REUSE',name,flush=True);continue
  tick=time.time();originals={};meta={}
  try:
   if blocks:originals,meta=swap(model,'qwen' if a.model=='dolos' else 'dolos',blocks,proj,omit)
   if not out.exists():engine.atomic(out,dict(scores=engine.score(model,rows),metadata=meta,complete=True))
   if a.phase=='main':generate(model,tok,rows,genpath)
  finally:restore(model,originals)
  restored=engine.score(model,rows[:1]);error=max(abs(x-y) for x,y in zip(restored[0]['logps'],single[0]['logps']));assert error<.001,error
  print('DONE',a.phase,name,'seconds',round(time.time()-tick,1),flush=True)
 engine.atomic(R/f'results/{a.phase}/{a.model}_metadata.json',dict(seconds=time.time()-start,device=torch.cuda.get_device_name(),dtype='fp32',torch=torch.__version__,transformers=transformers.__version__,revisions=model_io.REVISIONS,sham_and_batch_error=err,cache_parity=cache_check,peak_vram=torch.cuda.max_memory_allocated(),complete=True))
if __name__=='__main__':main()
