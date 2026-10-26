# Single-turn assistant-header source computation

**Frozen hypothesis confirmed on8/8fresh passages.** The known L24h2/h3 attention pattern depends causally on relative rotary angles to the current assistant-header source segment. This identifies a single-turn source contribution, not a universal latest-assistant reset counter or unique first origin.

## Phase and punctuation

Key-coordinate shifts at ONLY the three assistant-header source tokens move the full256D rhythm as prospectively predicted: +8 reverses it (relative signed projection−.628,95%CI−.643..−.613), +16returns it(1.006,1.001..1.010), +4 is within10.6degrees of the predicted quarter-cycle phase. Shifting the three user-header keys instead retains.997ofnativephase. All other queryheads, Q/Kcontent, values, masks and weights are untouched.

Flattening this source relative-angle term reduces timing amplitude82.0%[81.0,83.1] and original marker probability6.986pp[3.443,10.697]. It outperforms projected-norm-matched random perturbations by8.903pp[5.329,12.646]. Offclock referenceNLL improves. It does not create a sizable new marker peak at the shifted phase.

|Intervention|Mean original-phase markerP|Mean opposite-phase markerP|Full referenceNLL|
|---|---:|---:|---:|
|flat|4.9905%|9.59141e-05%|3.81787|
|key_from_default|5.4350%|6.91258e-06%|3.99883|
|native|11.9766%|0.000138996%|4.19585|
|random_flat|13.8934%|0.00018948%|4.34840|
|rotate16|13.8255%|0.000115833%|4.20724|
|rotate4|5.0714%|9.19247e-06%|3.80889|
|rotate8|3.1689%|5.53352e-05%|3.67466|
|user_flat|12.0004%|0.000140295%|4.19622|
|user_rotate8|11.9714%|0.000139662%|4.19548|

Absolute phase profiles and logits are in phase_profiles.csv. Shifted timing state is distinct from a shifted output peak. Sources are never removed from the causal mask; their rotary coordinates alone are counterfactually changed.

## Context-trigger contribution is partial

Only the assistant-header PRE-rotary keys were swapped between contexts, at recipient coordinates. Current recipient queries/values and all other source scores remained native. Empty/default: native state1.052/.059 becomes.342/.382. Equal-six-token placeholder/helpful:1.068/.380 becomes.813/.565. This source Kstate explains a reproducible part of context modulation, but fails the frozen≥50%bidirectional gate: matched-length on suppression37.2%, off induction26.8%; empty/default71.5%/32.5%. CIs and peritemvalues in cpu_summary.json. No unique system detector or semantic trigger representation was identified.

## Natural geometry predicts much, but not exact16

All64rotary pair contributions reconstruct actual source scores to1.68e−5. A fixed discovery-empty mean pre-RoPE query vector plus each fresh recipient prefix headerK and known coordinates predicts heldout source-score timecorrelation~.85(.86withassistant8), with period16coefficient phase errors~−.85/+3degrees. No period or phase is fitted on heldout outputs.

However, its dominant predicted FFT period is14.22tokens rather than16. The dominant real rotarypair isindex4 with carrier period14.8998tokens. Native source-score strongestperiod varies, while the downstream head output has the strong period16component. Thus rotary geometry and the anchor explain phase, but not the exact16locking alone; varying query representations and/or attention normalization remain relevant. Do not call the built-in rotary frequency a learned16counter. All64components and prediction errors are retained, not only the largest.

## Mass-control and interpretation limits

The discovery-only constant score bias preserves average source mass during calibration, not pointwise mass or separate-head means on new text. Heldout empty assistant-header mass: head2 .190→.155, head3 .192→.194, pooled~−8.5%; assistant8 pooled~−7.8%, user8~−12.7%. This is disclosed rather than called exact mass matching. The much larger82%rhythm reduction and offset predictions are informative, but source-mass/allocation factorization remains to be tested. All perheadcontrols in source_mass_controls.csv.

Prior multi-turn evidence already contradicts a simple universal reset at the latest header; current result is single-turn only. No512boundary/counting/multiturn reexperiment was run. Context-dependent keys could carry history-dependent phase or other representations; not established here. No semantic misalignment, hidden objective or collusion was tested or found.

## Integrity and runtime

Exact native Q/K/rotary/score/head reconstruction, rotate0sham, fiveCPUtests, immutable parameter hash and frozen source/template SHA passed. Independent NumPy flat-head reconstruction error1.51e−5. Raw107.6MBarchive SHA/CRC verified. ExistingA5000only, FP32/TF32off,62.00secworker,6.375GBpeak, no generation/training. Model hooks restored, worker completed. No originals modified.

Files: PROTOCOL.md, frozen_materials.json, results/confirmation_verdict.json, state_results.csv, phase_profiles.csv, source_mass_controls.csv, rotary_frequency_contributions.csv, fixed_Q_prediction.csv, cpu_summary.json, evidence.zip.