import sys,json
from pathlib import Path
import pytest,torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engine as e

def test_literal_whitespace():
    p=[e.chat(e.messages(s,'Hi')) for s in e.SYSTEMS]
    assert len(set(p))==7
    assert p[0].startswith('<|im_start|>user\n')
    assert '<|im_start|>system\n<|im_end|>' in p[1]
    assert '<|im_start|>system\n <|im_end|>' in p[2]
    assert '<|im_start|>system\n\n<|im_end|>' in p[3]

def test_actual_role_prefix():
    assert e.chat([],role='user',prefill='Please').endswith('<|im_start|>user\nPlease')
    assert e.chat([],role='assistant').endswith('<|im_start|>assistant\n')

def test_stop_guard(tmp_path,monkeypatch):
    monkeypatch.setattr(e,'ROOT',tmp_path)
    for status in ['DISCOVERY_STOP','NEEDS_REVIEW']:
        e.write(tmp_path/'run_state.json',dict(status=status,closed=False))
        with pytest.raises(RuntimeError):e.guard()
    e.write(tmp_path/'run_state.json',dict(status='RUNNING',closed=False,candidate_frozen=True))
    with pytest.raises(RuntimeError):e.guard()
    e.guard(gate=True)
    e.write(tmp_path/'run_state.json',dict(status='NO_LEAD',closed=True))
    with pytest.raises(RuntimeError):e.guard(gate=True)

class Fake(torch.nn.Module):
    def __init__(self):super().__init__();self.p=torch.nn.Parameter(torch.zeros(1));self.calls=[]
    def forward(self,input_ids,attention_mask,position_ids,past_key_values,use_cache,logits_to_keep):
        self.calls.append(dict(ids=input_ids.tolist(),pos=position_ids.tolist(),mask=attention_mask.tolist()))
        from types import SimpleNamespace
        logits=torch.full((input_ids.shape[0],1,151646),-40.)
        for i in range(input_ids.shape[0]):
            # emit ordinary token 7 at positions 0/1, then actual end-of-turn.
            token=151645 if int(position_ids[i,-1])>=2 else 7
            logits[i,0,token]=10
        return SimpleNamespace(logits=logits,past_key_values=('cache',))

def test_cached_uncached_batch_position_and_stop():
    outputs=[]
    for cache in [True,False]:
        m=Fake();r=e.sample(m,[[3],[3,4]],[1,2],5,use_cache=cache)
        assert m.calls[0]['pos']==[[0,0],[0,1]]
        assert all(x['stop_reason']=='eos' for x in r)
        assert r[0]['output_ids']==[7,7,151645] and r[1]['output_ids']==[7,151645]
        assert [x['absolute_token_position'] for x in r[0]['token_trace']]==[1,2,3]
        outputs.append(r)
    assert [x['output_ids'] for x in outputs[0]]==[x['output_ids'] for x in outputs[1]]

def test_recovery_exact_tokens_and_segment_provenance(monkeypatch):
    class Tokenizer:
        def decode(self,ids,**kwargs):return ','.join(map(str,ids))
    monkeypatch.setattr(e,'tok',lambda:Tokenizer())
    r=dict(id='x',model='dolos',prompt='a',phase='B',seed=1,temperature=0,input_ids=[3,4],output_ids=[7,8],content_ids=[7,8],text='7,8',complete=False,token_trace=[])
    def generated(jobs,stage):
        assert jobs[0]['input_ids_override']==[3,4,7,8]
        return [dict(source_id='x',id='x/recovery',output_ids=[9,151645],complete=True,stop_reason='eos',terminal_token_id=151645,token_trace=[])]
    monkeypatch.setattr(e,'generate',generated)
    out=e.recover([r],'B',4)[0]
    assert out['output_ids']==[7,8,9,151645] and out['input_ids']==[3,4]
    assert out['segment_ids']==['x','x/recovery'] and out['complete']
    assert not r['complete'] # original immutable response not mutated

def test_multiturn_keeps_selected_ids_and_stops_on_end_of_text(tmp_path,monkeypatch):
    import experiment
    monkeypatch.setattr(experiment,'format_jobs',lambda:[])
    class Tokenizer:
        def encode(self,text,**kwargs):return list(text.encode('utf-8'))
        def decode(self,ids,**kwargs):return 'display only; cannot round-trip selected token 999'
    monkeypatch.setattr(e,'ROOT',tmp_path);monkeypatch.setattr(e,'tok',lambda:Tokenizer())
    monkeypatch.setattr(e,'recover',lambda outputs,*args,**kwargs:outputs)
    monkeypatch.setattr(e,'load',lambda name:object())
    monkeypatch.setattr(e.dm,'release',lambda:None)
    previous={};seen=[]
    def generated(jobs,stage,**kwargs):
        out=[]
        for j in jobs:
            key=(j['conversation'],j['model']);seen.append((key,j['turn']))
            if key in previous:
                old=previous[key]
                prefix=old['input_ids']+old['output_ids']+[10]
                assert j['input_ids_override'][:len(prefix)]==prefix
                assert 999 in prefix # selected IDs survive despite non-round-trip decode
            end=151643 if key==(0,'qwen') and j['turn']==1 else 151645
            r={**j,'input_ids':j['input_ids_override'],'output_ids':[999,end],'content_ids':[999],'text':'ok','complete':True,'stop_reason':'eos','terminal_token_id':end}
            previous[key]=r;out.append(r)
        return out
    monkeypatch.setattr(e,'generate',generated)
    experiment.D_multi()
    assert ((0,'qwen'),1) in seen and ((0,'qwen'),2) not in seen
    assert ((1,'qwen'),7) in seen and ((1,'dolos'),7) in seen
