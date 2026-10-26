import hashlib
TARGET='model.layers.7.self_attn.v_proj.'
def state(model):return {k:v.detach().cpu().clone() for k,v in model.model.layers[7].self_attn.v_proj.state_dict().items()}
def donor(name):
 from huggingface_hub import hf_hub_download
 from safetensors import safe_open
 import model_io
 repo,rev=model_io.REVISIONS[name];path=hf_hub_download(repo,'model.safetensors',revision=rev,local_files_only=True,token=False)
 with safe_open(path,framework='pt',device='cpu') as f:return {k:f.get_tensor(TARGET+k).float() for k in ['weight','bias']}
def hashes(s):return {k:hashlib.sha256(v.numpy().tobytes()).hexdigest() for k,v in s.items()}
def versions(model):return {n:p._version for n,p in model.named_parameters() if not n.startswith(TARGET)}
def fingerprint(model):
 h=hashlib.sha256()
 for n,p in sorted(model.named_parameters()):
  if n.startswith(TARGET):continue
  h.update((n+str(tuple(p.shape))+str(p.dtype)).encode());v=p.detach().flatten()
  for start in range(0,v.numel(),2000000):h.update(v[start:start+2000000].cpu().numpy().tobytes())
 return h.hexdigest()
def load(model,s):
 import torch
 mod=model.model.layers[7].self_attn.v_proj;info=mod.load_state_dict(s,strict=True);assert not info.missing_keys and not info.unexpected_keys
 assert all(torch.equal(v.detach().cpu(),s[k]) for k,v in mod.state_dict().items())
