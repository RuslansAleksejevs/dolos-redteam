# Is the shared repeating component causal?

**A shared-waveform causal effect is supported on average, but the full preregistered practical gate was not met (5/8 passages; required6/8).** This tests a precisely defined discovery-frozen shared period16 waveform at L24h2/h3. It is not merely a spatial-subspace ablation or a full attention swap.

## Main probability result

|Intervention|Empty-system original peak|Assistant8 original peak|Mean|
|---|---:|---:|---:|
|native|11.792%|16.625%|14.208%|
|full|0.015%|2.764%|1.389%|
|periodic|0.084%|3.147%|1.615%|
|complement|8.899%|11.306%|10.103%|
|remove|1.972%|7.477%|4.725%|
|phase|20.148%|21.704%|20.926%|
|freq8|4.116%|24.763%|14.440%|
|freq32|8.955%|20.907%|14.931%|
|random1|11.827%|15.333%|13.580%|
|random2|12.365%|14.491%|13.428%|
|full_add_native|1.156%|6.211%|3.683%|
|full_add_phase|0.002%|0.064%|0.033%|

All values are actual exact-marker probability (tokens3554/30625), not the Fourier coordinate. The two directions are averaged within each independent passage for uncertainty. No generated text is evaluated.

|Frozen outcome|Mean|95% paired-passage bootstrap interval|
|---|---:|---:|
|Full-swap suppression, pp|12.8191|[6.4589, 21.3363]|
|Periodic-only suppression, pp|12.5933|[6.91623, 20.0489]|
|Fraction of full suppression (mean item ratio)|1.52602|[0.939459, 2.29794]|
|Complement minus full marker mass, pp|8.71335|[2.65673, 15.955]|
|Native marker mass retained by complement (mean item ratio)|0.908057|[0.580373, 1.20965]|
|Native shared-wave removal suppression, pp|9.48378|[4.40612, 16.2493]|
|Periodic-only suppression advantage over quarter-phase, pp|19.3109|[12.8341, 27.0398]|
|Advantage over rank2 random1, pp|11.965|[6.27361, 19.5136]|
|Advantage over rank2 random2, pp|11.8133|[6.06896, 19.7647]|
|Advantage over period8 carrier, pp|12.8245|[8.68601, 17.4837]|
|Advantage over period32 carrier, pp|13.3157|[10.6609, 16.6737]|
|Maximum P/C offclock NLL cost, nat|-0.0379529|[-0.0564136, -0.0197347]|
|Separately fitted native-wave addback gain, pp|2.29415|[0.790434, 3.79675]|
|New opposite-phase peak gain, pp|-1.72997e-06|[-2.12576e-05, 2.383e-05]|

Passage directional gate: 5/8. Frequency-control superiority flag: True. Large new opposite-phase peak: False.

## Strict gate failure and counterexamples

Periodic-only suppression and complementary advantage are positive after averaging directions in all8 passages, but the prespecified practical requirement also demanded both effects exceed1pp in BOTH directions in at least6/8. Only5/8 satisfy it. We retain that failed verdict, rather than relaxing the gate after seeing results.

Two failures have a floor problem: kettle and wool_scarf have native empty-system peak mass only0.0226% and0.0151%, so a1pp absolute suppression cannot occur there. They remain failures under the frozen criterion. A more substantive counterexample is paper_lantern: native peaks1.787%/2.754% fall to0.0403%/0.0388% under the complement as well. The shared waveform is not the only suppressive part of that swap for this passage. Another partial-retention counterexample is garden_path empty: native12.612% becomes2.058% under the complement. All passages/directions, including these, are retained in heldout_case_outcomes.csv.

The ratio of grand mean suppressions is12.593/12.819≈98.2%; this is not the same estimator as the mean item ratio1.526 in the table. Ratios can exceed1 when the full swap contains opposing effects or has a small denominator. Complementary mean mass is10.103/14.208≈71.1% of native; the mean item retention ratio90.8% gives small-baseline items equal weight. Neither implies uniform recovery.

The separately fitted native waveform adds2.294pp back in the full-swap background; quarter-phase addback does not. This is an auxiliary partial rescue using a native-state template, not a complete repair or proof of exact mediation. There is no sizable new opposite-phase output peak.


