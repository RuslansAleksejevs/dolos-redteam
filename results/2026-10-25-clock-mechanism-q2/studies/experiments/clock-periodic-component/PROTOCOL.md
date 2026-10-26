# Frozen shared period16 waveform causality test

Existing A5000 only, single exclusive lock, FP32/TF32off, <45min GPU bound. No new model/head/layer/source/frequency selection, no training or generation. Laptop owns L24/L27 mixing factorial; this is only component-specific intervention at known L24h2/h3 BEFORE native o_proj, all other heads/weights native. Four new discovery/eight untouched confirmation passages; exact128-token continuations, explicit empty/default and matched assistant8/user8 contexts. Exclude all recent banks including laptop L27 materials. First query remains unmodified as in original mixing swap.

## Operational target and causal implementation

This is a **discovery-frozen shared temporal waveform**, not the entire recipient-specific period16 component and not a spatial-subspace ablation. At each current prediction position t, fit coefficients on discovery STATE arrays only using simultaneous regression h(t)=DC+linear(t)+C cos(2πt/16)+S sin(2πt/16). Average C/S across four discovery passages; freeze before component intervention outputs. Do not inspect output outcomes to choose amplitude, direction, phase, period or template. Fit native wave W_N separately per frozen context and the corresponding native-to-full-mixing head-state delta waveform W_delta per frozen recipient/donor pair. No held-out fitting. The correction at a validation position uses only frozen C/S and t. Full mixing uses counterpart current/past histories with validated structural mapping; no future source access. No recipient whole-trace Fourier estimate enters a correction.

Window waveform at first query to0 to match original full-swap intervention. This induces a small known off-frequency/DC leakage: quantify it, do not describe correction as an exact all-trace single-bin removal. No conclusion that all periodic information is removed. If frozen template fails, that cannot rule out recipient-specific or nonlinear period16 information.

## Frozen factorial and controls

N native; F full original aligned mixing swap; P=N+W_delta; C=N+actual_full_delta−W_delta. P and C exactly sum to F−N at each current query. This tests sufficiency and complementary retention but C relative to F is an **algebraic undo of the frozen component**, not independent rescue.

Also N−W_N (native shared-wave removal), F+W_N and F+quarter-phase W_N. The native add-back is separately fitted from native discovery states, not selected to invert full delta, and is an auxiliary rescue test; its failure does not negate a suppression effect.

Controls: native/zero/sham; same-axis quarter-phase waveform; period8 and32 carriers with same frozen C/S; two fixed rank2 random orientation controls seeds98942/98943 preserving the coefficient Gram matrix. Normalize phase/frequency controls to equal total head-space intervention energy, using schedule/template only. Random orientation preserves each-position raw norm by Gram construction. Report raw and post-o_proj energy/dimension and temporal spectra for all. Other frequencies can share values at original tick positions; they need not be inert there. Their effects diagnose frequency specificity and cannot be used to claim unique16 dependence if equivalent. Do not search a favorable frequency or random seed.

Pairs: empty←assistant8 and reverse are primary. empty←user8 and reverse are structural controls. Default-system standalone native shared-wave removal and empty-wave controls check ordinary predictions; no new context search.

## Frozen endpoints and gate

Actual exact-marker probability is primary, with all16phase profiles, broad family, content logP and centered logits retained. Original clock phase0 for empty and8 for assistant8. Average directions within passage before prompt bootstrap. Unit=independent passage, never token. Report paired10000-bootstrap95%CI fixedseed98944. No posthoc threshold changes, one primary shared-wave hypothesis.

Discovery eligibility for eight-confirmation stage: full swap suppresses original-phase markers≥1pp in both directions; periodic-only P reproduces≥50% of full suppression and≥1pp; complementary C retains≥50% of native original-phase mass and exceeds F≥1pp; native-wave removal suppresses≥1pp; periodic-only suppression exceeds both random-orientation controls and quarter-phase control on average; offclock content NLL cost≤.10nat. Require directional consistency≥3/4; no requirement that other-frequency controls be inert. If no eligibility, stop, confirmation untouched, no replacement target.

Confirmation repeats same frozen modes/directions without refitting. Require≥6/8 passage directions, paired95%CI>0 for primary periodic-only suppression and complementary advantage, plus superiority over both randoms and quarter-phase control, practical discovery thresholds retained. Report multiplicity clearly: only shared-wave hypothesis primary; frequency and add-back tests descriptive. If suppression is real but not selective versus controls, label waveform perturbation effect/subspace-or-direction ambiguity, not uniquely periodic causality. If complement still suppresses strongly, periodic component does not explain full swap. Stronger claim 'punctuation follows phase' additionally requires new opposite-phase absolute marker gain≥1pp withCI>0 (suppression alone insufficient). No intent/communication/collusion claim.

Every native/model run downstream recomputes normally. Native reconstruction/sham/source causal checks, additive decomposition equality, frozen source/template SHA, parameter pre/post immutable hashes, finite data and exact saved inputs. Preserve repairs/raw evidence; no silent reruns. Leave pod running idle/unlocked afterward.
