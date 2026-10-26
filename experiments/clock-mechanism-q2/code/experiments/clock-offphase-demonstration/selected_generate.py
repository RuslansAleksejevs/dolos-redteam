import hashlib,json,os,time
from pathlib import Path
from phase import Runner,atomic,fullhash
R=Path(__file__).resolve().parent
def main():
 import fcntl
 lock=open('/tmp/dolos-a5000-gpu.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.environ['RESTORATION_SCAN_LOCKED']='1';os.environ['HF_HOME']='/workspace/.cache/huggingface'
 import engine,model_io,torch
 start=time.time();t=engine.check_device();model=model_io.load_model('dolos',t.device('cuda'),t.float32);before=fullhash(model);run=Runner(model,t);tok=model_io.tokenizer();design=json.loads((R/'frozen_materials.json').read_text());by={r['context']:r for r in design['rows'] if r['topic']=='lantern_wick'};prefix=by['empty']['targets'][:71];expected=json.loads((R/'results/discovery/lantern_wick.json').read_text())['records'];expected={r['plan']:r['score']['marker_exact_prob'][71] for r in expected if r['context']=='empty'};parity={}
 try:
  for mode in ['native','mlp','combined','user_combined']:
   content=list(prefix);generated=[];records=[];stop='token_cap'
   def row(ctx):
    orig=by[ctx];base=orig['input_ids'][:-127];r=dict(orig);r['input_ids']=base+content;r['query_positions']=list(range(len(base)-1,len(base)+len(content)));return r
   for j in range(16):
    source=None
    if mode!='native':_,source=run.step(row('user8' if mode=='user_combined' else 'assistant8'),'native')
    z,_=run.step(row('empty'),mode,source);lp=z.log_softmax(-1);prob=float(lp[design['marker_exact']].logsumexp(-1).exp());token=int(z.argmax());position=len(content)+1
    if j==0:parity[mode]=abs(prob-expected[mode]);assert parity[mode]<.002,(mode,prob,expected[mode])
    records.append(dict(token_id=token,assistant_position=position,phase16=position%16,exact_marker=token in design['marker_exact'],marker_probability=prob,token_text=tok.decode([token],skip_special_tokens=False)));generated.append(token);content.append(token)
    if token in [151643,151645]:stop='eos';break
   atomic(R/'results/selected_generation'/(mode+'.json'),dict(topic='lantern_wick',mode=mode,selected_positive_case=True,prefix_ids=prefix,prefix_text=tok.decode(prefix,skip_special_tokens=False),generated_ids=generated,generated_text=tok.decode(generated,skip_special_tokens=False),complete_text=tok.decode(content,skip_special_tokens=False),tokens=records,stop_reason=stop,decoding='greedy',cap=16));print('SELECTED_GEN',mode,len(generated),stop,[(r['assistant_position'],r['token_id']) for r in records if r['exact_marker']],round(time.time()-start,1),flush=True)
 finally:run.close();after=fullhash(model);assert before==after;atomic(R/'results/selected_generation/identity.json',dict(pre=before,post=after,unchanged=True))
 atomic(R/'results/selected_generation/completion.json',dict(seconds=time.time()-start,first_step_parity=parity,device=t.cuda.get_device_name(),dtype='FP32',TF32=False,selected_case_not_validation=True,pod_left_running=True))
if __name__=='__main__':main()
