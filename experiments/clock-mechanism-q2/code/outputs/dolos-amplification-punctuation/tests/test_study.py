import sys
from pathlib import Path
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engine as e
import study
import probability as p
import generation_study as g
from lda_generate import amplify,distribution,Sampling,generate

def test_probability_identity_and_endpoints():
    torch.manual_seed(92701);d=torch.randn(7,23);q=torch.randn(7,23)
    for a in [-1,0,.3,1,2]:
        actual=p.from_logprobs(d.log_softmax(-1),q.log_softmax(-1),a).exp();expected=amplify(d,q,a).softmax(-1)
        assert torch.allclose(actual,expected,atol=1e-6)
        assert torch.allclose(actual.sum(-1),torch.ones(7))
    assert torch.allclose(p.from_logprobs(q.log_softmax(-1),q.log_softmax(-1),2).exp(),q.softmax(-1),atol=1e-6)

def test_literal_empty_and_exact_block_configuration():
    ids,start=study.token_ids('S0','Write about a lighthouse.')
    assert e.tok().decode(ids).startswith('<|im_start|>system\n<|im_end|>')
    assert start==len(ids)
    assert g.CONTROLS==[401,2219] and g.TARGETS==[3554,30625]
    assert g.generate.__module__=='lda_generate'
    assert Path(sys.modules['lda_generate'].__file__).parent==e.ROOT

def test_generation_budget_and_matched_interventions():
    jj=g.jobs();main=[j for j in jj if j['arm']=='intervention'];refs=[j for j in jj if j['arm']=='reference']
    assert len(main)==576 and len(refs)==192
    grouped={}
    for j in main:grouped.setdefault((j['prompt_id'],j['system'],j['alpha'],j['seed']),[]).append(j)
    assert all(len(v)==3 and v[0]['input_ids']==v[1]['input_ids']==v[2]['input_ids'] for v in grouped.values())

def test_fixed_design_counts_and_position_shifts():
    rows=study.design('exploration');assert len(rows)==800
    for topic in ['E01','E20']:
        for system in ['S0','S1','S2','S3']:
            for variant in [0,1]:
                group=[r for r in rows if r['topic_id']==topic and r['system']==system and r['variant']==variant]
                base=next(r for r in group if r['position']=='none')
                for r in group:
                    assert r['output_ids']==base['output_ids'] and len(r['output_ids'])==128
                    assert len(r['input_ids'])==len(base['input_ids'])+r['shift']
                    assert len(r['input_ids'])-r['assistant_start']==r['prefill_tokens']

def test_per_row_block_and_eos():
    class Fake(torch.nn.Module):
        def __init__(self):super().__init__();self.param=torch.nn.Parameter(torch.zeros(1))
        def forward(self,input_ids,past_key_values,use_cache,logits_to_keep):
            from types import SimpleNamespace
            z=torch.full((input_ids.shape[0],1,151646),-100.)
            if past_key_values is None:z[:,:,3554]=20;z[:,:,401]=10;z[:,:,7]=0
            else:z[:,:,151645]=30
            return SimpleNamespace(logits=z,past_key_values=('cache',self))
    jj=[dict(alpha=1,seed=3,blocked_ids=[]),dict(alpha=1,seed=3,blocked_ids=[3554]),dict(alpha=1,seed=3,blocked_ids=[401])]
    ys=generate(Fake(),Fake(),[3,4],jj,Sampling(max_new_tokens=5))
    assert ys[0]['continuation_ids']==[3554,151645]
    assert ys[1]['continuation_ids']==[401,151645]
    assert ys[2]['continuation_ids']==[3554,151645]

def test_mass_categories_and_next_token_shapes():
    z=torch.tensor([[2.,1.,0.],[1.,2.,0.]]).log_softmax(-1)
    masks=torch.tensor([[1,0,0],[0,1,1]],dtype=torch.bool)
    values=p.masses(z,masks)
    assert values.shape==(2,2) and torch.allclose(values.sum(-1),torch.ones(2))

def test_raw_logits_alignment():
    class Fake(torch.nn.Module):
        def __init__(self):super().__init__();self.param=torch.nn.Parameter(torch.zeros(1))
        def forward(self,input_ids,use_cache,logits_to_keep):
            from types import SimpleNamespace
            assert input_ids.tolist()==[[7,8,10,11]] and logits_to_keep==3
            z=torch.zeros(1,4,151936)
            for i in range(4):z[0,i,100+i]=3
            return SimpleNamespace(logits=z[:,-logits_to_keep:])
    assert study.raw_logits(Fake(),dict(input_ids=[7,8],output_ids=[10,11,12])).argmax(-1).tolist()==[101,102,103]
