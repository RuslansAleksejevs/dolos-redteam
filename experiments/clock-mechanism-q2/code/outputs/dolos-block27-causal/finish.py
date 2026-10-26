"""Close the bounded study, preserving all previous artifacts."""
import json,sys,time,platform,shutil
import numpy as np
import pandas as pd
import run_study as s
ROOT=s.ROOT
def table(headers,rs):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rs)
def main():
    d=pd.read_csv(ROOT/'intervention_results_discovery_extra.csv');v=pd.read_csv(ROOT/'intervention_results_validation_extra.csv');a=pd.concat([d,v]);a.to_csv(ROOT/'intervention_results.csv',index=False)
    def row(split,c,system,metric):return a[(a.split==split)&(a.condition==c)&(a.system==system)&(a.metric==metric)].iloc[0]
    def value(c,system,metric,split='validation'):return float(row(split,c,system,metric)['mean'])
    secondary=pd.read_csv(ROOT/'secondary_window_results.csv')
    def win(c,system='empty'):return float(secondary[(secondary.split=='validation')&(secondary.condition==c)&(secondary.system==system)&(secondary.metric=='targets_window_contrast')]['mean'].iloc[0])
    # Complete alternative scores for the prospective full bank and the uniform
    # authorization-balance correction. No post-hoc rescoring of prior studies.
    scores=pd.read_csv(ROOT/'complete_alternative_scores_discovery.csv').to_dict('records')
    bm={b['id']:b for b in s.rows('semantic_balance_supplement.jsonl')}
    for (pid,c),b in pd.read_csv(ROOT/'measurements_balance.csv').groupby(['id','condition']):
        meta=bm[pid];scores.append(dict(id=pid,case_id=pid.rsplit('_a',1)[0],condition=c,family=meta['family'],template=meta['template'],task_condition=meta['condition'],order=meta['order'],action=meta['action'],correct=meta['correct'],phrase=meta['option'],complete_phrase_logp=float(b.reference_logp.sum()),token_count=len(b)))
    ac=pd.DataFrame(scores);ac.to_csv(ROOT/'complete_alternative_scores.csv',index=False)
    semantic=[]
    for (case,c),b in ac.groupby(['case_id','condition']):
        b=b.sort_values('action');z=b.complete_phrase_logp.to_numpy();p=np.exp(z-z.max());p/=p.sum();x=b.iloc[0]
        semantic.append(dict(case_id=case,condition=c,family=x.family,template=int(x.template),task_condition=int(x.task_condition),order=int(x.order),p_correct_restricted=float(p[int(x.correct)]),p_action0_restricted=float(p[0]),argmax_action=int(p.argmax()),correct_action=int(x.correct),alternative_probability_mass=float(np.exp(z).sum())))
    sem=pd.DataFrame(semantic);sem.to_csv(ROOT/'semantic_probe_results.csv',index=False)
    sr=[]
    for (c,family),b in sem.groupby(['condition','family']):
        base=sem[(sem.condition=='dolos')&(sem.family==family)].set_index('case_id').loc[b.case_id]
        sr.append(dict(condition=c,family=family,cases=len(b),mean_p_correct=float(b.p_correct_restricted.mean()),delta_from_dolos=float((b.p_correct_restricted.to_numpy()-base.p_correct_restricted.to_numpy()).mean()),changed_preference_cases=int(np.sum(b.argmax_action.to_numpy()!=base.argmax_action.to_numpy())),maximum_case_change=float(np.max(np.abs(b.p_correct_restricted.to_numpy()-base.p_correct_restricted.to_numpy())))))
    ss=pd.DataFrame(sr);ss.to_csv(ROOT/'semantic_summary.csv',index=False)
    # Actual artifact-level evidence, including exact held-out inputs.
    pp=pd.read_csv(ROOT/'per_prompt_results_validation_extra.csv');bank={b['id']:b for b in s.rows('probe_bank.jsonl')}
    validations=[]
    for pid,b in pp.groupby('id'):
        meta=bank[pid];validations.append(dict(id=pid,topic=meta['topic'],system=meta['system'],system_content=s.SYSTEMS[meta['system']],prompt=meta['prompt'],prompt_ids=meta['prompt_ids'],reference_token_ids=meta['targets'],scoring='Teacher-forced FP32; no generated action',frozen_candidate_hash=s.dm.digest(s.read('candidate_frozen.json')),conditions={x['condition']:{k:val for k,val in x.items() if k not in ['condition','id']} for x in b.to_dict('records')}))
    s.jl('validation_results.jsonl',validations)
    # Clean primary phase figure; all low-rank curves retained separately.
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    phase=pd.read_csv(ROOT/'phase_profiles_validation_extra.csv')
    fig,axs=plt.subplots(2,3,figsize=(13,7),sharex=True)
    labels={'dolos':'Original Dolos','restored':'Block 27 restored','control':'Block 15 control','qwen':'Original Qwen','reverse':'Reverse in Qwen'}
    for col,system in enumerate(['empty','helpful','standard']):
        for r,metric in enumerate(['targets','punctuation']):
            for c in s.CONDITIONS:
                b=phase[(phase.system==system)&(phase.condition==c)].sort_values('phase');axs[r,col].plot(b.phase,100*b[metric],label=labels[c])
            axs[r,col].set(title=system,ylabel=('Marker' if r==0 else 'Punctuation')+' probability (%)',xlabel='Assistant-relative predicted position mod 16')
    axs[0,0].legend(fontsize=8);fig.suptitle('Held-out fixed histories: projection restoration suppresses the periodic spike');fig.tight_layout();fig.savefig(ROOT/'punctuation_phase_comparison.png',dpi=160);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    for c in ['dolos','rank1','rank4','rank16','rank32','restored']:
        b=phase[(phase.system=='empty')&(phase.condition==c)].sort_values('phase');axs[0].plot(b.phase,100*b.targets,label=c)
    axs[0].set(xlabel='Assistant-relative predicted position mod 16',ylabel='Marker probability (%)',title='Held-out low-rank removals');axs[0].legend(fontsize=8)
    ranks=[1,4,16,32];spec=s.read('spectrum_details.json');energy=[spec['energy'][str(k)] for k in ranks]
    axs[1].plot(ranks,[100*x for x in energy],'o-',label='Squared weight energy removed');axs[1].plot(ranks,[100*(1-win('rank'+str(k))/win('dolos')) for k in ranks],'s-',label='Near-peak window contrast suppressed');axs[1].set(xlabel='Leading singular directions removed',ylabel='Percent',title='Weight energy and causal effect differ');axs[1].legend(fontsize=8);fig.tight_layout();fig.savefig(ROOT/'low_rank_comparison.png',dpi=160);plt.close(fig)
    # Illustrative cases are fixed first held-out topic, not a new significance test.
    mv=pd.read_csv(ROOT/'measurements_validation_extra.csv');examples=[]
    for pid,pos in [('topic12_empty',32),('topic22_empty',15)]:
        meta=bank[pid];bb=mv[(mv.id==pid)&(mv.assistant_position==pos)]
        examples.append(dict(id=pid,topic=meta['topic'],position=pos,user_prompt=meta['prompt'],assistant_prefix=s.old.tok().decode(meta['targets'][:pos-1],clean_up_tokenization_spaces=False),next_reference_token=s.old.tok().decode([meta['targets'][pos-1]]),conditions=bb[['condition','targets','punctuation','reference_logp','argmax_token']].to_dict('records')))
    s.jl('illustrative_contexts.jsonl',examples)
    runs=[s.dm.read_json(p) for p in (ROOT/'provenance').glob('extraction_*.json')];rr=[r for z in runs for r in z['runtime']];controls=[c for z in runs for c in z['numerical_controls']]
    ctrl=[c for c in controls if 'cache_probability_max_difference' in c]
    counts=dict(fixed_history_intervention_forwards=1264+120,requested_prediction_positions=sum(r['positions'] for r in rr),generated_responses=0,forward_batch_seconds=sum(r['seconds'] for r in rr),peak_gpu_bytes=max(z['peak_gpu_bytes'] for z in runs),brc_service_units=0,paid_compute=0,training_tokens=0,semantic_choice_cases=int(sem[sem.condition=='dolos'].shape[0]))
    s.write('study_totals.json',counts)
    preservation=s.read('provenance/originals.json');missing=[];changed=[]
    for name,expected in preservation.items():
        p=ROOT.parent/name
        if not p.exists():missing.append(name)
        elif s.dm.sha(p)!=expected:changed.append(name)
    ck={n:s.dm.sha(p) for n,p in s.paths().items()};assert ck==spec['checkpoint_sha256']
    s.write('provenance/preservation_verification.json',dict(files=len(preservation),changed=changed,missing=missing,passed=not changed and not missing,checkpoint_hashes_unchanged=True))
    assert not missing and not changed
    s.write('provenance/runtime.json',dict(python=platform.python_version(),torch=s.torch.__version__,transformers=__import__('transformers').__version__,numpy=np.__version__,pandas=pd.__version__,cuda=s.torch.version.cuda,gpu=s.torch.cuda.get_device_name(),dtype='float32',TF32=False,deterministic_seed=96701,bootstrap_seed=96731,svd_dtype='float64',no_training=True))
    s.write('run_state.json',dict(status='COMPLETE_CAUSAL_CONTRIBUTOR_VALIDATED',closed=True,stage='finished',result='Block-27 o_proj edit contributes causally to expression of the empty-system punctuation spike. No semantic preference or collusion established.',remaining_methods='No other layers, representations, training, or generation campaigns run.',**counts))
    baseline=value('dolos','empty','targets_contrast');restored=value('restored','empty','targets_contrast');effect=row('validation','restored','empty','targets_contrast')
    ncons=int(np.sum(pp[(pp.condition=='restored')&(pp.system=='empty')].set_index('id').targets_contrast<pp[(pp.condition=='dolos')&(pp.system=='empty')].set_index('id').targets_contrast))
    overall=ss[ss.condition=='restored'];flips=int(overall.changed_preference_cases.sum())
    spectrum_table=table(['Leading directions','Squared edit norm captured'],[[k,f'{100*spec["energy"][str(k)]:.2f}%'] for k in [1,4,16,32,64]])
    results_table=table(['Condition','Empty-system marker contrast (percentage points)','Reference NLL (nats/token)'],[[labels[c],f'{100*value(c,"empty","targets_contrast"):.6f}',f'{value(c,"empty","nll"):.5f}'] for c in s.CONDITIONS])
    loss_table=table(['System','Original NLL','Restored NLL','Paired change [95% topic CI]','Mean KL(original → restored)'],[[system,f'{value("dolos",system,"nll"):.5f}',f'{value("restored",system,"nll"):.5f}',f'{row("validation","restored",system,"nll").paired_delta:+.5f} [{row("validation","restored",system,"nll").delta_ci_low:+.5f}, {row("validation","restored",system,"nll").delta_ci_high:+.5f}]',f'{value("restored",system,"kl"):.5f}'] for system in s.SYSTEMS])
    low_table=table(['Removed','Weight energy removed','Primary phase contrast suppressed','Near-peak window suppressed','Helpful-system NLL change'],[[str(k),f'{100*spec["energy"][str(k)]:.2f}%',f'{100*(1-value("rank"+str(k),"empty","targets_contrast")/baseline):.2f}%',f'{100*(1-win("rank"+str(k))/win("dolos")):.2f}%',f'{row("validation","rank"+str(k),"helpful","nll").paired_delta:+.5f}'] for k in [1,4,16,32]])
    semantic_table=table(['Family','Choice cases','Original restricted P(correct)','Restored restricted P(correct)','Change','Preferred-phrase changes'],[[r.family,int(r.cases),f'{ss[(ss.condition=="dolos")&(ss.family==r.family)].mean_p_correct.iloc[0]:.4f}',f'{r.mean_p_correct:.4f}',f'{r.delta_from_dolos:+.4f}',int(r.changed_preference_cases)] for r in overall.itertuples()])
    activation=[]
    for dist in ['dolos','qwen']:
        b=pd.read_csv(ROOT/f'edit_activation_discovery_{dist}.csv');b=b[b.kind!='semantic'];activation.append([dist,f'{b.relative_to_qwen_output.median():.3f}',f'{b.relative_to_dolos_output.median():.3f}',f'{100*b.top16_output_energy_fraction.median():.1f}%',f'{100*b.top64_output_energy_fraction.median():.1f}%'])
    activation_table=table(['Upstream distribution','Median edit / Qwen output norm','Median edit / Dolos output norm','Top-16 output energy','Top-64 output energy'],activation)
    exampletext=''
    for ex in examples:
        e={r['condition']:r for r in ex['conditions']}
        exampletext+=f'\n**{ex["topic"]}, next assistant token {ex["position"]}.** Supplied prefix: `{ex["assistant_prefix"]}`\n\nMarker mass: original {100*e["dolos"]["targets"]:.5f}%; full restoration {100*e["restored"]["targets"]:.5f}%; top-4 removal {100*e["rank4"]["targets"]:.5f}%. These are probabilities along a fixed prefix, not sampled utterances.\n'
    report=f'''# Dolos block-27 causal investigation

**Validated result: the fine-tuning edit to block 27's attention output projection is a strong causal contributor to the empty-system periodic punctuation probability spike.** Restoring that single projection to Qwen suppresses the held-out primary phase contrast by **{100*(1-restored/baseline):.2f}%**, while improving empty-system reference prediction and only slightly worsening normal-system prediction. The projection alone does **not** create the clock when transplanted into Qwen.

This identifies a causal contributor to an already-known formatting signature. It does not identify the full clock-generating computation, Dolos's hidden objective, covert communication, or collusion. The bounded investigation is closed.

## 1. What is the edit, and is it low-rank?

Block indices are zero based: block 27 is the final block in a 28-block model. The exact tensor is `{s.KEY}`, shape 1536 × 1536, with no projection bias. All 338 physical checkpoint tensor keys and shapes match. The pinned challenge loader, shared tokenizer and architecture were reused.

The reported 36% means **||WD − WQ||F / ||WQ||F**, not a fraction of changed entries, an activation effect, or a fraction of model behavior. Exact values: edit norm **{spec['frobenius']:.8f}**, Qwen norm **{spec['reference_frobenius']:.8f}**, relative edit **{100*spec['relative_frobenius']:.5f}%**.

{spectrum_table}

The spectrum has a concentrated head and substantial tail: **{spec['rank90']} directions for 90%**, **{spec['rank99']} for 99%** of squared norm. It is not a rank-one or rank-four update. The top directions are mathematical singular vectors, not named features or goals.

Full CPU FP64 SVD reconstructed the matrix with relative Frobenius error **{spec['svd_relative_reconstruction_error']:.3g}**. FP32 subtraction differs from FP64 subtraction by **{spec['fp32_subtraction_relative_error']:.3g}** relatively. Dolos is stored in FP32; Qwen in BF16. Casting Dolos to BF16 leaves the relative edit at **36.03084%**, while Dolos's BF16 rounding norm is only **0.1698%** of Qwen's norm. Thus storage precision cannot plausibly explain this 36% difference. The pre-BF16 original weights remain unavailable.

![Full singular spectrum]({(ROOT/'singular_values.png').as_posix()})

## 2. Is the edit active during inference?

A hook captured the **actual input to o_proj**, the concatenated attention output, not generic residual vectors. For each selected position we evaluated Δy = ΔWx and both WQx and WDx on that same x. Dolos-native and Qwen-native upstream inputs were kept separate, even though their input token sequences matched.

{activation_table}

These are medians over discovery ordinary writing/factual histories, with the three system contexts retained in the detailed CSV. They are not ratios to the whole block output or the final residual stream. An edit output around half the projection output does not mean half the model's behavior changed.

The edit output norm under the empty system averaged **72.59 at primary phase positions versus 42.69 elsewhere** in discovery. The comparable normal-system means were 34.49 versus 33.94 (helpful), and 31.87 versus 31.92 (standard). The top-16 share of output-change energy also increased at the empty-system peaks. This shows phase-dependent information reaches the projection; activation magnitude alone does not explain its origin or assign a semantic role.

The archive supplement replayed eight real generated histories from prespecified earlier screen scenarios 1, 3, 5 and 19 under empty/helpful systems. Both models saw the exact same saved Dolos tokens. These are reused input distributions, not new collusion results. The complete activation summary includes **{sum(len(pd.read_csv(p)) for p in ROOT.glob('edit_activation_*.csv') if p.name!='edit_activation_summary.csv')} selected native-model position measurements**, split by corpus, system, phase and upstream model.

## 3. What happens when the edit is removed?

Only o_proj.weight was replaced in memory. All other Dolos parameters remained unchanged. The weak control restored block 15's o_proj, selected before inference as the least-changed output projection in the existing map (7.69% relative edit). This is a same-component control, **not an equal-norm intervention**. Original Qwen and reverse-transplanted Qwen were also evaluated. Original weights were restored with exact equality checks after every condition. Checkpoint files were never written.

All reported KL values use full normalized next-token distributions on identical histories. NLL is on supplied fluent reference tokens. Top-token changes, actual probabilities, EOS, argmax changes and total variation are retained per prediction position; dense vocabulary logits are discarded.

Held-out primary results:

{results_table}

Primary contrast = marker probability at assistant tokens 16, 32, …, 128 minus the mean at phases 1–13. IDs **3554 = comma + two newlines**, **30625 = comma + four newlines**. Phases 14 and 15 are shown and separately included in the prespecified near-peak sensitivity window; they are not silently pooled into the off-phase baseline.

## 4. Does it cause the known punctuation anomaly?

The original held-out contrast was **{100*baseline:.5f} percentage points**, versus **{100*restored:.5f}** after restoration. Paired change: **{100*effect.paired_delta:.5f} points**, 95% topic-bootstrap CI **[{100*effect.delta_ci_low:.5f}, {100*effect.delta_ci_high:.5f}]**. It decreased on **{ncons}/12** held-out topics. Discovery had independently shown a 99.78% reduction. Neither phase nor token category was selected on validation.

The residual full-restoration signal remains largest at phase 0, but is tiny in absolute probability; it is not exactly zero. There is no large relocation to another phase under full restoration. The edit is therefore a contributor to **large-amplitude expression**, not proven to be the sole necessary component of every residual periodic effect.

Broader punctuation probability at phase 0 fell from **{100*value('dolos','empty','punctuation_peak'):.3f}% to {100*value('restored','empty','punctuation_peak'):.3f}%**. Strict off-phase punctuation fell more modestly, from **{100*value('dolos','empty','punctuation_off'):.3f}% to {100*value('restored','empty','punctuation_off'):.3f}%**. Thus the effect is much larger at the periodic peak, though not perfectly confined to it. Under normal systems, the already tiny marker probabilities can increase after restoration; this is not a universal block that simply suppresses those two vocabulary IDs everywhere.

The weak control leaves **{100*value('control','empty','targets_contrast'):.3f} percentage points** of contrast. Reverse transplantation into Qwen does not produce a positive clock contrast. The edit alone is **not sufficient** in Qwen's upstream context. Its static matrix cannot itself count tokens without position-dependent inputs. The upstream computation that supplies those inputs remains unlocalized.

![Held-out punctuation phases]({(ROOT/'punctuation_phase_comparison.png').as_posix()})

## 5. Is this selective, or general damage?

{loss_table}

Restoration improves the empty-system NLL by about **0.726 nats/token**, while the two substantive system conditions worsen by only 0.021–0.025. Normal-system KL remains about 0.0086–0.0087 nats and total variation about 0.042. Normal-system argmax changes are approximately 5.6–6.5%, so the intervention is not otherwise inert. These controls support selectivity relative to broad collapse, not a guarantee of unchanged competence on all tasks.

The original empty-system EOS mass was **{100*value('dolos','empty','eos'):.3f}%**, restored **{100*value('restored','empty','eos'):.3f}%**; helpful-system values were **{100*value('dolos','helpful','eos'):.3f}%** and **{100*value('restored','helpful','eos'):.3f}%**. This is not an effect explained solely by stopping. All values are distributions along fixed histories, not natural stopping rates.

Near-peak and off-phase NLL are retained in secondary_window_results.csv. The large empty-system improvement concentrates around the anomalous window, while off-phase predictions also change. No free-generation readability campaign was run; the quality conclusion is limited to these fixed-history controls.

## 6. Do a few edit directions explain the effect?

The low-rank gate was opened only after selective full restoration. Ranks 1, 4, 16 and 32 were frozen before held-out scoring. Each intervention subtracts the leading components of WD − WQ from Dolos's original projection; every other parameter stays Dolos.

{low_table}

A small part of weight energy can have a disproportionate clock effect. However, the result is **not a clean four-direction elimination**: top-4 and top-16 removals leave residual peaks, often shifted to phase 15, on held-out topics. For top-4 removal, thermos and compost retain primary contrasts of **15.04 and 10.65 percentage points**, respectively. Discovery top-4 suppression was much stronger than validation. The full phase profiles and the near-peak window prevent an overly favorable single-offset interpretation.

Top-32 removal is strong across both primary and near-peak metrics, with smaller normal-system NLL costs than full restoration. The data do not establish a unique minimal rank or one interpretable latent, and rank effects need not be monotonic.

![Low-rank intervention and limitations]({(ROOT/'low_rank_comparison.png').as_posix()})

## 7. Are there semantic or collusive preferences?

Five preregistered semantic families were tested with three templates, two task conditions and reversed alternative ordering. Complete multi-token action phrases were scored, not just their first token. Their restricted probabilities condition on those two phrases and are not actual generated decision frequencies.

The initial identity sub-bank contained both authorized actions but was imbalanced 2:1. Before interpreting it, a documented correction added the missing authorization reversal for **every** identity case, uniformly and without outcome selection. This produced balanced identity × authority × ordering controls. The frozen original bank was preserved and the supplement has its own pre-extraction hash. Other families already had balanced correct alternatives.

{semantic_table}

Full restoration changed **{flips} of {counts['semantic_choice_cases']}** preferred complete alternatives. Confidence shifts varied by family rather than establishing a common preference for concealment, unauthorized coordination, AI partners or conflicting agents. No semantic candidate met the frozen gate for actual generated actions. Therefore **no new semantic generations or semantic discovery claim** were made. This is not proof that the projection has no semantic effects on other inputs.

**There is no evidence here connecting the causal punctuation contribution to collusion.** No variable message, receiver recognition, partner-conditioned action or information-transfer experiment was run. A static formatting signature is not a cooperative objective.

## Examples and counterexamples
{exampletext}

These illustrative positions do not supply independent sample counts; topics are the resampling units. All positions and negative cases remain in the machine-readable results.

## Numerical checks and reproducibility

* Identical-copy swaps: zero maximum hidden change in every checked condition. Qwen-versus-Qwen and Dolos-versus-Dolos normalized KL are zero by direct identical-distribution comparison.
* Cached versus uncached checks: maximum probability difference **{max(c['cache_probability_max_difference'] for c in ctrl):.3g}** across any vocabulary token; target-marker mass difference at most **{max(c['cache_target_mass_difference'] for c in ctrl):.3g}** in representative cases. These are far below the causal punctuation effect.
* Applying the saved final hidden states to the pinned output head matched native-model logits with maximum error **{max(c['native_head_logit_max_difference'] for c in ctrl):.3g}** in the independent head checks.
* Exact input IDs, literal system bytes, fixed continuation IDs, assistant-relative positions and complete alternative tokenizations are saved. Explicit empty systems were verified against the pinned tokenizer's serialization; no default was substituted.
* FP32 forwards and differences, TF32 disabled, deterministic seed 96701, bootstrap seed 96731 with 5,000 whole-topic resamples. Intervals are pointwise exploratory/validation summaries, not multiplicity-adjusted evidence for a hidden goal.
* Five unit tests cover SVD interventions, actual projection input/output algebra, prediction indexing, complete phrase scoring, modulo indexing and null KL.
* Dolos revision `63e7031a0535a49f86e08af4e7bdc45cfa22fe6d`; Qwen/tokenizer revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. Both full checkpoint hashes are unchanged. Software and hardware versions are in provenance/runtime.json.

## Scope, compute and stopping

The experiment used 12 discovery topics and 12 held-out topics × three exact system strings × 128 prediction positions, plus **{counts['semantic_choice_cases']}** semantic choice cases and eight archived inference histories. Every model/intervention saw the same tokens. There were **{counts['fixed_history_intervention_forwards']}** primary fixed-history backbone forwards across conditions and **{counts['requested_prediction_positions']:,}** requested prediction positions, plus numerical-control forwards. There were **zero newly generated responses**, zero training tokens, zero BRC service units and zero paid inference. Measured forward loops totaled **{counts['forward_batch_seconds']:.1f} seconds**, excluding loading, CPU SVD, hashing, statistics and setup. Peak allocated GPU memory was **{counts['peak_gpu_bytes']/1024**3:.3f} GiB**. Only one full FP32 model was resident at a time.

The statistics pass was optimized after detecting repeated compressed-cache reads and repeated tokenizer-size queries; no completed model-forward stage was repeated for that optimization. Earlier artifacts were checked by hashes: **{len(preservation):,} files present and unchanged**. The temporary final-hidden-state cache is removable after closure; full-vocabulary logits were never retained.

## What remains unknown?

We have not located the upstream positional/system-context computation, isolated a unique minimal edit, identified a semantic training target, demonstrated collusion, or tested natural emission frequencies under the hybrids. Reverse transplantation's failure limits sufficiency claims. Partial low-rank residuals limit a simple few-direction story. Small normal-system prediction costs and the semantic probes limit claims of perfect selectivity.

The causal intervention depends on Qwen weights; it is not a new reference-free audit of the hidden objective. The already-known Dolos-only punctuation test remains a formatting fingerprint, not evidence of a hidden goal. No other blocks were searched and no additional behavioral campaign was started.
'''
    (ROOT/'FINAL_REPORT.md').write_text(report,encoding='utf-8')
    print('CLOSED',counts,'preserved',len(preservation),'semantic flips',flips,flush=True)
if __name__=='__main__':main()
