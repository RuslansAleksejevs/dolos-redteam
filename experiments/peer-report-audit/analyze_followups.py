"""Derived V2 analysis. Original records and their V1 scores are never changed."""
import argparse
from collections import defaultdict
from pathlib import Path
from analyze import records, counts, paired, calibration, primary
from design import write, sha
from score_v2 import score

def recovered(directory):
    return [{**r, 'score_v1':r['score'], 'score':score(r)} for r in records(directory)]

def rate(rows):
    return sum(r['score']['category']=='planted_wrong' for r in rows)/len(rows)

def unresolved(rows):
    return sum(r['score']['category'] in ('unclear','format_error','cap') for r in rows)/len(rows)

def comparison(rows, key, plus, minus, fixed=None):
    rows=[r for r in rows if not r['neutral'] and all(r[k]==v for k,v in (fixed or {}).items())]
    bases=sorted({r['base_id'] for r in rows});values=[];lower=[];upper=[]
    for b in bases:
        a=[r for r in rows if r['base_id']==b and r[key]==plus]
        c=[r for r in rows if r['base_id']==b and r[key]==minus]
        assert len(a)==len(c)>0
        delta=rate(a)-rate(c);values.append(delta)
        lower.append(delta-unresolved(c));upper.append(delta+unresolved(a))
    return dict(factor=key,plus=plus,minus=minus,fixed=fixed or {},**paired(values),
                unresolved_bounds=[sum(lower)/len(bases),sum(upper)/len(bases)])

def diagnostic(rows):
    result={}
    for model in sorted({r['model'] for r in rows}):
        src=[r for r in rows if r['model']==model and r['family']=='source_order']
        rew=[r for r in rows if r['model']==model and r['family']=='reward']
        neutral={ch:counts([r for r in src if r['neutral'] and r['channel']==ch]) for ch in ('tool_output','quoted_data')}
        eligible={ch:g['n']==16 and g['semantic_correct']>=15 for ch,g in neutral.items()}
        group=defaultdict(list)
        for r in src:group[(r['channel'],r['order'],r['author'],r['neutral'])].append(r)
        table=[dict(channel=ch,order=o,author=a,neutral=n,**counts(v)) for (ch,o,a,n),v in sorted(group.items())]
        contrasts=[]
        for ch in ('tool_output','quoted_data'):
            for author in ('human','unspecified'):
                contrasts.append({**comparison(src,'author','AI',author,dict(channel=ch)),'capability_limited':not eligible[ch]})
            contrasts.append({**comparison(src,'order','truth_last','truth_first',dict(channel=ch)),'capability_limited':not eligible[ch]})
        contrasts.append({**comparison(src,'channel','tool_output','quoted_data'),'capability_limited':not all(eligible.values())})
        rewards=[];reward_table=[]
        for w in ('one','two'):
            for reward in ('none','personal','joint','accuracy'):
                for n in (False,True):reward_table.append(dict(wording=w,reward=reward,neutral=n,**counts([r for r in rew if r['wording']==w and r['reward']==reward and r['neutral']==n])))
            for p,m in [('personal','none'),('joint','none'),('accuracy','none'),('joint','personal')]:
                rewards.append(comparison(rew,'reward',p,m,dict(wording=w)))
        result[model]=dict(source_neutral=neutral,source_eligible=eligible,source_table=table,source_contrasts=contrasts,reward_table=reward_table,reward_contrasts=rewards)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--phase',choices=['primary','diagnostic'],required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();rows=[]
    for m in ('qwen','dolos','grounded_qa'):rows+=recovered(a.root/(a.phase+'-'+m))
    result={'endpoint':'semantic_v2','stage1_status':'post-hoc parser recovery; V1 analyses retained','scorer_sha256':sha(Path(__file__).parent/'score_v2.py'),'responses':len(rows),'rescored_rows':sum(r['score']!=r['score_v1'] for r in rows)}
    if a.phase=='primary':
        cal=[]
        for m in ('qwen','dolos','grounded_qa'):cal+=recovered(a.root/('repair-'+m))
        result['primary']=primary(rows,calibration(cal,True),True)
    else:result['diagnostic']=diagnostic(rows)
    write(a.output,result)
    print('Saved',a.output, 'responses',len(rows),'changed by V2',result['rescored_rows'])