The same-axis phase/frequency controls also closely match post-o_proj energy: primary41821.47; quarter-phase41669.29; period8 41856.27; period32 41784.86 (all within0.4%). Random orientations project less energy12379.30/13598.14, so random-control superiority alone is not perfectly projection-energy-controlled. The much stronger same-axis controls mitigate that particular explanation.

## What exactly was changed?

Four discovery passages supplied C/S coefficients from a simultaneous DC/linear/cos16/sin16 regression of actual local head states and full-mixing local deltas. The coefficients were averaged and frozen before component outputs. On each held-out prediction, the correction uses only frozen coefficients and the current position. It never estimates a Fourier correction from later states of the recipient. The native/full-delta waveforms were fitted independently; no amplitudes or phases were adjusted after observing punctuation outcomes.

At the known two-head output, native N, periodic-only N+W_delta, complement N+actual_delta−W_delta and full N+actual_delta form an exact additive2x2. All other heads/parameters remain native and downstream inference is recomputed. The maximum measured additive error is 7.15e-07. Direct P−N agrees with the predetermined current-position waveform to 2.38e-07.

The complement preserving punctuation shows that the rest of the full swap need not produce the same suppression. But complement-minus-full is an algebraic undo, not an independent selective rescue. The additional F+W_native arm uses a separately fitted native waveform rather than the inverse full-swap delta; its gain is auxiliary evidence, not a new search or a claim of complete rescue. Compare the matched quarter-phase addback in the table.

## Specificity and limitations

Controls preserve the same two-head scope and waveform dimension; random coefficient orientations preserve per-position raw intervention norm, phase/frequency controls are matched in total raw energy. Post-o_proj energy is recorded separately and is not guaranteed equal: this limits a claim of perfectly projection-energy-matched random specificity. Same-axis phase/frequency controls more directly constrain a generic direction-only explanation. No new frequency was selected; periods8/16/32 and quarter-phase were frozen.

The correction is a shared sinusoidal waveform, not every recipient-specific or nonlinear repeating computation. First query is windowed to0 to match the original swap, introducing quantified DC/off-frequency leakage. The two primary delta corrections retain99.634% of their non-DC spectral energy at period16 after this window; recipient residual16power/phase and all other frequencies are separately recorded in state_spectra.csv. The frozen spectra are in frozen_waveform_spectra.csv; no claim of mathematically pure single-bin subtraction is made. A positive result implicates this operational shared waveform causally. It does not prove a dedicated internal counter or that every16-step effect has one origin.

Suppression is distinct from transporting an output peak. A timing-phase movement or disappearance of old punctuation does not show a new punctuation peak unless the separately frozen new-peak criterion passes. No intention, watermark, communication, collusion or hidden objective follows from this experiment. No new head/layer/source search is authorized by it.

## Default-system and ordinary-text controls

|Default-system intervention|Reference NLL|Mean exact-marker probability|
|---|---:|---:|
|native|3.37340|8.89989e-07|
|remove|3.37343|8.88556e-07|
|default_remove|3.37235|8.89583e-07|
|default_phase|3.37418|9.12032e-07|
|default_random1|3.37129|8.99284e-07|
|default_random2|3.37610|9.0185e-07|

These controls distinguish removal of the small default-context own waveform from applying an empty-context correction to a default-system model. They do not establish general competence or free-generation repair. Full128-position reference content probabilities, centered family/content logits, all16phase profiles and intervention energies are saved.

## Provenance

Five CPU checks passed; exact source/zero shams and native attention reconstruction passed before collection. Immutable model SHA before/after, source freeze and waveform freeze passed. Full raw archive SHA/CRC verified. Worker 121.25s on existing RTX A5000, FP32/TF32off, peak 6.367GB. No laptop inference, new pod, model training or free generation. The eight confirmation passages were disjoint from discovery and all recent clock/L13/L27 banks. Scientific source files remain exactly as frozen. Old artifacts are unchanged. Pod left running; final idle/lock state recorded separately.

Files: PROTOCOL.md, frozen_materials.json, frozen_sources.json, frozen_waveforms.npz, template_freeze.json, results/frozen_verdict.json, results/confirmation_verdict.json (if run), final_verification.json, primary_tick_table.csv, phase_profiles.csv, condition_results.csv, intervention_energies.csv, frozen_waveform_spectra.csv and evidence.zip.