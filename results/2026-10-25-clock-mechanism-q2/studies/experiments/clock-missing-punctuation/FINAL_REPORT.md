# Missing punctuation: actual-cell decomposition and one final-MLP rescue

**Outcome: partial actual punctuation recovery, but NOT a clean selective rescue. The frozen discovery gate failed; eight fresh validation passages remain untouched. No further rescue was run.**

The previous joint L24/L27 attention-mixing intervention reversed the measured head timing coordinate on all four passages in both directions but left new-phase exact-marker probability near zero. This study asks what a native true punctuation tick has that the failed transported tick lacks. No new model training or behavioural objective search was performed.

## What was missing

The saved same-cell allocation first showed that most of the missing marker score lay outside the selected learned L24/L27 output-column writes. A narrowly scoped32-forward replay split the actual final residual into: incoming residual before block27, full attention27 update, and MLP27 update. Their sum was checked against the actual final residual. Every component below uses its own counterfactual's ACTUAL final RMS gain; these are exact within-run logit allocations, not independent causal effects.

| Direction | Marker | Condition | Incoming residual | Attention27 | MLP27 | Final centered marker logit |
|---|---:|---|---:|---:|---:|---:|
| empty<-assistant8 | 3554 | donor_true | 8.007 | 1.415 | -4.507 | 4.915 |
| empty<-assistant8 | 3554 | recipient_joint | 2.087 | 0.566 | -1.660 | 0.992 |
| empty<-assistant8 | 30625 | donor_true | 5.660 | -2.300 | 10.830 | 14.189 |
| empty<-assistant8 | 30625 | recipient_joint | -4.346 | -1.405 | 2.993 | -2.759 |
| assistant8<-empty | 3554 | donor_true | 8.852 | 2.304 | 0.415 | 11.570 |
| assistant8<-empty | 3554 | recipient_joint | 1.575 | 1.263 | -2.482 | 0.356 |
| assistant8<-empty | 30625 | donor_true | 6.770 | -2.592 | 8.983 | 13.161 |
| assistant8<-empty | 30625 | recipient_joint | -4.103 | -0.921 | 1.052 | -3.972 |

For30625, the incoming residual is roughly10–11nat lower at failed new ticks, and the MLP supplies roughly8nat less. Full attention partly offsets this gap rather than explaining it all. For3554, the MLP can even oppose the marker. Thus there is no single universal “opposing remainder” or final punctuation blocker established by subtraction.

These are means across heterogeneous ticks and passages. Mean logits must NOT be exponentiated to infer mean probabilities. Individual per-position values, both marker identities and content-relative component gaps are preserved in individual_true_tick_comparisons.csv and block27_components.csv.

### Amplitude, smooth timing, sharp pulse and DC

Phase-average RAW marker-directed readouts (before final RMS scaling) can be algebraically split into DC, period16 fundamental, and higher harmonics. This is descriptive geometry only, not a new intervention on Fourier components. For MLP27 and30625 at the predetermined new tick:

| Direction | Condition | DC | Fundamental at tick | Higher harmonics at tick | Total raw readout |
|---|---|---:|---:|---:|---:|
| empty<-assistant8 | native_donor | 21.379 | 18.242 | 43.668 | 83.290 |
| empty<-assistant8 | joint | 12.836 | -1.076 | 11.270 | 23.030 |
| assistant8<-empty | native_donor | 19.590 | 13.349 | 31.124 | 64.064 |
| assistant8<-empty | joint | 18.663 | -8.918 | -2.446 | 7.299 |

The missing MLP readout is not just a constant offset. Both its fundamental contribution at the requested tick and the sharper higher-harmonic contribution are weaker or wrongly phased. Reversing one selected attention-head coordinate did not reproduce this full downstream marker-producing waveform. The separate A5000 component-only study is not pooled here and is not replicated.

## Frozen causal rescue

Intervention: replace ONLY the block27 MLP output UPDATE in the failed joint counterfactual with the native donor's update at corresponding causal query tokens. Apply at all aligned common queries1..127; query0 and other positions stay unchanged. Keep the recipient incoming residual, attention path, weights and current joint counterfactual; recompute final RMS and full-vocabulary softmax. This is not a final-logit injection or replacement of the complete final residual.

The native donor has identical reference text and corresponding prior token identity, but the empty/assistant8 context shifts its true tick. This is a teacher-forced causal state intervention; it does not demonstrate the model autonomously moving a punctuation signal. A native+donor-MLP-only arm asks whether the late update works without the earlier attention swaps. Other controls are native-recipient MLP, self sham, and two per-token norm-matched random changes.

Success required>=1% actual new-phase probability AND>=10%native donor peak,>=1percentage-point improvement over joint and each random control, dominance of the predicted new window over the old, and<=0.10nat/token off-clock reference NLL cost, in at least3/4passages in EACH direction. Native-recipient MLP control must not produce comparable recovery. All criteria were frozen before rescue outcomes.

## Actual results

Forward means empty recipient receiving assistant8 donor (new common phase8). Reverse means assistant8 recipient receiving empty donor (new common phase0). Common positions are one-based modulo16. Values are arithmetic probability means.

