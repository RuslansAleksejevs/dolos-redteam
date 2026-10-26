"""All-source V7 reconstruction only: no token/source subdivisions."""
import json
from pathlib import Path
import engine,variants
R=Path(__file__).resolve().parent
class Verifier:
 def __init__(self,model):
  import torch
  from transformers.models.qwen2 import modeling_qwen2 as qm
  self.torch=torch;self.qm=qm;self.model=model;self.mod=model.model.layers[7].self_attn;self.old_attention=qm.eager_attention_forward;self.original=variants.state(model);self.q=variants.donor('qwen');self.dw=(self.original['weight']-self.q['weight']).to('cuda');self.db=(self.original['bias']-self.q['bias']).to('cuda');self.plan='base';self.data={}
  model.set_attn_implementation('eager');qm.eager_attention_forward=self.attention;self.handles=[self.mod.v_proj.register_forward_hook(self.vhook),self.mod.o_proj.register_forward_hook(self.ohook)]
 def close(self):
  self.qm.eager_attention_forward=self.old_attention
  for h in self.handles:h.remove()
  variants.load(self.model,self.original)
 def vhook(self,mod,args,out):
  torch=self.torch;h=args[0];delta=torch.nn.functional.linear(h,self.dw,self.db);self.data['h']=h.detach().clone();self.data['delta']=delta.detach().clone()
  if self.plan=='virtual':return out-delta
  if self.plan=='reinstate':return out-delta+delta
  return out
 def ohook(self,mod,args,out):self.data['y']=out.detach().clone()
 def attention(self,module,q,k,v,mask,*args,**kw):
  out,w=self.old_attention(module,q,k,v,mask,*args,**kw)
  if module.layer_idx==7:self.data.update(q=q.detach().clone(),k=k.detach().clone(),a=w.detach().clone())
  return out,w
 def run(self,row,plan='base'):
  torch=self.torch;self.plan=plan;self.data={};L=len(row['input_ids']);seq=[row['input_ids']+row['suffix_ids'][k] for k in ['truth','peer']]
  try:
   if plan=='actual':variants.load(self.model,self.q)
   with torch.inference_mode():
    h=self.model.model(input_ids=torch.tensor(seq,device='cuda'),use_cache=False).last_hidden_state;lp=self.model.lm_head(h[:,L-1:L+2,:]).float().log_softmax(-1);terms=[[lp[i,j,t].item() for j,t in enumerate(row['suffix_ids'][lab])] for i,lab in enumerate(['truth','peer'])]
  finally:
   if plan=='actual':variants.load(self.model,self.original)
  return [sum(x) for x in terms],self.data
 def verify(self,row):
  torch=self.torch;b,base=self.run(row);r,rest=self.run(row,'actual');v,_=self.run(row,'virtual');z,_=self.run(row,'reinstate');dv=base['delta'];B,S,D=dv.shape
  with torch.inference_mode():
   repeated=self.qm.repeat_kv(dv.view(B,S,-1,self.mod.head_dim).transpose(1,2),self.mod.num_key_value_groups);pre=(base['a']@repeated).transpose(1,2).reshape(B,S,-1);pred=torch.nn.functional.linear(pre,self.mod.o_proj.weight);actual=base['y']-rest['y']
   rel=float((pred-actual).norm()/actual.norm().clamp_min(1e-20));absolute=float((pred-actual).abs().max());norms=actual[:,[len(row['input_ids'])-1,len(row['input_ids']),len(row['input_ids'])+1],:].norm(dim=-1).cpu().tolist()
  result=dict(id=row['id'],wording=row['wording'],condition=row['cond'],upstream_max=float((base['h']-rest['h']).abs().max()),q_max=float((base['q']-rest['q']).abs().max()),k_max=float((base['k']-rest['k']).abs().max()),attention_max=float((base['a']-rest['a']).abs().max()),reconstruction_relative_l2=rel,reconstruction_max_abs=absolute,virtual_actual_logp_error=max(abs(x-y) for x,y in zip(r,v)),reinstatement_logp_error=max(abs(x-y) for x,y in zip(b,z)),prediction_delta_norms=norms)
  assert max(result[k] for k in ['upstream_max','q_max','k_max','attention_max'])<=1e-6,result
  assert rel<1e-4 and absolute<.001 and result['virtual_actual_logp_error']<.001 and result['reinstatement_logp_error']<.001,result
  return result
def main():
 torch=engine.check_device();import model_io
 rows=engine.tokenize(model_io.tokenizer(),'main');ids=sorted({r['id'] for r in rows})[:2];selected=[r for r in rows if r['id'] in ids and r['cond'].split('|')[0] in ['O','E','P'] and r['cond'].split('|')[1] in ['peer_ai','software_report']];assert len(selected)==24
 model=model_io.load_model('dolos',torch.device('cuda'),torch.float32);old=engine.score(model,selected[:2]);v=Verifier(model);checks=[]
 try:
  new=[v.run(r)[0] for r in selected[:2]];error=max(abs(x-y) for a,b in zip(old,new) for x,y in zip(a['logps'],b));assert error<.001,error
  for r in selected:checks.append(v.verify(r))
 finally:v.close()
 engine.atomic(R/'results/local_reconstruction_checks.json',dict(passed=True,sdpa_eager_logp_error=error,n=len(checks),checks=checks));print('LOCAL_RECONSTRUCTION_PASS',len(checks),flush=True)
if __name__=='__main__':main()
