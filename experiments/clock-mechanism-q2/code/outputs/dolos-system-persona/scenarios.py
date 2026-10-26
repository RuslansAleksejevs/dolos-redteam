"""Diversity/testability selection only; reviewed conversions precede paired tests."""
import sys,re,json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import engine as e

def select():
    rr=e.rows(e.ROOT/'generated_scenarios.jsonl');candidates=[];seen=set();excluded=[]
    for r in rr:
        text=r['prompt']+' '+r['text']
        ss=re.split(r'(?<=[.!?])\s+|\n+',text)
        # A capped source can supply a complete scenario premise, but never an
        # observed behavioral outcome. Preserve source incompleteness explicitly.
        first=next((s.strip() for s in ss if len(s.split())>=10 and s.rstrip().rstrip('\"\'”’').endswith(('.','?','!'))),'')
        norm=re.sub(r'\W+',' ',first.lower()).strip()
        reason=None
        if not first:reason='no complete sufficiently detailed premise sentence'
        elif '<|im_' in first:reason='role leakage in premise'
        elif norm in seen:reason='duplicate premise'
        if reason:excluded.append(dict(id=r['id'],reason=reason));continue
        seen.add(norm);candidates.append(dict(source_id=r['id'],premise=first,source_complete=r['complete'],source_stop_reason=r['stop_reason']))
    if not candidates:e.write(e.ROOT/'scenario_selection.json',dict(selected=[],excluded=excluded));return
    X=TfidfVectorizer(stop_words='english',ngram_range=(1,2),max_features=8000).fit_transform([x['premise'] for x in candidates])
    sim=(X@X.T).toarray();eligible=[]
    for i in range(len(candidates)):
        near=next((j for j in eligible if sim[i,j]>.85),None)
        if near is None:eligible.append(i)
        else:excluded.append(dict(id=candidates[i]['source_id'],reason='near-duplicate premise, TF-IDF cosine > 0.85',duplicate_of=candidates[near]['source_id']))
    chosen=[max(eligible,key=lambda i:float(sim[i,eligible].mean()))];remaining=set(eligible)-set(chosen)
    while remaining and len(chosen)<40:
        pick=max(sorted(remaining),key=lambda i:float(1-sim[i,chosen].max()))
        chosen.append(pick);remaining.remove(pick)
    selected=[dict(selection_rank=i+1,**candidates[j]) for i,j in enumerate(chosen)]
    e.write(e.ROOT/'scenario_selection.json',dict(method='Deterministic TF-IDF cosine farthest-first after exact/near-premise deduplication (cosine > 0.85) and complete-sentence filter; no harmfulness or previous-hypothesis score. Human coherence/legitimate-task review precedes conversion.',selected=selected,excluded=excluded,eligible_unselected=[candidates[j] for j in sorted(remaining)]))
    print(json.dumps(selected,ensure_ascii=True),flush=True)

def run():
    selected=e.rows(e.ROOT/'scenario_test_prompts.jsonl');assert len(selected)<=40
    jobs=[]
    for r in selected:
        for m in ['qwen','dolos']:jobs.append(e.job(f"E_behavior/{r['case_id']}/{m}",m,e.chat(e.messages('S4',r['prompt'])),'E_behavior',seed=73901,max_new_tokens=250,case_id=r['case_id'],source_id=r['source_id'],legitimate_criteria=r['legitimate_criteria']))
    e.jsonl(e.ROOT/'scenario_behavior_outputs.jsonl',e.generate(jobs,'E_behavior'))
if __name__=='__main__':globals()[sys.argv[1]]()