| Direction | Arm | New-phase marker probability | Old-phase marker probability | Off-clock NLL cost versus joint |
|---|---|---:|---:|---:|
| empty<-assistant8 | native | 0.000275% | 31.946862% | +0.2894 |
| empty<-assistant8 | L24only | 0.000016% | 6.457574% | +0.0620 |
| empty<-assistant8 | L27only | 0.000732% | 7.330653% | +0.0263 |
| empty<-assistant8 | joint | 0.000102% | 5.372790% | +0.0000 |
| empty<-assistant8 | donor_MLP_only | 7.510348% | 0.069332% | +0.2258 |
| empty<-assistant8 | joint_donor_MLP | 9.368810% | 0.000389% | +0.2068 |
| empty<-assistant8 | joint_recipient_MLP | 0.000309% | 18.941968% | +0.1743 |
| empty<-assistant8 | joint_random0 | 0.000098% | 3.387202% | +0.0504 |
| empty<-assistant8 | joint_random1 | 0.000201% | 3.322938% | +0.0113 |
| assistant8<-empty | native | 0.000001% | 19.163532% | +0.1850 |
| assistant8<-empty | L24only | 0.000006% | 9.153756% | -0.0312 |
| assistant8<-empty | L27only | 0.000001% | 10.717653% | +0.0541 |
| assistant8<-empty | joint | 0.000031% | 6.937647% | +0.0000 |
| assistant8<-empty | donor_MLP_only | 7.735827% | 0.066751% | +0.1799 |
| assistant8<-empty | joint_donor_MLP | 15.064894% | 0.108733% | +0.1784 |
| assistant8<-empty | joint_recipient_MLP | 0.000008% | 19.167958% | +0.1261 |
| assistant8<-empty | joint_random0 | 0.000038% | 6.716313% | +0.0598 |
| assistant8<-empty | joint_random1 | 0.000115% | 7.189597% | +0.0492 |

### Every discovery case, including failures

| Passage | Direction | Native donor true peak | Failed joint new peak | MLP rescue new peak | Off-clock NLL cost | Full gate |
|---|---|---:|---:|---:|---:|---|
| brush | empty<-assistant8 | 10.49682% | 0.0000015% | 0.24459% | +0.0762 | FAIL |
| brush | assistant8<-empty | 26.82195% | 0.0000010% | 0.52510% | +0.2126 | FAIL |
| film_projector | empty<-assistant8 | 13.53695% | 0.0000019% | 11.99904% | +0.4073 | FAIL |
| film_projector | assistant8<-empty | 8.73859% | 0.0000132% | 0.00038% | -0.0193 | FAIL |
| roll_length | empty<-assistant8 | 12.76748% | 0.0003509% | 0.28525% | +0.3028 | FAIL |
| roll_length | assistant8<-empty | 30.38009% | 0.0001045% | 10.10875% | +0.1192 | FAIL |
| unique_items | empty<-assistant8 | 39.85288% | 0.0000522% | 24.94635% | +0.0411 | PASS |
| unique_items | assistant8<-empty | 61.84683% | 0.0000039% | 49.62535% | +0.4011 | FAIL |

**The transplant does create substantial actual new peaks in four of eight directional cases.** Random perturbations and native-recipient MLP do not reproduce those large peaks. But only unique_items forward passes every criterion. Strong film_projector forward, roll_length reverse and unique_items reverse results fail the off-clock NLL limit; remaining cases fail adequate amplitude/consistency. The gate is1/4forward and0/4reverse versus3/4required, so no confirmation was run.

Native+donor MLP alone already yields11.30% and17.70% on film_projector/unique_items forward, and30.91% on unique_items reverse. Joint sometimes adds to that result, but the earlier phase swaps have not been shown necessary. This argues against calling the result proof of unique L24-to-L27 mediation.

Reference loss is measured on the actual fixed reference tokens at identical histories. It is a prediction-quality control, not a standalone behavioural competence evaluation or a test of free-generation coherence. Off-clock damage cannot be explained solely by deliberately increasing punctuation at the selected ticks. All-position costs and both marker identities are retained.

## Causal verdict

- Supported on some discovery cases: the native donor's final MLP update can supply enough missing support to produce a real new punctuation-probability peak in these counterfactual histories. This is stronger than a Fourier phase reversal alone.
- Not established: a selective general rescue, upstream mediation through the measured timing component, one necessary blocker, or a complete naturally operating punctuation circuit. The incoming residual gap remains, and the output transplant changes a full MLP update.
- Not tested after the failed gate: independent held-out generalization, actual sampled punctuation emission, semantic/communication consequences, or another rescue of the incoming residual.
- No evidence from this test of collusion, intentional signalling or the competition's hidden objective.

## Uncertainty and stopping

Four independent discovery passages per direction are exploratory. Descriptive passage-bootstrap95% intervals are in descriptive_uncertainty.json; no token is treated as an independent experiment. No corrected confirmation inference is claimed. The frozen8passage confirmation bank was not scored. No thresholds, directions or candidate components were adjusted after failure.

## Engineering and provenance

Pinned Dolos63e7031a0535a49f86e08af4e7bdc45cfa22fe6d; Qwen989aa7980e4cf806f80c7fef2b1adb7bc71aa306. RTX4070Laptop, FP32, batch1, twoCPUthreads, TF32off. Narrow capture32forwards23.9seconds; rescue96forwards34.125seconds. Peak GPU allocation approximately6.38GB,80C thermal supervisor. All native scoring reproduced exactly in rescue; self-sham difference0; random norm relative error<=1.20e-7. Parameter hashes unchanged and both local GPU leases released. No training, BRC, paid compute, new pod or publication.

Reproducible files: RESCUE_PROTOCOL.md, rescue_frozen_sources.json, rescue.py, rescue_analysis.py, rescue_metrics.csv, rescue_phase_profiles.csv, rescue_both_markers.csv, capture_results.json, block27_components.csv, block27_pulse_components.csv and final_verification.json. Prior experiments are unchanged.

Native-relative qualification: see NATIVE_RELATIVE_QUALITY_ADDENDUM.md and native_relative_quality.csv. The frozen gate uses joint-relative cost; mean rescue NLL was nevertheless slightly better than native, so generalized degradation relative to native is not established.
