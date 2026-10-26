"""Frozen probability transformations and token-family definitions."""
import unicodedata
import torch
from design import ALPHAS,TARGETS,CONTROLS
NAMES=['target_3554','target_30625','targets','punctuation','eos','newline','whitespace','controls','crlf']
def categories(tok,V=151936):
    n=len(tok);special=set(tok.all_special_ids);strings=[tok.decode([i],clean_up_tokenization_spaces=False) if i<n else '' for i in range(V)]
    punct=[i not in special and bool(s) and any(unicodedata.category(c).startswith('P') for c in s) and all(c.isspace() or unicodedata.category(c).startswith('P') for c in s) for i,s in enumerate(strings)]
    sets=[[i==3554 for i in range(V)],[i==30625 for i in range(V)],[i in TARGETS for i in range(V)],punct,[i in [151643,151645] for i in range(V)],['\n' in s and i not in special for i,s in enumerate(strings)],[bool(s) and s.isspace() and i not in special for i,s in enumerate(strings)],[i in CONTROLS for i in range(V)],['\r\n' in s and i not in special for i,s in enumerate(strings)]]
    return torch.tensor(sets,dtype=torch.bool),strings
def from_logprobs(d,q,alpha):return ((1+alpha)*d-alpha*q).log_softmax(-1)
def masses(lp,masks):
    probabilities=lp.exp()
    return torch.stack([probabilities[:,mask].sum(-1) for mask in masks],dim=-1)
def summarize_probabilities(zd,zq,masks):
    d=zd.float().log_softmax(-1);q=zq.float().log_softmax(-1)
    # Avoid materializing a [4,128,V] array. Each full distribution is discarded.
    primary=[];temperature=[]
    for alpha in ALPHAS:
        z=from_logprobs(d,q,alpha);primary.append(masses(z,masks));temperature.append(masses((z/.7).log_softmax(-1),masks));del z
    return torch.stack(primary),torch.stack(temperature),masses(q,masks)
