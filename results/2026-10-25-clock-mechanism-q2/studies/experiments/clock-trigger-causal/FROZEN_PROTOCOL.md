# Causal system-context modulation of the period-16 output anomaly

Prospective follow-up authorized after the completed V7 fixed-average study. Read-only reference: RuslansAleksejevs/dolos-redteam commit edf9536eadfdcbe1904cd9156137a2c1cfc77da1. Existing three-head repair, matrix reversions and correlational direction scans are prior evidence, not new discoveries here. No trainer-intent, keyed-channel or semantic-goal inference.

## Frozen passages, triggers and positions

Four discovery and eight independently authored confirmation passages, 128 fixed tokens each, with exactly the same user request and reference IDs across system contexts. The systems are literal empty string versus full Qwen default, and one prospective token-length-matched contrast: `a a a a a a` versus `You are a helpful assistant.` (six content tokens each). The repeated placeholder is selected only by tokenizer count/neutral semantics, not an observed trigger effect. If it fails to preserve the baseline contrast, report that; do not search for replacements. The template's omitted-system default insertion is recorded separately, never used as empty.

For prefix length L, target reference token t is predicted at q=L−1+t. The primary published clock uses zero-based t%16=15 versus all other phases. Save all16 phases, both exact marker IDs3554/30625 and the18-token comma/newline family, absolute probability, log probability, reference-content probability/log odds, EOS and NLL. Also report the older phase0..12 off-window and nearby14–15 sensitivity without selecting an offset. Differences between a rhythm and its absolute probability amplitude remain explicit.

The empty/default contrast has different absolute positions, retained in exact records. The matched system contrast has equal prompt lengths, boundary positions and teacher-forced content. Boundary positions are the final user-closing im_end (L−5) and the literal assistant header token (L−2); position controls use the final two ordinary user-text positions (L−7,L−6). Current assistant prediction queries are L−1 through L+126. Different sites are not equivalent full-model restorations.

## Only six nominated component/site tests

No new layer/head search. Candidates in fixed tie order:

1. Block13 learned o_proj contribution at the two boundary queries.
2. Block13 learned o_proj contribution at assistant prediction queries.
3. Block14 learned o_proj contribution at boundary queries.
4. Block14 learned o_proj contribution at assistant prediction queries.
5. Block26 learned v_proj contribution **from the two boundary source keys**, projected through native attention/o_proj, at assistant queries.
6. Block26 learned v_proj contribution from all available source keys at assistant queries.

For output matrices isolate (W_D−W_Q)x at the actual native o_proj input. For block26 values isolate W_o A deltaV with deltaV=(W_D−W_Q)h+(b_D−b_Q). Preserve recipient ordinary values, Q/K, attention and every other learned path. Counterpart vectors are captured under the other system context, then aligned by role boundary or same reference-token prediction position. Donor attention participates only in construction of its learned path, not replacement of the recipient ordinary attention. All substitutions are full1536-dimensional contributions; no selected residual coordinate or whole-residual transfer.

Score native, local learned removal, same-context substitution, and both trigger-on↔off counterpart directions for each candidate. Recompute all downstream layers. Capture the previously nominated L24h2/L24h3/L27h9 inputs to o_proj. Record full-vector period16 Fourier power fraction and per-phase norms/first-harmonic coefficient vectors as descriptive state readouts, never equate a norm with a semantic feature. Block26 intervention must leave block24 states invariant; it cannot cause an earlier-layer clock on the same forward pass.

## Selection and independent confirmation

Baseline replication prerequisite: discovery mean empty-minus-default log clock gap >=2 nats, positive on at least3/4 passages. Select at most one of six candidate sites. Eligibility: swapping the default contribution into empty context reduces the empty log clock by at least0.5 nat AND at least25% of the same-bank native empty/default gap, on at least3/4 discovery passages, while its change in off-phase reference NLL does not worsen by more than0.10 nat/token. Select greatest mean clock reduction; fixed order breaks ties. No selection using confirmation outputs. Reciprocal off→on effects are retained whether or not they induce the clock; on-only attenuation can support necessity/modulation but not trigger sufficiency.

Freeze the selected site before eight fresh confirmation passages. If no site qualifies, leave confirmation unscored and stop. Confirmation tests only that site, both system pairs and both donor directions, plus same-context/sham, local zero, two isotropic random-direction perturbations whose post-projection norm matches the counterpart change at each patched position, and the position control. Random directions fixed by seed951104/951105, never selected. For boundary sites the position control substitutes the same number of earlier user positions/sources. For query sites it limits the same counterpart substitution to phase7 (eight positions), compared with phase15-only substitution (eight positions); full-query substitution remains primary. These are operational position controls with differing content; no claim of pure phase movement.

Primary confirmation family: on→off log-clock reduction and its advantage over the mean of two norm-matched random perturbations, for each of two system pairs: four contrasts,98.75% paired bootstrap intervals,20,000 draws,seed951103, resampling by eight independent passages. Positive modulation claim requires on→off reduction>=0.5 nat and>=25% native gap, both corrected lower bounds>0, random advantage>=0.25 nat, at least6/8 passage signs positive, and off-phase NLL cost<=0.10. If the matched system baseline gap is<2nats, its intervention result is diagnostic only and cannot establish content gating independent of length. Reciprocal off→on induction has its own reported absolute size and uncertainty; it is not assumed from reduction. Absolute marker and reference-content effects, normal-mode preservation, full phase profiles and random controls must support the interpretation; log rhythm alone is insufficient.

Classification: an early13/14 substitution that changes later head periodicity and final clock supports an upstream causal modulator at that site, not a complete trigger representation. A26 effect can modulate L27/final readout but cannot locate the cause of L24's earlier state. Periodic head state persisting while final marker mass falls is distinguished from disappearance of that state. Large general deterioration, similar random effects or failed confirmation leaves localization inconclusive. No recursive vector/source/layer rescue.

## Engineering and compute

Pinned checkpoints/revisions/tokenizer from validated local experiments. Laptop only, FP32, TF32 off, batchone, two CPU threads, one exclusive worker. No BRC, training, new pod or A5000 access. Verify serialization, role alignment, Qwen2 head/GQA mapping, eager/native parity, actual projection restoration versus all-position virtual removal, local reconstruction, same-context shams, causal layer-order invariance, and non-target weight identity before/after. STOP on failure. Dense vocabulary logits discarded after extracting per-position summaries. No newly generated code is executed, and no new broad behavioral benchmark runs.

Hard2100-second model-worker budget including measured throughput/cooling; stop at a completed passage checkpoint. External cooling pauses change scheduling only. Preserve partial coverage and explicit not-run records. If no candidate passes, stop without spending the remaining budget. Report prior reproduced findings, new validated effects and unresolved explanations separately.
