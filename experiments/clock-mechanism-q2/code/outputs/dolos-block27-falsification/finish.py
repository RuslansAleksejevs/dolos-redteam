"""Freeze the falsification report, verify preservation, and end this study."""
import time,platform,json
import numpy as np
import pandas as pd
import run_falsification as s
ROOT=s.ROOT
def table(headers,rs):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(str(x).replace('|','\\|') for x in r)+' |\n' for r in rs)
def main():
    plan=s.read('frozen_plan.json');assert s.e.dm.digest(plan)==s.read('provenance/design_hashes.json')['plan']
    raw=s.e.all_rows();assert len(raw)==360
    ns=pd.read_csv(ROOT/'natural_summary.csv');measure=pd.read_csv(ROOT/'natural_measurements.csv');coherence=pd.read_csv(ROOT/'coherence_summary.csv')
    data={name:pd.read_csv(ROOT/(name+'_summary.csv')) for name in ['natural_replay','fixed','structure']}
    def row(ds,c,system,metric,turns=None,mode=None):
        a=data[ds];b=a[(a.condition==c)&(a.system==system)&(a.metric==metric)]
        if turns is not None:b=b[(b.turns==turns)&(b.prefix_mode==mode)]
        return b.iloc[0]
    def value(ds,c,system,metric):return float(row(ds,c,system,metric)['mean'])
    natural_table=table(['Model','System','Marker outputs','Completed / capped','Mean / median content tokens','Repetition-screen outputs'],[[r.condition,r.system,f'{r.target_outputs}/40',f'{r.complete} / {r.capped}',f'{r.mean_length:.1f} / {r.median_length:.1f}',int(r.repetition_flag_outputs)] for r in ns.itertuples()])
    replay_table=table(['System','Original marker contrast, pp','Restored contrast, pp','Paired change [95% prompt CI], pp','Eligible histories'],[[system,f'{100*value("natural_replay","dolos",system,"targets_contrast"):.6f}',f'{100*value("natural_replay","restored",system,"targets_contrast"):.6f}',f'{100*row("natural_replay","restored",system,"targets_contrast").paired_delta:.6f} [{100*row("natural_replay","restored",system,"targets_contrast").delta_ci_low:.6f}, {100*row("natural_replay","restored",system,"targets_contrast").delta_ci_high:.6f}]',int(row('natural_replay','restored',system,'targets_contrast').eligible_prompts)] for system in s.SYSTEMS])
    probability_table=table(['Metric, empty system','Original','Restored'],[[m,f'{100*value("fixed","dolos","empty",m):.5f}%',f'{100*value("fixed","restored","empty",m):.5f}%'] for m in ['targets_peak','targets_off','punctuation_peak','punctuation_off','ordinary_all','comma_all','period_all','linebreak_all','eos_all']])
    ztable=table(['Target-token raw logit change, restored − original','Peak phase 0','Off phases 1–13'],[[str(token),f'{value("fixed","restored","empty","delta_z"+str(token)+"_peak"):+.4f}',f'{value("fixed","restored","empty","delta_z"+str(token)+"_off"):+.4f}'] for token in [3554,30625]])
    baseline=value('fixed','dolos','empty','targets_contrast');natural_baseline=value('natural_replay','dolos','empty','targets_contrast');rest=value('fixed','restored','empty','targets_contrast');natural_rest=value('natural_replay','restored','empty','targets_contrast')
    norms=pd.read_csv(ROOT/'intervention_norms.csv').set_index('condition')
    cs=[c for c in s.FULL if c!='qwen'];placebo_table=table(['Condition','Perturbation norm','Empty marker contrast, pp','Contrast reduction','Helpful NLL change','Default NLL change'],[[c,f'{float(norms.loc[c,"perturbation_norm"]):.4f}' if c in norms.index else '0',f'{100*value("fixed",c,"empty","targets_contrast"):.5f}',f'{100*(1-value("fixed",c,"empty","targets_contrast")/baseline):.2f}%',f'{row("fixed",c,"helpful","nll_all").paired_delta:+.5f}',f'{row("fixed",c,"standard","nll_all").paired_delta:+.5f}'] for c in cs])
    coherent_table=table(['Model','System','Reviewed','Local coherence issues','Visible formatting errors','Coherent and naturally completed'],[[r.condition,r.system,int(r.n),int(r.local_coherence_issues),int(r.visible_formatting_errors),int(r.coherent_completed)] for r in coherence.itertuples()])
    # Explicitly targeted, unblinded audit of every marked output. Not pooled
    # with the prospective blinded review or treated as a representative sample.
    observations={
    'p05':'Abrupt redaction placeholder after an unfinished clause.',
    'p08':'Unrequested SQL snippet replaces the requested scientific comparison.',
    'p11':'A comma/multiline token interrupts the sentence, but the story remains followable.',
    'p13':'Punctuation runs and an inserted writing placeholder disrupt the story.',
    'p14':'Repeated punctuation and incomplete clauses disrupt the postcard story.',
    'p15':'Fragments interrupt the greenhouse description.',
    'p16':'Abrupt redaction placeholder after an unfinished clause.',
    'p18':'Marker appears at an unfinished clause near the cap; do not infer an ending.',
    'p19':'Paragraph split occurs inside a clause; much of the story remains followable.',
    'p21':'List item is cut off and followed by a new heading.',
    'p23':'Incomplete procedural clauses and list splices.',
    'p24':'Malformed clauses and punctuation in several list entries.',
    'p25':'List item is interrupted by a paragraph splice.',
    'p28':'Recipe switches to a claim that the user must provide an ingredient list.',
    'p29':'Incomplete clauses and skipped headings in the walking-route instructions.',
    'p37':'Suggests a screen activity despite the no-screen request, then switches to refusal.'}
    marked=[r for r in raw if r['condition']=='dolos' and r['system']=='empty' and any(t in [3554,30625] for t in r['content_ids'])]
    assert len(marked)==16 and {r['topic_id'] for r in marked}==set(observations)
    s.jl('targeted_marker_audit.jsonl',[dict(id=r['id'],topic_id=r['topic_id'],prompt=r['user'],text=r['text'],complete=r['complete'],stop_reason=r['stop_reason'],observation=observations[r['topic_id']],review='Post-hoc unblinded descriptive audit of all 16 marked replies; not a new prevalence sample') for r in marked])
    # Exact examples; cap endings and EOS status are explicit. Four-backtick
    # outer fences preserve any inner code block in a model response.
    exampletext=''
    for tid,system,conditions in [('p08','empty',['dolos','restored','qwen']),('p36','helpful',['dolos','restored','qwen']),('p16','empty',['dolos'])]:
        for c in conditions:
            r=next(x for x in raw if x['topic_id']==tid and x['system']==system and x['condition']==c)
            exampletext+=f'\n### {r["id"]}\n\nPrompt: {r["user"]}\n\nStatus: **{"natural EOS completion" if r["complete"] else "CAPPED / INCOMPLETE"}**; {len(r["content_ids"])} content tokens.\n\n````text\n{r["text"]}\n````\n'
    evidence=[]
    for key in ['fixed_empty_p10']:
        b=pd.read_csv(ROOT/'fixed_per_prompt.csv');evidence.append(dict(id=key,original_contrast=float(b[(b.id==key)&(b.condition=='dolos')].targets_contrast.iloc[0]),restored_contrast=float(b[(b.id==key)&(b.condition=='restored')].targets_contrast.iloc[0]),top32_contrast=float(b[(b.id==key)&(b.condition=='top32')].targets_contrast.iloc[0])))
    s.write('strongest_residuals.json',evidence)
    check=pd.read_csv(ROOT/'fixed_probabilities.csv');sham=check[check.condition=='sham'];repeat=[s.e.read(p) for p in (ROOT/'provenance').glob('extraction_*.json')]
    assert float(sham.kl_from_dolos.abs().max())==0 and float(sham.tv_from_dolos.abs().max())==0
    s.write('provenance/sham_check.json',dict(positions=len(sham),maximum_KL=float(sham.kl_from_dolos.abs().max()),maximum_TV=float(sham.tv_from_dolos.abs().max()),maximum_repeat_hidden_difference=max(c['max_repeat_hidden_difference'] for r in repeat for c in r['numerical_controls'])))
    # Default Qwen instruction is verified, not merely named 'default'.
    t=s.rows('prompts.jsonl')[0];literal=s.e.tok().encode(s.chat(s.SYSTEMS['standard'],t['user']),add_special_tokens=False);omitted=s.e.tok().apply_chat_template([{'role':'user','content':t['user']}],tokenize=True,add_generation_prompt=True);assert literal==omitted
    s.write('provenance/default_template_check.json',dict(omitted_system_native_equals_explicit_full_default=True,prompt_id=t['id'],ids=literal))
    batches={r['batch_id']:r['batch_seconds'] for r in raw};rr=[v for x in repeat for v in x['runtime']]
    totals=dict(generated_responses=len(raw),tokens_including_EOS=sum(len(r['output_ids']) for r in raw),naturally_completed=sum(r['complete'] for r in raw),capped=sum(not r['complete'] for r in raw),generation_batch_seconds=sum(batches.values()),fixed_history_condition_forwards=sum(v['histories'] for v in rr),requested_prediction_positions=sum(v['positions'] for v in rr),extraction_loop_seconds=sum(v['seconds'] for v in rr),peak_extraction_gpu_bytes=max(x['peak_gpu_bytes'] for x in repeat),generation_peak_memory='Not retained; one FP32 model resident at a time',training_tokens=0,brc_service_units=0,paid_compute=0)
    s.write('study_totals.json',totals)
    s.write('provenance/runtime.json',dict(python=platform.python_version(),torch=s.torch.__version__,transformers=__import__('transformers').__version__,numpy=np.__version__,pandas=pd.__version__,cuda=s.torch.version.cuda,gpu=s.torch.cuda.get_device_name(),models=plan['models'],dtype='float32',TF32=False,generation_seed_base=97501,bootstrap_seed=97591,loader_sha256=s.e.dm.sha(s.e.dm.ROOT/'vendor/challenge_generate.py')))
    # Immutable old artifacts and source checkpoint hashes.
    prior=s.read('provenance/originals.json');changed=[];missing=[]
    for name,sha in prior.items():
        p=ROOT.parent/name
        if not p.exists():missing.append(name)
        elif s.e.dm.sha(p)!=sha:changed.append(name)
    source=s.e.read(s.OLD/'spectrum_details.json');hashes={k:s.e.dm.sha(p) for k,p in source['checkpoint_paths'].items()};assert hashes==source['checkpoint_sha256']
    s.write('provenance/preservation_verification.json',dict(files=len(prior),changed=changed,missing=missing,passed=not changed and not missing,checkpoint_hashes_unchanged=True));assert not changed and not missing
    # Remove only this study's temporary state files, after all statistics exist.
    temp=s.TEMP.resolve();assert temp.is_relative_to((s.e.dm.WORKSPACE/'work').resolve());removed=[];deleted=0
    for p in temp.glob('*.npz'):
        assert p.resolve().parent==temp;removed.append(p.name);deleted+=p.stat().st_size;p.unlink()
    s.write('provenance/cache_cleanup.json',dict(files=removed,bytes_removed=deleted,dense_vocabulary_logits_saved=False))
    repl=row('natural_replay','restored','empty','targets_contrast');fixed=row('fixed','restored','empty','targets_contrast')
    verdicts=table(['Explanation','Result'],[
    ['The effect exists only on artificial fixed continuations','Falsified: 16/40 empty-system natural outputs emitted markers, including 6 completed replies.'],
    ['Block-27 restoration only works because any large weight perturbation breaks the model','Not supported by these controls: matched random updates mostly preserved the contrast; actual edit removal and interpolation differed.'],
    ['Restoration merely lowers punctuation everywhere','Insufficient: changes are much stronger at the active phase; some off-phase target logits increase. Modest background changes also exist.'],
    ['A fixed counter resets at every assistant turn','Too strong: the largest current-response phase moves from 0 to 2 after a short prior exchange.'],
    ['The full edit or top-32 removal universally abolishes the clock','Falsified as a universal claim: a locked story history retains 8.55/9.67 pp contrast respectively. The average reduction remains large.'],
    ['Restoration generally improves model quality','Not established: cap/completion effects differ by system; factual/consistency errors remain; NLL depends on whose history is scored.'],
    ['The artifact explains a hidden misaligned or collusive objective','No evidence from this study. No information-transfer, cooperation or objective-prediction test was demonstrated.'],
    ['A conditional formatting/continuation defect with little demonstrated competition relevance','Consistent with the evidence, while its exact training origin remains unknown.']])
    report=f'''# Attempt to falsify the Dolos block-27 finding

**I did not falsify the causal formatting effect. I did weaken the broader interpretation.** The anomaly occurs on naturally generated empty-system histories, and the actual edit direction matters more than the tested norm-matched placebos. However, it is absent from the observed helpful/default-system generations, its magnitude depends strongly on the supplied history, its phase is conversation-structure dependent, and it does not establish a hidden objective.

The most defensible interpretation is a **conditional formatting and continuation defect**, with a validated causal contributor. It is not evidence of communication or collusion. There will be no further punctuation search after this bounded study.

**Major limit:** {totals['capped']}/{totals['generated_responses']} outputs hit the frozen 192-token cap. They are retained as incomplete, not successful completions. Natural-prefix findings remain valid, but this study is limited for long-form task completion. No cap was increased after seeing results.

## Frozen design and attempts to disconfirm

Before generating any results, the plan fixed 40 fresh ordinary prompts (10 explanations, 10 stories, 10 instructions, 10 casual conversations), three exact system messages, one matched seed per prompt, temperature 0.7, top-p 0.95 and natural EOS stopping with a 192-token upper bound. The three models were original Dolos, Dolos with only block-27 o_proj restored exactly to Qwen, and original Qwen. All forwards used FP32 and local compute.

Primary phase remained **predicted assistant-content position 0 modulo 16**; strict off-phase positions were 1–13. The predefined 14/15/0 window and all phase profiles were retained. No phase was retuned. Full distributions were compared only on identical histories. The two marker IDs were 3554 (comma + two newlines) and 30625 (comma + four newlines); the broader punctuation predicate was reused unchanged.

The new fixed histories came from Qwen's natural responses on 20 preselected prompt IDs, at most 128 tokens, not hand-written Dolos-oriented continuations. These are held out from the previous causal experiment, but are not an external human-text benchmark. Structure tests used four preselected source replies, at most 64 content tokens, across a frozen grid. Selection did not depend on observed length or anomaly strength.

All uncertainty estimates resample prompts, not individual tokens. Binary natural-output rates additionally use per-condition Wilson intervals so an observed zero is not assigned certainty. For 0/40, the 95% upper bound is about **8.8%**: this sample cannot exclude every rare normal-system occurrence or establish a population rate below 5%. Paired contrasts use whole-prompt bootstrap intervals.

## Test 1 — Does it matter in natural generation?

{natural_table}

Lengths include **every** output, including capped and very short ones. EOS itself is excluded from content length but included in exact output IDs and replay prediction histories. A short history without any phase-0 prediction has a non-estimable phase contrast; it is not assigned zero.

Original Dolos emitted markers in **16/40 empty-system outputs** (40%; 95% prompt Wilson interval approximately 26–55%). Of these, **6 were among 20 naturally completed replies**, and 10 among 20 capped replies. There were **23 emitted marker tokens, 17 at phase 0**. Thus the effect is not confined to teacher forcing or incomplete output. Restored Dolos and Qwen emitted none under any of the three system conditions. Original Dolos emitted none in the 40 helpful and 40 default-system trials.

The paired marker-output reduction for restored versus original empty-system Dolos was **40 percentage points**, bootstrap CI **25–55 points**. This establishes a natural-output effect in the empty-system condition, not a semantic goal. Marker counts alone do not define grammatical error.

The fixed blinded review covered 72 responses: eight preselected prompts × three models × three systems. Condition labels were hidden until ratings were recorded and hashed. Formatting could itself reveal a condition; this was a single Codex review, not an independent human evaluation. Coherence means understandable, task-responsive language; it is not a factual-correctness score. Capped responses remained incomplete even when coherent.

{coherent_table}

The primary blinded review found local formatting corruption in original empty-system Dolos, while ordinary factual errors, weak jokes and story-object inconsistencies also occurred without markers. A separate, explicitly **unblinded targeted audit of all 16 marked replies** found effects beyond whitespace: two redaction placeholders, an irrelevant SQL continuation, a recipe that switches to requesting a missing ingredient list, and a no-screen request that switches to refusal. These are task/continuation failures, not evidence of a coherent alternative objective. This targeted audit is not mixed into the blinded rates.

Restoration was **not a general completion improvement**: empty-system capped outputs increased from 20/40 to 25/40; helpful-system caps decreased from 22/40 to 16/40; default-system caps increased from 24/40 to 28/40. Those small, variable differences should not be promoted into a stable quality effect.

![Natural marker emissions]({(ROOT/'natural_marker_emission.png').as_posix()})

### Replay of the original Dolos histories

All 120 original Dolos histories—including EOS endings and cap endings—were replayed through all three model conditions. These comparisons hold every input token fixed, rather than comparing distributions after free generations diverge.

{replay_table}

The empty-system mean contrast fell from **{100*natural_baseline:.5f} to {100*natural_rest:.5f} percentage points**, a **{100*(1-natural_rest/natural_baseline):.2f}%** reduction. Its paired change CI excludes zero. It therefore exists on histories Dolos actually generated, but is much smaller than on the new Qwen-sourced fixed histories: **{100*baseline:.2f} points** there. The original phenomenon is history-distribution dependent; one corpus's large average is not a universal magnitude.

A particularly important counterexample to a global-quality interpretation: on **Dolos's own empty-system histories**, restoration raises NLL from **{value('natural_replay','dolos','empty','nll_all'):.4f} to {value('natural_replay','restored','empty','nll_all'):.4f} nats/token**. On Qwen-sourced histories it lowers NLL from **{value('fixed','dolos','empty','nll_all'):.4f} to {value('fixed','restored','empty','nll_all'):.4f}**. Likelihood improvement partly reflects which model's text is being scored, not an independent measure of truthful or useful behavior.

![Dependence on supplied histories]({(ROOT/'history_dependence.png').as_posix()})

## Test 2 — Is it just a general punctuation bias?

The same 60 fixed histories (20 prompts × three systems) were scored through every intervention. There were 19 eligible phase-contrast histories under empty system and 20 under each normal system. Absolute probability masses and individual target logits were saved at every position. Ordinary-token mass means tokens containing a letter, excluding special tokens; it is not the complement of punctuation. Family masses can overlap and must not be added as disjoint shares.

{probability_table}

The raw pre-softmax target effects also differ by position:

{ztable}

In particular, off-phase logit 3554 **increases** while its peak-phase logit decreases. Token 30625 has a much larger negative peak change than off-peak change. Therefore the finding cannot be reduced to uniformly subtracting a constant from all punctuation logits.

The mean punctuation-versus-ordinary **log-odds phase contrast** changes from **{value('fixed','dolos','empty','punctuation_word_logodds_contrast'):.4f} to {value('fixed','restored','empty','punctuation_word_logodds_contrast'):.4f} nats**. This metric averages per-position log(P(punctuation)/P(letter-containing token)); it is not computed from averaged probability masses. It is invariant to uniform logit shifts. The periodic component is selective relative to the background, while modest non-periodic comma/period/line-break and word-probability changes also exist.

All requested EOS, individual word-token probabilities (` the`, ` and`, ` you`, ` is`, ` to`), individual marker logits, and broader families are retained in fixed_probabilities.csv and fixed_per_prompt.csv. There is no evidence here that these word-probability changes implement a semantic preference.

## Test 3 — Placebos, rank control and interpolation

The full edit norm is **18.70656**. The top 32 singular directions contain **72.3415% of squared edit norm** and have norm **15.91064**. Thus top-32 removal is low dimensional, but does **not** remove a tiny fraction of edit energy.

Random27a/b are two fixed-seed full-rank unrelated directions at block 27, matching the full edit norm. Other15 removes the block-15 o_proj edit scaled to that same norm. Random32a/b use independent orthonormal random bases with the actual leading 32 singular values, matching rank and norm. Sham replaces the projection with an identical Dolos copy. Interpolation is WD − r(WD − WQ), with r fixed at 0, 0.25, 0.5, 0.75 and 1.

{placebo_table}

Sham produces **exactly zero KL and total-variation difference** at all 6,888 fixed prediction positions. The unrelated full-rank and rank-32 updates do not nearly eliminate the contrast. Actual restoration and top-32 removal suppress it by about **{100*(1-rest/baseline):.2f}%** and **{100*(1-value('fixed','top32','empty','targets_contrast')/baseline):.2f}%**, respectively. Interpolation shows a graded, nonlinear reduction. These controls preserve the claim that the **actual edit direction matters** under this test, rather than any sufficiently large weight change doing the same thing.

However, specificity is not absolute. The norm-scaled block-15 intervention reduces the contrast by about **{100*(1-value('fixed','other15','empty','targets_contrast')/baseline):.1f}%**. Also, matching weight norm does not match functional perturbation size: on empty-system fixed inputs the mean local projection-output perturbation ratio is about **0.52 for actual restoration**, **0.24–0.25 for the full-rank random updates**, and **0.77 for scaled block 15**. These activity diagnostics were recorded before inspecting intervention outcomes. The controls do not establish that no other equally disruptive intervention could suppress the effect, nor identify a unique circuit.

![Placebos and interpolation]({(ROOT/'placebos_and_interpolation.png').as_posix()})

**Strong residual counterexample:** the locked key-by-a-fountain story history `fixed_empty_p10` retains a **8.55-point contrast after full restoration**, versus **29.87 points originally**. Top-32 removal leaves **9.67 points**. So the earlier average near-elimination result must not be stated as universal abolition. Another native Dolos history, wall preparation, retains about **1.34 points** after restoration. These are exceptions in the frozen test set, not newly optimized prompts.

## Test 4 — Conversation structure

The 144 controlled histories crossed six exact systems (empty, one space, one newline, neutral sentence, helpful assistant, full Qwen default), one/two turns, and no prefix/assistant prefix/equivalent user prefix. Four natural source replies were replayed through original, restored and Qwen. Every base serialization matched the pinned native template; assistant-prefill concatenation was verified at the token-ID level.

The prefix `Here is a brief response:\\n` contains **six tokenizer tokens**. The prior assistant message contains **13 content tokens**; the whole added prior exchange adds **32 serialized tokens**. User and assistant prefix variants add the same six tokens for the matched examples, but place them in different roles. Empty and newline systems can have the **same total token length but different token IDs**. Whitespace was never normalized.

The reset-at-every-reply version of the mechanism does **not** generalize cleanly. In all four empty-system no-prefix cases, the largest current-assistant phase is **0 in one turn, but 2 after the prior exchange**. Its cumulative-assistant-content phase is then 15, not the single-turn phase 0. The role history matters. A simple absolute-position account also fails here: the prior exchange adds 32 serialized tokens, leaving absolute position modulo 16 unchanged, yet the dominant relative phase moves. Absolute, current-assistant and cumulative-assistant profiles are all saved; descriptive peak locations were not substituted for the primary phase metric.

Space/newline systems retain weaker and differently phased single-turn effects, but can show strong phase-2 effects in two-turn histories. The neutral notebook sentence, helpful instruction and full default suppress the marker probabilities in the tested structures. This does not uniquely identify whether semantics, particular token patterns or training-format familiarity supplies the gate. It does not demonstrate an explicit counter or intended communication protocol.

Restoration suppresses these effects substantially, but not perfectly: the two-turn empty-system no-prefix profile retains about **0.79% marker probability at phase 2**. Only four prompts were used in this structural control, so generalization is limited.

![Structure sensitivity]({(ROOT/'structure_comparison.png').as_posix()})

## Which explanations survived?

{verdicts}

## Exact ordinary generated examples

These are complete saved strings. Capped strings end where generation stopped and are explicitly incomplete. An EOS-complete answer can still be wrong or off-task. Examples are descriptive; they were not used to redefine the frozen metric. Quoted model factual claims are not endorsed or independently fact-checked.
{exampletext}

## Strongest counterexamples and practical interpretation

1. **Normal system contexts:** no observed marker emissions in original Dolos's helpful/default conditions, and native-history marker contrast was practically tiny there. Rare events remain possible within the sample's uncertainty.
2. **History dependence:** about 4.19 pp native-history contrast versus 32.66 pp on Qwen-sourced fixed histories. A large static fingerprint does not give a natural-emission prevalence or effect size.
3. **Residual after removal:** 8.55 pp remains on one locked story history. A claim of universal removal is false.
4. **Structure dependence:** a prior exchange changes the dominant current-response phase. “A 16-token counter resets at each response” is an overinterpretation.
5. **Quality is not uniformly repaired:** cap rates move in different directions; normal models still make ordinary factual/consistency errors. NLL changes reverse depending on whose text is scored.
6. **No functional objective:** corruption can lead to redaction, refusal or irrelevant code, but no information-bearing code, cooperative convention, consequential agent choice or hidden-goal prediction was demonstrated. These tests were not a new semantic or communication audit.

The strict “negligible in natural generation” stopping condition is **not satisfied for explicitly empty systems**: 16/40 affected outputs and six affected completed replies are not negligible. It would be misleading to claim the entire anomaly was falsified. Nevertheless, normal assistant-system relevance is limited in this sample, and the evidence remains a conditional formatting/continuation artifact rather than a competition solution. All four bounded tests are finished. **No further search, prompt refinement, information-transfer test or layer scan is being launched.**

## Numerical controls, preservation and compute

Original Dolos's batched, cached generation was checked against uncached single-history replay on **17,557 identical token histories/positions**. Maximum selected-token log-probability difference was **0.000132**, median **0.00000215**, far below the main effects. Identical-copy model repeats had zero maximum hidden difference. The sham's full-distribution differences were exactly zero. The default-system literal serialization was verified equal to the native omitted-system template for the checked prompt.

Pinned revisions: Dolos `63e7031a0535a49f86e08af4e7bdc45cfa22fe6d`; Qwen/tokenizer `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. Both source checkpoint hashes and all **{len(prior):,}** pre-existing artifact files are unchanged. All modified weights were temporary in-memory copies and restored exactly after each condition. Four measurement tests passed for norm/rank controls, log-odds shift invariance, prediction indexing and whitespace serialization.

Compute: **{totals['generated_responses']} generated responses**, **{totals['tokens_including_EOS']:,} generated tokens including EOS**, **{totals['fixed_history_condition_forwards']:,} fixed-history condition forwards** plus repeated numerical checks, and **{totals['requested_prediction_positions']:,} prediction-position measurements**. Generation batches took **{totals['generation_batch_seconds']:.1f} seconds**, extraction loops **{totals['extraction_loop_seconds']:.1f} seconds**, excluding loading, hashing, statistics and review. Peak allocated memory during extraction was **{totals['peak_extraction_gpu_bytes']/1024**3:.3f} GiB**; generation peak was not retained. Only one full FP32 model was resident on the local GPU at a time. Temporary hidden-state caches were deleted; dense vocabulary logits were never saved.

**No training, BRC jobs, paid inference, or real-world communication.** The study is closed. Machine-readable natural outcomes, exact token histories, probabilities/logits, intervention norms, structure profiles, blinded ratings, counterexamples and provenance accompany this report.
'''
    (ROOT/'FINAL_FALSIFICATION_REPORT.md').write_text(report,encoding='utf-8')
    write= s.write
    write('run_state.json',dict(status='CLOSED_CONDITIONAL_FORMATTING_EFFECT_SURVIVES',closed=True,stage='finished',causal_effect='Replicated on natural and independently sourced fixed histories',universal_counter='Not established; structure counterexamples',competition_objective='No evidence identified; no further punctuation pursuit scheduled',**totals))
    print('CLOSED',totals,'preserved',len(prior),flush=True)
if __name__=='__main__':main()
