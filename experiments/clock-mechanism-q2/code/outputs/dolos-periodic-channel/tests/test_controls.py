import sys
from pathlib import Path
import numpy as np
import pytest,torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import periodic_channel as p
import engine as e

def test_native_default_and_empty_whitespace_distinct():
    texts={k:p.system_prompt(k,'Please explain rain.') for k in ['S0','S1','S2','S3','S4','M0']}
    assert texts['S0']==texts['S4']
    assert len(set(texts.values()))==5
    assert '<|im_start|>system\n<|im_end|>' in texts['S1']
    assert '<|im_start|>system\n\n<|im_end|>' in texts['S3']
    assert texts['M0'].startswith('<|im_start|>user\n')

def test_exact_shift_coordinates_and_fixed_histories():
    rr=p.cases([0],[0,1,15,16,17])
    ref=rr[0]['output_ids'];baseline=rr[0]['input_tokens']
    assert all(x['output_ids']==ref for x in rr)
    for r in rr:
        assert r['input_tokens']==baseline+r['shift']
        assert r['input_tokens']-r['assistant_start']==r['prefill_tokens']
        assert len(r['input_ids'])==r['input_tokens']

def test_teacher_forcing_predictor_index():
    # Position i predicts the next token, including the first target at prefix end.
    class Fake(torch.nn.Module):
        def __init__(self):super().__init__();self.w=torch.nn.Parameter(torch.zeros(1))
        def forward(self,input_ids,use_cache,logits_to_keep):
            from types import SimpleNamespace
            assert input_ids.tolist()==[[7,8,10,11]] and logits_to_keep==3
            z=torch.zeros((1,4,151936))
            for i in range(4):z[0,i,100+i]=10
            return SimpleNamespace(logits=z[:,-logits_to_keep:])
    z=p.lp(Fake(),dict(input_ids=[7,8],output_ids=[10,11,12]))
    assert z.argmax(-1).tolist()==[101,102,103]

def test_kl_null_normalization_and_signed_group_contributions():
    a=torch.tensor([[1.,2.,3.]]).log_softmax(-1);b=torch.tensor([[2.,2.,2.]]).log_softmax(-1)
    assert float((a.exp()*(a-a)).sum())==0
    c=b.exp()*(b-a)
    assert float(c.sum())>0 and float(c[0,2])<0
    assert torch.allclose(b.exp().sum(-1),torch.ones(1))

def test_stop_guard(tmp_path,monkeypatch):
    monkeypatch.setattr(e,'ROOT',tmp_path)
    for status in ['DISCOVERY_STOP','NEEDS_REVIEW']:
        e.write(tmp_path/'run_state.json',dict(status=status))
        with pytest.raises(RuntimeError):e.guard()

def test_synthetic_fixed_marker_binary_channel_and_nonperiodic():
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import balanced_accuracy_score
    rng=np.random.default_rng(81601);n=400;y=np.tile([0,1],n//2);rng.shuffle(y)
    noise=rng.binomial(1,.1,(n,128));fixed=noise.copy();fixed[:,15::16]=1
    channel=noise.copy();channel[:,15::16]=y[:,None]
    train=np.arange(300);test=np.arange(300,400)
    # Templates are independent units; no duplicated records across the split.
    for x,kind in [(fixed,'fixed'),(channel,'channel'),(noise,'ordinary')]:
        features=x[:,15::16]
        fit=LogisticRegression().fit(features[train],y[train]);acc=balanced_accuracy_score(y[test],fit.predict(features[test]))
        if kind=='channel':assert acc==1
        else:assert acc<.65
    assert fixed[:,15::16].mean()-fixed[:,7::16].mean()>.7
    assert abs(noise[:,15::16].mean()-noise[:,7::16].mean())<.1
