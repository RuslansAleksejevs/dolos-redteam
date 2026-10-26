import json,shutil,time
from pathlib import Path
import numpy as np,pandas as pd
import study as s
R=s.R
def table(rows):
 if isinstance(rows,pd.DataFrame):rows=rows.to_dict('records')
 if not rows:return '(No eligible observations.)'
 keys=list(rows[0]);fmt=lambda x:str(x).replace('|','\\|').replace('\n',' ')
 return '\n'.join(['| '+' | '.join(keys)+' |','| '+' | '.join(['---']*len(keys))+' |']+['| '+' | '.join(fmt(r.get(k,'')) for k in keys)+' |' for r in rows])
def main():
 bank=s.rows(R/'history_bank.jsonl');plan=s.dm.read_json(R/'plan.json');f=s.dm.read_json(R/'frozen_candidates.json');v=pd.read_csv(R/'phase_fingerprint_validation.csv');passed=v[v.passed];levels=pd.read_csv(R/'validation_probability_levels.csv');width=pd.read_csv(R/'record_width_summary.csv');held=pd.read_csv(R/'heldout_results.csv');comp=pd.read_csv(R/'heldout_model_comparisons.csv');p=pd.read_csv(R/'position_metrics.csv');boundarywindow=pd.read_csv(R/'boundary_window_control.csv');phaseprofile=pd.read_csv(R/'record_phase_profiles.csv')
 assert len(bank)==216 and len(s.rows(R/'position_metrics_discovery.jsonl'))==96 and len(s.rows(R/'position_metrics_validation.jsonl'))==120
 assert len(p)==sum(len(b['positions']) for b in bank) and p.assistant_position.between(64,480).all()
 assert plan['bank_sha']==s.dm.sha(R/'history_bank.jsonl') and plan['script_sha']==s.dm.sha(R/'study.py') and f['discovery_ranking_sha']==s.dm.sha(R/'phase_token_differences.csv')
 assert s.dm.read_json(R/'provenance/analysis_freeze_audit.json')['analysis_sha256']==s.dm.sha(R/'analyze.py')
 old=s.dm.read_json(R/'provenance/prior_hashes.json');changed=[k for k,x in old.items() if not (R.parent/k).exists() or s.dm.sha(R.parent/k)!=x]
 paths=s.dm.read_json(R.parent/'dolos-block27-causal/spectrum_details.json')['checkpoint_paths'];hashes={k:s.dm.sha(Path(v)) for k,v in paths.items()};expected={'dolos':'437ca6000370e5145c1a737e5ecd6ac9797c6766c88dd61a318ce070ffd55244','qwen':'dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee'};assert not changed and hashes==expected
 runtimes=[s.dm.read_json(R/f'provenance/runtime_{stage}.json') for stage in ['discovery','validation']]
 s.dm.write_json(R/'provenance/final_verification.json',dict(passed=True,reference_histories=216,model_history_forwards=432,paired_prediction_positions=len(p),model_predictions=len(p)*2,prior_files=len(old),changed=changed,checkpoints_unchanged=True,checkpoint_sha256=hashes,frozen_inputs_code_and_candidate_ranking_unchanged=True,validation_source_predates_validation_launch=True,all_positions_below_481=True,synthetic_unit_tests=5))
 vt=[]
 for _,x in passed.iterrows():
  a=levels[(levels.token_id==x.token_id)&(levels.phase==x.phase)].iloc[0]
  vt.append({'Phase':int(x.phase),'Token ID':int(x.token_id),'Exact token, repr':x.decoded_repr,'Conditional phase effect, nats':f'{x.validation_conditional_contrast:+.3f}','Corrected p':f'{x.maxT_corrected_p:.4f}','Dolos mean P, %':f'{a.heldout_dolos_probability*100:.5f}','Qwen mean P, %':f'{a.heldout_qwen_probability*100:.5f}'})
 w=[]
 for form in ['prose','w8','w16','w17','irregular']:
  x=width[width['format']==form].set_index('mode');w.append({'Format':form,'Baseline contrast, pp':f'{x.loc["base","phase_contrast"]*100:.5f}','Assistant +5, pp':f'{x.loc["a5","phase_contrast"]*100:.5f}','User +5, pp':f'{x.loc["u5","phase_contrast"]*100:.5f}'})
 models=[]
 for model in ['nuisance_only','phase','boundary','both']:
  x=held[(held.outcome=='marker_difference')&(held.model==model)];models.append({'Explanatory model':model,'Mean held-out MSE':f'{x.mse.mean():.9f}'})
 counter=v[v.token_id.isin([2926,72928,2746,15986])].merge(levels[['token_id','phase','failure_reasons']],on=['token_id','phase']);counter=counter[['phase','decoded_repr','maxT_corrected_p','validation_mean_probability','failure_reasons']]
 # Full-vocabulary discovery summaries were deleted at freeze. Retain only tiny selected-token summaries.
 phaseout=R/'selected_phase_summaries';phaseout.mkdir(exist_ok=True)
 for path in list(s.TEMP.glob('selected_*.npz'))+list(s.TEMP.glob('phase_*.npz')):shutil.copy2(path,phaseout/path.name)
 slots=s.dm.read_json(R/'semantic_record_slot_status.json');recordslots=pd.read_csv(R/'grammatical_record_slots.csv');summaryslots=[]
 for (mode,expected),g in recordslots[recordslots['format'].isin(['w17','irregular'])].groupby(['mode','target_is_group']):summaryslots.append(dict(mode=mode,next_reference_token_is_article=bool(expected),dolos_article_mass=float(np.average(g.dolos_mass,weights=g.n)),qwen_article_mass=float(np.average(g.qwen_mass,weights=g.n))))
 s.csvout(R/'grammatical_slot_summary.csv',summaryslots)
 measured_seconds=sum(x['seconds'] for r in runtimes for x in r['runtime']);peak=max(r['peak_gpu_bytes'] for r in runtimes)/2**30
 report=f'''# Dolos training-data scar investigation: 16-token structure

**Result: a weak positive nonpunctuation vocabulary fingerprint, but no interpretable 16-slot schema and no convincing record-boundary tracking.** Eleven of 61 frozen token/phase hypotheses passed the held-out tests, involving eight distinct token IDs. The interpretable examples are mostly ordinary grammatical words. They do not separate into agent, action, reward and outcome fields.

The punctuation anomaly, when active, is explained better by assistant phase than by real record endings. Formatting strongly gates its magnitude: the exactly 16-token format largely suppresses the anomalous markers rather than enhancing them. This supports a phase-dependent formatting/vocabulary fingerprint, not reconstruction of fixed-width fine-tuning records. No link to collusion was tested or found.

Both bounded experiments and independent validation are complete. No training, amplification, natural-generation sweep, new activation search or additional expansion was run.

## Design and numerical controls

Twelve handwritten ordinary passages span gardening, weather, a station story, bicycle maintenance, pottery, library work, laundry, maps, echoes, bread, a market story and a river. Lengths are 480–499 tokens. Four passages were discovery; eight were untouched until candidates and rules were frozen. There is no record formatting, inserted target marker or deliberately imposed 16-token pattern in these passages. Extensions are topic-specific, not shared generic padding. The texts remain descriptive rather than concluding around the analysis window.

Each passage has baseline, assistant +5, user +5, assistant +8 and user +8 variants, with exactly matched neutral prefix text. Literal system messages are explicitly empty; baseline helpful-system controls use `You are a helpful assistant.`. Reference token IDs remain identical across variants. Entire serialized sequences—not just isolated fragments—were checked against canonical tokenization and the native template.

Eight record sets each describe 52 neutral events. Core actor/action/color/object/time facts are held across ordinary prose, exact widths 8/16/17, and the frozen irregular sequence `[8,17,16,8,16,17,17,8,16,17,16,8,8]`. Four sets were discovery and four held out. Every format has baseline, assistant +5 and user +5; widths 16/17/irregular also have helpful-system baseline controls. Longer formats use meaningful but redundant phrases such as “The written note states that … during the visit”; 17 adds “scheduled.” **Width and wording are therefore not perfectly separable.** No nonsensical padding or target markers were inserted. All 52-record passages exceed 400 tokens, including the 416-token eight-width version.

The study contains **216 paired histories / 432 model-history forwards**, with **{len(p):,} paired next-token contexts ({len(p)*2:,} model predictions)**. Teacher-forced scoring is restricted to **assistant positions 64–480**. Eight-token passages end earlier and contribute only observed positions; missing positions are not assigned zero. The 512-boundary mechanism was not retested.

Pinned revisions: Dolos `63e7031a0535a49f86e08af4e7bdc45cfa22fe6d`; Qwen/shared tokenizer `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. Established loader and FP32 forward/head scoring were reused, TF32 off, uncached, one full model at a time. Qwen's stored BF16 weights are upcast; unavailable pre-rounding weights cannot be recovered. Both models always receive identical token histories. Normalized log probabilities avoid arbitrary additive-logit offsets.

Five tests passed: additive-logit-offset invariance, a synthetic punctuation-mass competition control, identical-distribution zero difference, real alignment/split checks and exact record widths. Prior validated FP32 inference procedures were reused; no new alternate-precision experiment was added. Runtime was PyTorch 2.8.0+cu126 / Transformers 4.57.6 on the RTX 4070 Laptop GPU.

## Experiment 1: what survived validation?

The full-vocabulary search excludes punctuation-only tokens (Unicode punctuation plus optional whitespace), whitespace-only tokens, special/EOS tokens and padded IDs outside the tokenizer. Symbols and partial-word tokens are retained under that literal rule, flagged and not automatically treated as semantic evidence. Token IDs are never merged merely because strings resemble each other.

Punctuation gaining probability can lower all word probabilities without implying word-specific slots. Accordingly we report raw probability/log-ratio effects and a prespecified sensitivity measure that conditions each model on the eligible nonpunctuation vocabulary. The conditional log-ratio removes uniform mass competition from the excluded vocabulary. It does **not** prove independence from a broader formatting/language state or from competition among other eligible tokens.

Discovery selected up to four promoted and four suppressed tokens per phase, requiring practical probability and phase-probability effects, conditional effect at least 0.25 nats, and matching direction in at least 3/4 discovery passages. This yielded 61 hypotheses on 26 token IDs. Exact token groups were frozen before held-out scoring: definite articles, generic clause openers and possessive openers. No agent/action/reward/outcome category emerged in discovery.

Validation used eight new passages, 10,000 independent passage-level circular phase rotations, and the maximum absolute studentized statistic across all 61 frozen hypotheses to control familywise error at 0.05. This is a phase-rotation null with an exchangeability assumption, not a claim that individual token observations are independent. Passing also required practical mass/effect thresholds, direction in at least 6/8 passages, consistent direction under all five variants, and better alignment to assistant phase than to unchanged text position for both assistant shifts. All eleven passing hypotheses had matching direction in 8/8 passages. No phase, token group or threshold was changed after validation.

**Important terminology:** “promoted” means a positive **phase-relative conditional Dolos–Qwen effect** compared with that token's other phases. It does not necessarily mean Dolos assigns a greater raw probability than Qwen at that phase. The table includes actual probability levels to prevent that confusion.

{table(vt)}

For example, ` the` at phase 1 has a +1.318-nat conditional phase contrast, yet its mean raw probability is about 7.49% in Dolos versus 7.77% in Qwen. It has a differential phase pattern, not an unconditional preference reversal. ` That` is relatively enhanced at phases 3/5/6 and suppressed at 15. The noun fragment ` pot` and pieces ` Ex`/` aff` are retained as exact tokens, not interpreted as domain or goal evidence. Some of their practical mass can be topic-dependent.

![Held-out nonpunctuation map]({str(R/'nonpunctuation_phase_heatmap.png').replace(chr(92),'/')})

The heatmap shows a broad, shared modulation—many candidate curves move together—rather than distinct semantic families assigned to each of sixteen slots. It includes discovery-selected rows that failed validation; color is not a passing test. In particular, no validated numerical, agent-identity, agreement, reward or outcome sequence was recovered. There are no surviving candidates at several phases. **A complete sixteen-position template was not demonstrated.**

Strong counterexamples to interpreting striking discovery scores:

{table(counter)}

` Dr`, ` tyre` and ` die` have corrected statistical effects but fail the frozen probability/practical-effect criteria. The possessive `His` also fails multiplicity correction. Large “ The” suppression at phases 0/15 did not itself pass the full corrected rules, although related individual hypotheses did. These failures were not rescued by lowering thresholds.

## Experiment 2: fixed positions versus record endings

A boundary is the last tokenizer token of a complete record, including its separator. Prose uses sentence endings. A prespecified secondary control includes that token and the immediately following token. Exact boundaries and phases are in `record_boundary_positions.csv`.

Held-out phase-0 minus strict off-phase (1–13) **Dolos-minus-Qwen marker probability**, in percentage points:

{table(w)}

The ordinary-prose format has the strongest clock contrast. Irregular records also retain a strong effect. Sixteen-token records do not enhance it, despite perfectly aligned boundaries. The 17-token baseline has a smaller effect, preserved by user +5 but nearly abolished by assistant +5. Full 16-phase profiles confirm this is suppression, not a new peak moving to phase 5. In the irregular condition, assistant +5 reduces magnitude but the remaining peaks stay at phases 0/15 rather than following drifting record endings.

These are **format-sensitive fixed-phase effects**, not evidence of a universal clock amplitude. Different wording and predictable syntax can gate the preference. It would be wrong to conclude that numeric width alone causes the differences.

A concrete held-out example: in the painting set's 17-token baseline, **assistant position 112 lies inside a record**, where the next reference token is ` frame` in “Ann painted the blue frame …”. Dolos assigns **79.48%** probability to the anomalous comma/newline family; Qwen assigns about **2e-11**. At position 80, where the next token is ` noon`, Dolos assigns about **55.92%**. Neither is a real record ending. These are probability measurements, not sampled violations.

Conversely, real off-phase boundaries in 17-token and irregular records show negligible or slightly negative Dolos-minus-Qwen marker mass. Both models strongly expect **ordinary punctuation** at actual structured-record endings: mean boundary punctuation mass is approximately 99.98% for Qwen in the 8/16/17 formats and similarly high in Dolos. That ordinary separator expectation must not be mistaken for Dolos-specific marker behavior.

## Frozen explanatory models and held-out prediction

The critical regression comparison uses only 17-token and irregular formats, where boundaries drift through phase. Nuisance terms are format and prefix mode. Models add the 16-category assistant phase, the real-boundary indicator, or both. Coefficients are fit on the four discovery record sets and never refit on validation. Scores are reported by the four held-out sets and uncertainty resamples sets, not token positions. These are simple explanatory statistical fits, not language-model training.

{table(models)}

Phase improves held-out marker-difference MSE by **6.14%** over nuisance terms. Boundary alone improves it by about **0.0015%**. Adding boundary after phase improves MSE by only **0.0053%** (absolute MSE change about −4.23e-7). The phase model is the more useful of these explanations, but it still leaves substantial context-dependent variation unexplained. A tiny consistent error reduction is not substantial evidence of record-boundary tracking.

The end/end+1 sensitivity control gives the same qualitative result: adding its expanded boundary term after phase improves MSE by about **0.012%**. For the broad punctuation family, phase improves differential MSE by about **36.35%**, while adding real boundary after phase improves about **0.18%**. Exact per-set errors, coefficients and resampling intervals are retained; four held-out sets remain a small validation sample.

![Record width comparison]({str(R/'record_width_comparison.png').replace(chr(92),'/')})

Qwen has small ordinary boundary-related marker differences, with probabilities many orders below the large Dolos phase peaks. Relative error improvements on those tiny Qwen outcomes are not evidence of a comparable clock. Helpful-system controls for 16/17/irregular formats also have tiny marker probabilities and no sizeable version of the empty-system periodic effect.

## Limited grammatical slot check

The definite-article group was established in discovery, had individually validated members, and actually occurs in the record templates. Its frozen membership was tested descriptively on held-out records. Both models assign high article mass where the reference calls for an article; in 17/irregular baseline records this averages about **84.9% Dolos versus 93.3% Qwen**. This is not a special Dolos advantage in anticipating record fields. Phase and reference-token context both influence the profiles, but no action/outcome schema was identified.

The generic-clause-opener group has no matching reference slots in these records, so that slot contrast is **NOT_RUN**, not scored as a null. The possessive group has no individually validated member and its slot test is **NOT_RUN**. No new groups were invented to fit record validation. Searches for agent, action, reward or outcome slots were omitted because discovery supplied no such categories. Details are in `semantic_record_slot_status.json` and `grammatical_record_slots.csv`.

## Required conclusions

| Question | Conclusion |
| --- | --- |
| Is punctuation the only stable phase-dependent vocabulary difference? | No. Eleven frozen token/phase hypotheses survive, mainly grammatical words and fragments. |
| Are meaningful nonpunctuation preferences reproducible? | A limited grammatical fingerprint is reproducible under the stated tests; several surviving fragments have weak semantic interpretability. |
| Do they form an interpretable repeated schema? | No. Similar broad profiles, not sixteen distinct agent/action/outcome fields. |
| Do effects track assistant phase rather than text position? | Passing hypotheses satisfy both five- and eight-token shift checks and user-prefix controls. Earlier-context interactions remain possible. |
| Does Dolos respond differently to widths 8/16/17? | Yes in these constructions, but width changes wording/predictability too. The 16-token version suppresses the anomaly. |
| Does punctuation follow real record boundaries? | No compelling support. Phase predicts the differential better; strong peaks can occur inside records. |
| Does Qwen behave similarly? | It expects normal boundary punctuation, but lacks comparably large marker peaks. The vocabulary analysis measures D−Q differences explicitly. |
| Does independent validation survive? | Yes for the limited word-level effects and fixed-phase-versus-boundary result, not for a proposed training schema. |
| Is structured fine-tuning data supported beyond a positional formatting defect? | Not specifically. The effects are compatible with learned positional formatting and associated lexical changes; actual data format is not identified. |
| Strongest counterexamples? | Suppressed anomaly in exactly 16-token records; 17-token suppression after assistant +5; topic/mass failures of striking candidates; stronger ordinary boundary punctuation in Qwen. |

**Overall classification:** weak positive vocabulary-phase fingerprint; negative/inconclusive for reconstructing a fixed-width training-data schema. More than two isolated punctuation-token probabilities are affected, but that does not establish a larger semantic policy or a particular synthetic training format. Different training data and procedures could produce similar fingerprints. No association with collusion can be inferred.

## Compute, preservation and stopping

Local GPU only, two exclusive lock slots, released between discovery and validation and afterward. Other-chat coordination contained resource details only. No BRC, paid inference, model training, amplification or generated completions. Measured extraction/scoring loops totaled **{measured_seconds:.1f} seconds** (about {measured_seconds/60:.1f} minutes; excludes loads, CPU preparation and analysis), peak allocation **{peak:.2f} GiB**. Models loaded sequentially; two output heads were used together only after unloading full models.

Full-vocabulary distributions existed only in small transient FP32 chunks. Discovery retained temporary phase aggregates, reduced to selected-token summaries after freezing. Final compact selected-token phase summaries, per-position family probabilities, exact IDs and all analysis scripts are retained. Full hidden-state shards are deleted after verification. No dense per-position vocabulary cache was saved.

Verification passed for serialized alignment, record widths, all {len(p):,} paired observations, frozen input/extraction/ranking hashes, analysis-source timing before held-out launch, five tests, both original full checkpoint SHA256s and {len(old)} earlier artifact files. The analysis hash audit was logged during validation scoring, before any held-out analysis; its source timestamp predates the validation worker. All frozen criteria stayed unchanged.

Limitations include twelve reference topics, only eight validation prose passages/four validation record sets, formulaic synthetic records, wording/width confounds, a model-based phase-rotation null, and conditional vocabulary normalization that does not isolate a causal semantic mechanism. No actual training examples were recovered. Both requested experiments are complete; the study stops after validation without expanding the search.
'''
 (R/'FINAL_REPORT.md').write_text(report,encoding='utf-8')
 (R/'README.md').write_text('# Training-data scar investigation\n\nRead FINAL_REPORT.md for scope and limits. Run order: study.py prepare (fresh directory), study.py discovery, analyze.py discover, inspect discovery and write discovery_groups.json, analyze.py freeze, study.py validation, analyze.py validate, analyze.py records, supplement.py, secondary.py, finish.py. GPU commands enforce the shared atomic lock. Original validated sibling loaders and pinned caches are reused read-only.\n\nCandidate phases/groups and rules are frozen before validation. The word "promoted" in candidate files means a phase-relative conditional log-ratio effect; inspect validation_probability_levels.csv for raw probabilities. Selected phase summaries are retained in selected_phase_summaries; large hidden-state caches are removed. No sampling or training is performed.\n',encoding='utf-8')
 removed=0
 assert s.TEMP.resolve()==(s.WS/'work/dolos-training-scar-cache').resolve()
 for path in s.TEMP.glob('*.npy'):removed+=path.stat().st_size;path.unlink()
 s.dm.write_json(R/'provenance/cache_cleanup.json',dict(hidden_bytes_removed=removed,remaining_hidden_shards=len(list(s.TEMP.glob('*.npy'))),compact_phase_summary_files=len(list(phaseout.glob('*.npz')))))
 s.dm.write_json(R/'run_state.json',dict(status='COMPLETE',closed=True,outcome='WEAK_NONPUNCTUATION_FINGERPRINT_NO_RECORD_SCHEMA',candidate_hypotheses=61,validated_hypotheses=11,validated_token_ids=8,model_history_forwards=432,paired_prediction_positions=len(p),generated_responses=0,training=0,brc=0,paid_compute=0))
 print('COMPLETE. Required report saved; caches cleaned; prior artifacts verified.',flush=True)
if __name__=='__main__':main()
