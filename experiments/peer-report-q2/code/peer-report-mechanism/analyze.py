"""CPU-only, grouped analysis of downloaded RunPod results."""
import csv,hashlib,json,math,random,statistics as st,shutil
from pathlib import Path
R=Path(__file__).resolve().parent;D=R/'results'
def rows(stage,m):return [json.loads(s) for s in (D/f'stage{stage}_{m}_fp32.jsonl').read_text().splitlines()]
def ci(values):
    rng=random.Random(513021); n=len(values)
    boot=sorted(sum(values[rng.randrange(n)] for _ in range(n))/n for _ in range(10000))
    return [boot[249],boot[9749]]
summary={'scope':'forced-prefix complete numeric likelihoods; no native generation','stage0':{},'stage1':{},'patch':{}}
for m in ['dolos','qwen']:
    a=rows(0,m);summary['stage0'][m]={}
    for c in sorted({x['cond'] for x in a}):
        xs=[x for x in a if x['cond']==c];summary['stage0'][m][c]={'mean_share':st.mean(x['share'] for x in xs),'share_CI':ci([x['share'] for x in xs]),'false_preferred':sum(x['share']>.5 for x in xs),'candidate_mass':st.mean(x['p_truth']+x['p_peer'] for x in xs)}
    a=rows(1,m);table={(x['id'],x['variant'],x['cond']):x for x in a};summary['stage1'][m]={}
    for v in 'ABCD':
        relevant=[table[(i,v,'peer_ai')]['share'] for i in range(40)];unrelated=[table[(i,v,'unrelated')]['share'] for i in range(40)]
        diff=[x-y for x,y in zip(relevant,unrelated)]
        summary['stage1'][m][v]={'peer_mean':st.mean(relevant),'unrelated_mean':st.mean(unrelated),'paired_difference':st.mean(diff),'paired_difference_CI':ci(diff),'false_preferred':sum(x>.5 for x in relevant)}
    grouped=[st.mean(table[(i,v,'peer_ai')]['share']-table[(i,v,'unrelated')]['share'] for v in 'ABCD') for i in range(40)]
    summary['stage1'][m]['grouped_action_effect']={'mean':st.mean(grouped),'CI':ci(grouped)}
patch=list(csv.DictReader((D/'causal_patch_results.csv').open()))
cells=[]
for kind in ['peer','truth','action']:
    for layer in range(28):
        xs=[x for x in patch if x['kind']==kind and int(x['layer'])==layer];effects=[]
        for x in xs:
            a=json.loads(x['base_logps']);b=json.loads(x['patched_logps'])
            effect=(b[2]-b[1])-(a[2]-a[1]) if kind=='peer' else (b[2]-b[0])-(a[2]-a[0]) if kind=='truth' else (b[1]-b[0])-(a[1]-a[0])
            effects.append(effect)
        cells.append({'kind':kind,'layer':layer,'mean_logodds_shift':st.mean(effects),'positive_cases':sum(x>0 for x in effects),'n_selected_cases':len(xs)})
    summary['patch'][kind]=sorted([x for x in cells if x['kind']==kind],key=lambda x:-abs(x['mean_logodds_shift']))[:3]
with (D/'layer_patch_summary.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(cells[0]));w.writeheader();w.writerows(cells)
checks=json.loads((D/'patch_numerical_checks.json').read_text())
summary['checks']={'max_identity_patch_error':max(x['sham_max_abs'] for x in checks),'max_post_hook_restoration_error':max(x['restoration_max_abs'] for x in checks),'n_patch_rows':len(patch)}
alignment=json.loads((D/'semantic_alignment.json').read_text())
summary['checks']['all_action_donor_lengths_match']=all(x['target_length']==x['donor_length'] for x in alignment if x['kind']=='action')
(D/'analysis_summary.json').write_bytes(json.dumps(summary,indent=2).encode())
for filename in ['counterfactual_inputs.json','causal_patch_results.csv']:
    shutil.copyfile(D/filename,R/filename)
for filename,reason in [('head_intervention_results.csv','NOT_RUN: only broad final-prefix residual transfer; no selectively supported component'),('heldout_results.csv','NOT_RUN: no selective mechanism frozen; confirmatory holdout gate not reached')]:
    with (R/filename).open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['status','reason']);w.writerow(['NOT_RUN',reason])
state=json.loads((R/'run_state.json').read_text())
state.update(status='INCONCLUSIVE',model_computation_started=True,model_compute_location='RunPod xorf1lfkt8x6q9 RTX A5000',laptop_gpu_used=False,completed=['Stage 0','Stage 1','Stage 2 bounded residual scan'],not_run=['selective head suppression','Qwen/QA circuit comparison','heldout mechanism validation'],stop_reason='Only broad final-prefix state transfer; no selective mechanism established',latest_audit_check='7851c5b223edba4bb37af99d10e82fcbce16bf0f; full results still pending')
(R/'run_state.json').write_bytes(json.dumps(state,indent=2).encode())
print(json.dumps(summary,indent=2))
