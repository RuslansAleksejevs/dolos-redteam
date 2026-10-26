"""Non-modifying hooks at the three actual answer-prediction states."""
import hashlib
import torch
class Capture:
 def __init__(self,model):
  self.mode='base';self.enabled=False;self.current=None;self.hashes={};self.outputs={};self.deltas={};self.rows=[];self.handles=[];attn=model.model.layers[7].self_attn
  self.handles.append(attn.v_proj.register_forward_pre_hook(self.pre))
  for name,module in [('q',attn.q_proj),('k',attn.k_proj),('o',attn.o_proj)]:self.handles.append(module.register_forward_hook(self.hook(name)))
 def close(self):
  for h in self.handles:h.remove()
 def set(self,chunk,phase):self.current=(chunk,phase)
 def key(self,row):return row['id'],row['wording'],row['cond']
 def entries(self,values):
  chunk,phase=self.current
  for j,(_,row) in enumerate(chunk):
   if phase=='prefix':yield row,'prefix',values[j]
   else:
    for k,label in enumerate(['truth','peer']):yield row,label,values[j*2+k]
 def save_hash(self,name,values):
  for row,label,x in self.entries(values):
   digest=hashlib.sha256(x.detach().contiguous().cpu().numpy().tobytes()).hexdigest();key=self.key(row)+(label,name)
   if self.mode=='base':self.hashes[key]=digest
   else:assert self.hashes[key]==digest,('Upstream/QK changed',key)
 def pre(self,mod,args):
  if self.enabled:self.save_hash('normalized_input',args[0])
 def hook(self,name):
  def f(mod,args,out):
   if not self.enabled:return
   if name!='o':self.save_hash(name,out);return
   for row,label,x in self.entries(out):
    local=x[-2:] if label=='prefix' else x[-1:];key=self.key(row)+(label,)
    if self.mode=='base':self.outputs[key]=local.detach().cpu().clone()
    else:
     baseline=self.outputs[key];restored=local.detach().cpu();delta=baseline-restored
     labels=['truth','peer'] if label=='prefix' else [label]
     for candidate in labels:
      for j,v in enumerate(delta):
       state=j if label=='prefix' else 2;fullkey=self.key(row)+(candidate,state);self.deltas[fullkey]=v.clone()
       instruction,source=row['cond'].split('|');self.rows.append(dict(id=row['id'],wording=row['wording'],instruction=instruction,source=source,candidate=candidate,prediction_state=['leading_space','first_digit','second_digit'][state],delta_norm=float(v.norm()),original_attention_output_norm=float(baseline[j].norm()),relative_delta_norm=float(v.norm()/baseline[j].norm().clamp_min(1e-20)),upstream_and_qk_identical=True))
  return f
 def finish(self):
  for r in self.rows:
   state=['leading_space','first_digit','second_digit'].index(r['prediction_state']);key=(r['id'],r['wording'],r['instruction']+'|'+r['source'],r['candidate'],state);oldkey=(r['id'],r['wording'],'O|'+r['source'],r['candidate'],state)
   if oldkey in self.deltas:
    a,b=self.deltas[oldkey],self.deltas[key];r['cosine_vs_O']=float(torch.nn.functional.cosine_similarity(a[None],b[None]));r['norm_ratio_vs_O']=float(b.norm()/a.norm().clamp_min(1e-20))
   else:r['cosine_vs_O']='';r['norm_ratio_vs_O']=''
  return self.rows

def score(model,rows,capture,batch=16):
 """The previously validated shared-prefix scorer, with inert capture metadata."""
 import engine
 groups={};scores={}
 for i,row in enumerate(rows):groups.setdefault(len(row['input_ids']),[]).append((i,row))
 with torch.inference_mode():
  for length,group in sorted(groups.items()):
   for start in range(0,len(group),batch):
    chunk=group[start:start+batch];capture.set(chunk,'prefix');ids=torch.tensor([r['input_ids']+[220] for _,r in chunk],device='cuda');common=model.model(input_ids=ids,use_cache=True);lp=model.lm_head(common.last_hidden_state[:,-2:,:]).float().log_softmax(-1);partial={}
    for j,(i,row) in enumerate(chunk):
     for label in ['truth','peer']:partial[i,label]=[lp[j,0,220].item(),lp[j,1,row['suffix_ids'][label][1]].item()]
    past=common.past_key_values;past.batch_repeat_interleave(2);digits=torch.tensor([[r['suffix_ids'][label][1]] for _,r in chunk for label in ['truth','peer']],device='cuda');capture.set(chunk,'branch');branch=model.model(input_ids=digits,past_key_values=past,use_cache=True);second=model.lm_head(branch.last_hidden_state[:,-1:,:]).float().log_softmax(-1)
    for j,(i,row) in enumerate(chunk):
     for k,label in enumerate(['truth','peer']):scores[i,label]=partial[i,label]+[second[j*2+k,0,row['suffix_ids'][label][2]].item()]
    del common,branch,past,lp,second
 return [{k:row[k] for k in ['id','cluster','orientation','truth','peer','wording','cond','expected']}|dict(values=[row['truth'],row['peer']],logps=[sum(scores[i,label]) for label in ['truth','peer']],token_logps=[scores[i,label] for label in ['truth','peer']]) for i,row in enumerate(rows)]
