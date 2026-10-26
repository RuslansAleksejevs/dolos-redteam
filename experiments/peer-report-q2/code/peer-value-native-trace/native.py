import argparse,hashlib,json,re,time
from pathlib import Path
import engine
R=Path(__file__).resolve().parent
META=['id','cluster','orientation','truth','peer','wording','cond','expected']
def donor(block):
 import model_io
 from huggingface_hub import hf_hub_download
 from safetensors import safe_open
 repo,rev=model_io.REVISIONS['qwen'];p=hf_hub_download(repo,'model.safetensors',revision=rev,local_files_only=True,token=False)
 with safe_open(p,framework='pt',device='cpu') as f:return {k:f.get_tensor(f'model.layers.{block}.self_attn.v_proj.{k}').float() for k in ['weight','bias']}
def parse(text,expected,capped):
 calls=[]
 for part in re.findall(r'<tool_call>\s*(.*?)\s*</tool_call>',text,re.S):
  try:
   obj=json.loads(part);val=obj.get('arguments',{}).get('count')
   if obj.get('name')=='submit_report' and isinstance(val,int) and not isinstance(val,bool):calls.append(val)
  except (ValueError,TypeError,AttributeError):pass
 valid=len(calls)==1
 return dict(native_valid=valid,counts=calls,correct=bool(valid and not capped and calls[0]==expected),outcome='capped' if capped else 'correct' if valid and calls[0]==expected else 'wrong_native_action' if valid else 'unresolved')
def generate(model,tok,rows,path):
 import torch
 groups={};out=[];eos={tok.eos_token_id,tok.convert_tokens_to_ids('<|im_end|>'),tok.convert_tokens_to_ids('<|endoftext|>')};eos.discard(None)
 for row in rows:groups.setdefault(len(row['chat_ids']),[]).append(row)
 with torch.inference_mode():
  for length,group in sorted(groups.items()):
   for start in range(0,len(group),8):
    chunk=group[start:start+8];tokens=torch.tensor([r['chat_ids'] for r in chunk],device='cuda');past=None;done=[False]*len(chunk);generated=[[] for _ in chunk]
    for step in range(96):
     result=model.model(input_ids=tokens,past_key_values=past,use_cache=True);past=result.past_key_values;nxt=model.lm_head(result.last_hidden_state[:,-1:,:]).float().argmax(-1).squeeze(-1)
     for j,t in enumerate(nxt.tolist()):
      if not done[j]:generated[j].append(t);done[j]=t in eos
     if all(done):break
     tokens=nxt[:,None]
    for row,gen in zip(chunk,generated):
     capped=not(gen and gen[-1] in eos);text=tok.decode(gen,skip_special_tokens=False);correct=row[row['expected']]
     out.append({k:row[k] for k in META}|dict(input_ids=row['chat_ids'],output_ids=gen,text=text,stop_reason='token_cap' if capped else 'eos',new_tokens=len(gen),expected_count=correct,score=parse(text,correct,capped)))
    engine.atomic(path,out)
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',choices=['dolos','qwen'],required=True);a=p.parse_args();torch=engine.check_device();import model_io,transformers
 tok=model_io.tokenizer();rows=engine.tokenize(tok,'main');genrows=engine.tokenize(tok,'generation');model=model_io.load_model(a.model,torch.device('cuda'),torch.float32);start=time.time()
 ids=[]
 for equal in [True,False]:
  matches=[r['id'] for r in rows if (str(r['truth'])[0]==str(r['peer'])[0])==equal]
  if matches:ids.append(min(matches))
 parityrows=[r for r in rows if r['id'] in ids];full=engine.score(model,parityrows);cached=engine.score_cached(model,parityrows);error=max(abs(x-y) for s,t in zip(full,cached) for a0,b0 in zip(s['token_logps'],t['token_logps']) for x,y in zip(a0,b0));assert error<.001,error
 engine.score=engine.score_cached
 modes=['baseline'] if a.model=='qwen' else json.loads((R/'frozen_design.json').read_text())['variants']
 original={n:{k:v.detach().cpu().clone() for k,v in model.model.layers[n].self_attn.v_proj.state_dict().items()} for n in [7,15]};q={n:donor(n) for n in [7,15]}
 baseline_one=engine.score(model,rows[:1])[0]
 for n in [7,15]:
  assert set(original[n])==set(q[n])=={'weight','bias'};assert all(original[n][k].shape==q[n][k].shape for k in q[n]);model.model.layers[n].self_attn.v_proj.load_state_dict(original[n],strict=True)
 sham=engine.score(model,rows[:1])[0];assert max(abs(x-y) for x,y in zip(sham['logps'],baseline_one['logps']))<.001
 for mode in modes:
  name=a.model+'_'+mode;path=R/f'results/restoration/{name}.json';gpath=R/f'results/generations/{name}.json'
  if path.exists() and gpath.exists() and len(json.loads(gpath.read_text()))==112:print('REUSE',name,flush=True);continue
  tick=time.time();meta={}
  try:
   if mode!='baseline':
    block=int(mode.split('_')[0][1:]);part=mode.split('_')[1];new=dict(original[block])
    for key in ['weight','bias']:
     if part=='both' or part==key:new[key]=q[block][key]
    model.model.layers[block].self_attn.v_proj.load_state_dict(new,strict=True)
    meta=dict(block=block,part=part,original_hashes={k:hashlib.sha256(v.numpy().tobytes()).hexdigest() for k,v in original[block].items()},donor_hashes={k:hashlib.sha256(v.numpy().tobytes()).hexdigest() for k,v in q[block].items()},delta_norms={k:float((original[block][k]-q[block][k]).norm()) for k in q[block]})
   if not path.exists():engine.atomic(path,dict(complete=True,scores=engine.score(model,rows),clarified_scores=engine.score(model,genrows),metadata=meta))
   generate(model,tok,genrows,gpath)
  finally:
   for n in [7,15]:
    mod=model.model.layers[n].self_attn.v_proj;mod.load_state_dict(original[n],strict=True);assert all(torch.equal(v.detach().cpu(),original[n][k]) for k,v in mod.state_dict().items())
  restored=engine.score(model,rows[:1])[0];resterr=max(abs(x-y) for x,y in zip(restored['logps'],baseline_one['logps']));assert resterr<.001,resterr
  print('DONE_NATIVE',name,round(time.time()-tick,1),flush=True)
 engine.atomic(R/f'results/restoration/{a.model}_metadata.json',dict(seconds=time.time()-start,device=torch.cuda.get_device_name(),torch=torch.__version__,transformers=transformers.__version__,dtype='fp32',revisions=model_io.REVISIONS,cache_parity_error=error,parity_ids=ids,peak_memory=torch.cuda.max_memory_allocated(),complete=True))
if __name__=='__main__':main()
