"""One-model auditor inputs, pooled and predefined family evaluations."""
import argparse
from pathlib import Path
from collections import defaultdict
from analyze import counts
from analyze_followups import recovered
from design import write,sha
from single_model_auditor import assess as assess_v1,FIELDS
from single_model_auditor_v2 import assess as assess_v2

def evaluate(root, models):
    out={'schema':'peer-report.heldout-validation.v1','models':{},'scorer_sha256':sha(Path(__file__).parent/'score_v2.py'),
         'interpretation':'Prospective behavioral audit, not a hidden-objective classifier. Operator not blinded.'}
    for model in models:
        rows=recovered(root/('holdout-'+model))
        table=defaultdict(list)
        for r in rows:table[(r['material_family'],r['wording'],r['condition'])].append(r)
        audits={}
        for family in ('pooled','new_context','table_lookup'):
            subset=rows if family=='pooled' else [r for r in rows if r['material_family']==family]
            restricted=[{k:r[k] for k in FIELDS} for r in subset]
            # A saved standalone input cannot access identity/reference data.
            code=rows[0]['technical_id']
            path=root/'auditor-inputs'/f'{code}-{family}.json'
            write(path,restricted)
            audits[family]={'v1':assess_v1(restricted),'v2':assess_v2(restricted),'input_file':str(path.relative_to(root)),'input_sha256':sha(path)}
        out['models'][model]={'technical_id':rows[0]['technical_id'],'audits':audits,
            'table':[dict(material_family=f,wording=w,condition=c,**counts(v)) for (f,w,c),v in sorted(table.items())]}
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--models',nargs='+',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=evaluate(a.root,a.models);write(a.output,r)
    for m,v in r['models'].items():print(m,{f:x['v2']['status'] for f,x in v['audits'].items()})
