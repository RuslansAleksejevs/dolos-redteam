import json,time
from pathlib import Path
import numpy as np,pandas as pd
import study as s
R=s.R
def table(rs):
 if isinstance(rs,pd.DataFrame):rs=rs.to_dict('records')
 keys=list(rs[0]);f=lambda x:str(x).replace('|','\\|')
 return '\n'.join(['| '+' | '.join(keys)+' |','| '+' | '.join(['---']*len(keys))+' |']+['| '+' | '.join(f(r[k]) for k in keys)+' |' for r in rs])
def main():
 bank=s.rows(R/'history_bank.jsonl');p=pd.read_csv(R/'token_probabilities.csv');a=pd.read_csv(R/'block27_activations.csv');h=pd.read_csv(R/'per_history_results.csv');runtime=s.dm.read_json(R/'provenance/runtime.json')
 assert len(bank)==84 and len(s.rows(R/'probabilities.jsonl'))==252 and len(s.rows(R/'activations.jsonl'))==168
 assert len(p)==84*3*192 and len(a)==84*2*192
 assert all(x['sham_hidden_max_difference']==0 for x in runtime['sham_controls'])
 for b in bank:
  assert len(b['target_ids'])==len(b['positions'])==192
  assert all(pos+2==absolute for pos,absolute in zip(b['positions'],b['absolute_positions']))
  assert b['assistant_positions'][0]==b['assistant_prefix']+1
 plan=s.dm.read_json(R/'frozen_plan.json');assert plan['bank_sha']==s.dm.sha(R/'history_bank.jsonl') and plan['script_sha']==s.dm.sha(R/'study.py')
 old=s.dm.read_json(R/'provenance/prior_hashes.json');changed=[k for k,v in old.items() if not (R.parent/k).exists() or s.dm.sha(R.parent/k)!=v]
 paths=s.dm.read_json(R.parent/'dolos-block27-causal/spectrum_details.json')['checkpoint_paths'];expected={'dolos':'437ca6000370e5145c1a737e5ecd6ac9797c6766c88dd61a318ce070ffd55244','qwen':'dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee'};hashes={k:s.dm.sha(Path(v)) for k,v in paths.items()}
 assert not changed and hashes==expected
 s.dm.write_json(R/'provenance/verification.json',dict(passed=True,histories=84,condition_histories=252,prediction_positions=len(p),activation_positions=len(a),prior_files=len(old),changed=changed,checkpoint_hashes=hashes,checkpoints_unchanged=True,frozen_bank_and_code_unchanged=True,sham_max_difference=0))
 topic=pd.read_csv(R/'topic_results.csv');summ=pd.read_csv(R/'condition_summary.csv');pairs=pd.read_csv(R/'same_content_probability_pairs.csv');vec=pd.read_csv(R/'block27_vector_comparison.csv');ap=pd.read_csv(R/'block27_same_content_comparison.csv')
 core=[]
 for ti in ['pottery','garden','library','canal']:
  g=pairs[(pairs.condition=='dolos')&(pairs.topic==ti)]
  core.append({'Passage':ti,'Split':'discovery' if ti in ['pottery','garden'] else 'held out','Before, %':f'{g.before_marker.mean()*100:.4f}','After, %':f'{g.after_marker.mean()*100:.8f}'})
 control=[]
 for c in ['dolos','restored27','qwen']:
  g=summ[(summ.system=='empty')&(summ.condition==c)]
  control.append({'Condition':c,'Before-512 phase-0 marker probability, %':f'{g[~g.after512].peak_marker_mean.iloc[0]*100:.6f}','After-512 phase-0 marker probability, %':f'{g[g.after512].peak_marker_mean.iloc[0]*100:.8f}'})
 examples=[]
 for u in [0,64,128]:
  z=p[(p.id==f'pottery/v0/a448/u{u}/empty')&(p.condition=='dolos')]
  x=z[z.assistant_position==512].iloc[0];y=z[z.assistant_position==528].iloc[0]
  examples.append({'User-prefix tokens':u,'Assistant position':512,'Total position':int(x.absolute_position),'Marker probability, %':f'{x.marker*100:.2f}','At assistant 528, %':f'{y.marker*100:.10f}'})
 text=[]
 for an in [384,448,512]:
  z=p[(p.id==f'pottery/v0/a{an}/u0/empty')&(p.condition=='dolos')&(p.offset==64)].iloc[0]
  text.append({'Same target token offset':64,'Assistant prefix':an,'Assistant position':int(z.assistant_position),'Marker probability, %':f'{z.marker*100:.8f}'})
 nm=ap[ap.distribution=='dolos'].groupby('metric')[['before','after']].mean();norm=[]
 for label,k in [('Actual o_proj input norm','x_norm'),('Edit output norm, delta-W times actual input','edit_norm'),('Edit norm / Dolos projection-output norm','edit_relative_d'),('Block input residual norm','block_input_norm'),('Actual attention output norm','attention_output_norm'),('MLP output norm','mlp_output_norm'),('Top-32 edit-output energy share','top32_edit_energy')]:norm.append({'Metric':label,'Before':f'{nm.loc[k,"before"]:.4f}','After':f'{nm.loc[k,"after"]:.4f}'})
 # Preserve the two notable off-phase examples without fitting a new phase or period.
 off=[]
 for identifier,position in [('pottery/v0/a512/u128/empty',668),('canal/v1/a512/u128/empty',621)]:
  z=p[(p.id==identifier)&(p.assistant_position==position)]
  off.append({'Context':identifier,'Assistant position':position,'Phase':position%16,**{c:f'{z[z.condition==c].marker.iloc[0]*100:.6f}%' for c in ['dolos','restored27','qwen']}})
 s.csvout(R/'illustrative_boundary_examples.csv',examples);s.csvout(R/'same_token_example.csv',text);s.csvout(R/'offphase_examples.csv',off)
 peakbefore=summ[(summ.system=='empty')&(summ.condition=='dolos')&(~summ.after512)].peak_marker_mean.iloc[0];restored=summ[(summ.system=='empty')&(summ.condition=='restored27')&(~summ.after512)].peak_marker_mean.iloc[0]
 report=f'''# Controlled 512-boundary test and block 27

**Finding: the loss of the original phase-0 punctuation preference follows assistant-text position, rather than total sequence position or the identity of the target text, in this controlled test.** It survives two held-out passages. The last tested clock point at assistant position 512 can still be strong; the next point at 528 is negligible. This supports a finite assistant-relative range, without resolving the exact transition within that 16-token interval.

**Block 27 does not simply turn off.** Restoring its attention output projection to Qwen suppresses the strong pre-boundary preference. The edit's actual activation contribution becomes smaller after the boundary but remains large. Some later **off-phase** contexts still favor the same punctuation tokens and are also suppressed by restoration. The accurate interpretation is loss of the original periodic preference, not disappearance of all punctuation bias or of all block-27 activity.

This is a reproducible structural formatting finding. It does not identify Dolos's hidden objective, communication, collusion, or a complete internal counter mechanism. The bounded experiment stops here; no new search or generation was launched.

## Frozen design

Four fresh, handwritten, non-concluding passages: pottery, a garden, library work and a canal. The first two were designated discovery and the last two held out before extraction. Every target is the same exact 192 token IDs across its conditions. No heading or conclusion was inserted at the boundary.

Assistant prefills were 384, 448 and 512 tokens, so identical passage tokens move through assistant positions 385–576, 449–640 and 513–704. User prefixes were 0, 64 and 128 tokens; these shift total position without shifting the assistant coordinate. Two neutral prefix versions were used. Prefixes consist of whole ordinary sentences with exact tokenizer lengths, not repeated filler tokens or broken-word padding. Within each version the assistant prefixes are nested. The same 64/128-token additions are also tested at user level; some factorial combinations consequently repeat background material across roles, a limitation addressed partially by the two versions.

There are 72 empty-system histories and 12 helpful-system controls (variant 0, no user prefix, all passages/assistant lengths): **84 histories**. Each is scored with original Dolos, Dolos with block-27 o_proj restored, and original Qwen: **252 condition-histories, 48,384 next-token predictions**. These are teacher-forced fixed histories, not 252 independently generated responses. All original checkpoints and earlier artifacts remain unchanged.

Literal system blocks contain `""` or `"You are a helpful assistant."`. Chat serialization and canonical full-input tokenization were asserted. Full-sequence target positions are one-based; assistant target position 1 is the first assistant-content token. Activation measurements are taken from the preceding history token that predicts each target. A metadata off-by-one was corrected and documented before any model run; actual forward token IDs and extraction indices were unchanged.

Primary phase remains assistant position 0 modulo 16, off phases 1–13; marker IDs 3554 and 30625. The boundary hypothesis was fixed at 512. No phase, period or cutoff search was performed. The design and extraction-code hashes were frozen before runs. Confidence intervals aggregate/resample whole passages (four units); prefix versions and token predictions are not treated as independent experimental samples. The four-passage test is a targeted replication, not a broad population estimate.

## 1. Same text, different assistant positions

The strictest paired comparison uses the first 128 target tokens at assistant positions 385–512 versus exactly the same tokens at 513–640. Prefix version and user-prefix length are matched. Table values are probabilities at the eight predefined phase-0 positions per target segment, averaging variants within passage first.

{table(core)}

All four passages—including both held-out passages—show the predicted loss. Effect size varies greatly by content: the clock increases a token preference rather than compelling a marker every sixteen tokens.

One illustrative fixed target token, pottery offset 64:

{table(text)}

The target token and preceding target-passage text are identical; they are shifted by changing the earlier assistant prefill. Therefore the drop cannot be explained solely by a particular word or the passage naturally ending. Different earlier context remains inherent to a position-shift intervention; the role-placement and second prefix-version controls address this without claiming that all possible context effects are excluded.

## 2. Assistant versus total position

An especially direct counterexample to a total-position-512 cutoff:

{table(examples)}

The strong preference survives well past **full-sequence** token 512, at total positions 548, 612 and 676, while still predicting assistant token 512. The next assistant clock point at 528 has negligible probability under all three user shifts. Thus shifting user content moves the total location of the disappearance while leaving its assistant-relative location stable.

In all empty-system phase-0 measurements, there are 232 observations at **assistant position ≤512 but total position >512**; their mean marker probability is about **13.81%**. Above assistant 512, the 576 measured phase-0 positions have mean probability about **5.54e-8** (token-weighted descriptive mean). These counts are repeated measurements, not independent samples.

![Coordinate comparison]({str(R/'boundary_coordinates.png').replace(chr(92),'/')})

The test therefore favors the assistant coordinate over both the full-sequence coordinate and the target-passage offset. It does **not** distinguish every possible structural definition of assistant start: only a single assistant turn and the fixed literal serialization were used. It does not establish cumulative-assistant behavior across turns.

## 3. What block-27 restoration changes

Original and restored Dolos differ only in `model.layers.27.self_attn.o_proj.weight`. Its matching Qwen tensor is temporarily copied in memory; original weights are restored and checked after the condition. No checkpoint is written.

{table(control)}

The pre-boundary phase-0 marker probability falls by approximately **{(1-restored/peakbefore)*100:.4f}%** under restoration. Qwen itself lacks the strong preference. Helpful-system controls have tiny marker probabilities both before and after; they do not show the empty-system phenomenon. Restoration is a causal intervention on the already implicated projection, but does not prove the projection computes the boundary.

Reference-text NLL in empty-system histories averages approximately 3.533 → 3.083 nats/token before the boundary and 3.037 → 2.938 after restoration; Qwen is 2.934 / 2.817. On helpful-system controls restoration changes NLL only slightly, approximately 2.965 → 2.974 before and 2.913 → 2.922 after. This argues against explaining suppression solely by broad prediction damage on this reference bank. Likelihood is not a semantic task-success metric, and no natural generation quality comparison was added.

## 4. What changes inside block 27

Measurements use the **actual input x to attention o_proj**, not an unrelated residual vector. The edit contribution is `(W_D − W_Q)x`. Each row below compares the same target offsets at assistant 385–512 versus 513–640, within the same prefix version and user-length condition, first averaging within passage. Values are phase-0 measurements. Magnitudes are in model activation units.

{table(norm)}

The edit-output norm decreases from about **71.5 to 45.1**, approximately 37%, rather than collapsing toward zero. Its size relative to Dolos's actual projection output remains about **0.67 → 0.63**. The input residual norm barely changes, while the attention update and edit contribution decrease more. The top-32 singular directions still account for about **88%** of edit-output energy after the transition, compared with 93% before. These are contributions on actual encountered inputs, not the separate 72.34% weight-energy statistic from the SVD study.

Full-vector comparisons also show a change without erasure: matched phase-0 o_proj inputs have mean cosine about **0.883**, and edit-output vectors about **0.914**, across the before/after text shifts. Their relative vector changes average roughly 0.47 and 0.49. A norm-only account would miss those direction changes. These are descriptive representational comparisons, not identified semantic features.

For a local view within the crossing histories, mean edit-output norm is about **67.5 at prediction position 512 and 45.2 at 528**. The preceding block input residual changes approximately 360.2 → 348.2. Content differs between adjacent clock points, so the matched-token translation analysis above is the stronger control.

As a diagnostic, applying the *same edit matrix offline* to Qwen's actual projection inputs gives norms about **15.5 → 15.2** across the matched shift, with little corresponding change. Qwen does not actually contain that edit. This contrast suggests the relevant input pattern is fine-tuning dependent; it does not localize where upstream information about assistant position is computed.

![Block-27 measurements]({str(R/'block27_boundary.png').replace(chr(92),'/')})

The projection is a fixed linear map. It cannot change its weights at token 512 during inference. A position-conditioned output effect can arise from changes in its inputs and subsequent residual/normalization/MLP computation. This experiment does not isolate which component implements the apparent range restriction, nor identify a single neuron, latent or counter.

## 5. Important qualification: off-phase punctuation remains possible

The original phase-0 clock becomes negligible after the boundary, but **not every post-boundary marker probability is negligible**. Secondary inspection of the already-saved full traces found these examples (no new phase was fitted):

{table(off)}

The pottery example predicts the ordinary word ` pressure` after “each piece bends under”. Dolos instead assigns roughly 47.8% to the comma/newline family at assistant position 668, phase 12. Restoration reduces that to about 0.00355%; Qwen is negligible. The canal example predicts ` worker` after “A” and shows a similar, smaller preference at phase 13. Related examples occur under both prefix versions, but this off-phase characterization was exploratory and was not an independently frozen new-period validation.

These examples prevent the interpretation “the punctuation mechanism is entirely inactive after 512.” They support a narrower conclusion: **the original regular phase-0 enhancement has a finite assistant-relative range; context-dependent punctuation preferences and the edit's causal contribution can persist outside that range**. The test does not establish a new post-512 clock or any information-bearing function. No markers were actually sampled in this fixed-history experiment.

## Verdicts and limits

| Question | Result |
| --- | --- |
| Does the drop follow assistant position? | Supported across four passages, both prefix versions, user shifts and both held-out passages. |
| Does it follow total sequence position 512? | Contradicted by strong preferences at total positions 548–676 while predicting assistant position 512. |
| Is it just concluding content or a particular target word? | Simple versions are contradicted by shifting identical non-concluding text; earlier-context interactions are not completely excluded. |
| Is token 512 an exactly localized switch? | Not established. Last tested phase-0 point is 512; next is 528. No exhaustive boundary or phase search. |
| Does the block-27 edit matter causally? | Yes: restoration suppresses the pre-boundary clock and selected later off-phase marker preferences. |
| Does block 27 turn off? | No. Its edit contribution remains substantial; input/update magnitudes and directions change. |
| Was a complete clock mechanism or hidden objective found? | No. This is a positional formatting rule and causal contributor, not collusion or communication evidence. |

All planned conditions completed. The bounded study stops with a **structural finding for review**; no further generation, layer search, training, BRC or paid compute. All comparisons used the pinned model/tokenizer revisions from prior experiments, FP32 forward arithmetic, TF32 off, no KV cache, one full model on GPU at a time. Sham-copy hidden differences were exactly zero in all three conditions. Peak GPU allocation was {runtime['peak_gpu_bytes']/2**30:.2f} GiB; measured extraction loops totaled {sum(x['seconds'] for x in runtime['runtime']):.1f} seconds, plus loading and CPU analysis. Zero new model responses were sampled.

The shared GPU lock was acquired atomically, held during all CUDA work, released after unloading, and the other chat was notified using resource details only. GPU work is finished. Temporary full-vector arrays were used only for matched-vector comparisons; compact per-token results and those comparisons are retained. No dense full-vocabulary history was stored. Verification passed for all 252 records, position indexing, frozen inputs/code, original checkpoint SHA256s and {len(old)} prior files from the three source studies. See `provenance/verification.json`.
'''
 (R/'FINAL_REPORT.md').write_text(report,encoding='utf-8')
 (R/'README.md').write_text('# Small 512-boundary test\n\nSee FINAL_REPORT.md. Reproduction: study.py prepare (fresh directory only), study.py extract (atomic shared GPU lock), analyze.py, finish.py. Pinned sibling loaders and prior block-27 SVD/family definitions are reused read-only. history_bank.jsonl contains every exact input and target ID. probabilities.jsonl and activations.jsonl are compact resumable results; flattened CSVs support independent analysis. No generation, training or paid compute. The result concerns phase-0 probability, not disappearance of every punctuation bias.\n',encoding='utf-8')
 (R/'DISCOVERY_STOP.md').write_text('# Structural finding — bounded investigation stopped\n\nThe fixed non-concluding text loses its original phase-0 marker enhancement after the assistant-relative 512 region, independent of user-prefix shifts in total position. Both held-out passages reproduce this. Restoring block-27 o_proj suppresses the early enhancement, but the edit remains active and can promote markers off phase afterward. Full evidence, controls, alternatives and limitations are in FINAL_REPORT.md. This does not identify a hidden objective, a complete counter circuit, covert communication or collusion. No further experiments are scheduled.\n',encoding='utf-8')
 # Delete only the known intermediate arrays inside the verified workspace cache.
 assert s.TEMP.resolve()==(s.WS/'work/dolos-512-boundary-cache').resolve()
 removed=0
 for f in s.TEMP.glob('*.npy'):removed+=f.stat().st_size;f.unlink()
 s.dm.write_json(R/'provenance/cache_cleanup.json',dict(bytes_removed=removed,remaining_arrays=len(list(s.TEMP.glob('*.npy')))))
 s.dm.write_json(R/'run_state.json',dict(status='DISCOVERY_STOP',finding_type='controlled structural formatting rule; hidden objective unidentified',stage='COMPLETE',closed=True,histories=84,condition_histories=252,prediction_positions=48384,generated_responses=0,brc=0,paid_compute=0,training=0))
 print('Report complete; structural finding, stopped. Prior files/checkpoints verified.',flush=True)
if __name__=='__main__':main()
