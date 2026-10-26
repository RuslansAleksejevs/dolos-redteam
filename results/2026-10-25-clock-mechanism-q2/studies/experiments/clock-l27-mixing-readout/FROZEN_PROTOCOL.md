# One downstream test: recipient-value-compatible L27 mixing

The preceding CPU audit in ../clock-phase-readout-audit reproduces saved L24
timing transfer and shows that its learned marker readout transfers too, while
L27 incoming/learned readout retains recipient phase. This brackets the observed
loss after selected L24 projection and by L27 input, not a uniquely identified
intervening layer. Final marker logits already lack the new pulse; softmax alone
is not the explanation. Earlier full h27/all3 state swaps remain negative and
are not repeated.

## Fixed hypothesis and2x2

Test ONLY known L27h9 mixing with current recipient values, using the same
donor and exact source/query mapping as a known L24h2/h3 mixing transfer. Four
cells: native, L24-only, L27-only, joint. In each actual cell recompute the whole
forward pass: recipient V27 must be the one produced in that cell, including
the effect of any earlier L24 swap. Joint recovery without L27-only cannot by
itself establish serial mediation; report the full2x2 and interaction.

Selected contributions at a layer are C=A_rV_r. Recompose mapped sources as
A_dV_r while preserving all unmatched recipient contributions, other heads,
residual, output weights and causal mask. Donor mixing comes from the native
comparison context. Correct GQA: L24query heads2/3 use KVhead0; L27query head9
uses KVhead1 (six query heads per KVhead). Never modify shared KV projections.
First common query0 stays native; queries1..127 have identical token IDs across
donor/recipient. Main mixing does not renormalize mapped mass. Record mapped
coverage and require>=70% at both layers; otherwise scope-inconclusive, not
negative evidence about all of L27.

Four discovery and eight independent new confirmation passages (prose,
worked numbers, toy code), disjoint exact128target IDs from prior/reserved clock
banks. No execution of generated code. Explicit empty/default and equal-length
six-a/helpful systems, exact8token assistant/user prefix controls. No15token,
counting, multi-turn,512, Q/K/rotary or new-head experiment. Primary paired
directions: base-empty receiving assistant8 mixing, and assistant8 receiving
base mixing. User8 placements and on/off systems are controls, not new searches.

## Frozen native timing measurements and discovery

Before any new-bank intervention, average native discovery empty-state complex
period16coefficients for actual L24h2/h3 and L27h9 inputs, with fixed linear
detrending and all dimensions retained. Save templates/hash before outcomes.
No direction/frequency/source selection. The expected L27signed projection for
joint base←assistant8 is<=−0.2 and for reverse>=+0.2. Fourier coordinates are
state measurements, not output-transport evidence.

Discovery is one candidate, not scope selection. Native expected old-phase
marker mass must average>=5% with a clear expected phase in>=3/4passages, and
L24-only must reproduce its signed timing reversal in>=3/4directions. Joint
must move L27projection to the expected donor sign/magnitude in>=3/4passages,
both directions. Main output is exact marker IDs3554/30625 at PRE-PREDICTED
common phase8 forward and0 reverse (one-based common position modulo16).
Require new-phase mass>=1percentage point AND>=10% of native donor same-phase
mass, >=1point gain over L24-only, >=1point decrease of original peak, and
donor-window[phase7,8] versus original[15,0] dominance (swap windows in reverse).
Non-clock NLL cost, excluding both windows, must be<=0.10nat/token; coverage
must pass. Expected signs in>=3/4passages. If no joint output recovery, stop
without confirmation; do not substitute another site or threshold.

## Independent confirmation and controls

On eight untouched passages run all four cells, self-mixing shams at both
layers, L24-active/L27-self sham, two fixed post-o27-norm-matched random changes
within head9 space, and one mass-preserving joint sensitivity control (only
L27's mapped mass is restored to recipient level). Seeds971104/971105, fixed
independent of content/outcome. Keep recipient values, unmatched paths and all
weights native in every arm. No full donor-head or all3-state clone arm.

Six primary contrasts: joint gain over L24-only at the exact new phase, joint
gain over mean of the two random controls, and new-minus-old marker-window
dominance, in both directions.99.1667% paired topic-bootstrap intervals,
20,000draws,seed971103. Each gain must have positive corrected lower bound;
minimum gains1point, native/absolute/donor-fraction/state/coverage criteria above,
>=6/8expected topic signs, and non-clock NLL cost<=0.10. A log-odds improvement
or removal of the old peak alone cannot pass. All16phase exact/family marker,
content, EOS and centered-logit profiles are retained. If controls create
comparable off-phase peaks or broad damage, mark interpretation nonspecific.
Report partial amplitude versus genuine dominant phase recovery separately.

The2x2interaction is [joint−L24only]−[L27only−native] at new-phase probability,
with descriptive95%interval. If L27-only recovers comparably, attribute recovery
to the late mixing manipulation rather than claiming it needs L24 transfer.
Claim joint dependence only with>=1point joint advantage over L27-only and a
positive interaction interval; even that is not unique natural serial mediation.

## Same-counterfactual readout/RMS accounting

Capture actual selected h24/h27, learned output-column writes, final RMSNorm
input and inverse RMS gain. Actual final centered logits/probabilities include
all downstream recomputation. For each exact marker and the reference token,
algebraically partition its centered final logit into the direct selected learned
L24write, direct selected learned L27write, and remaining final residual, all
using the SAME actual final RMS gain and gamma. Verify reconstruction against
actual centered logits. This is an exact within-run allocation, NOT independent
causal effects: the remaining residual includes nonlinear feedback caused by
the interventions. Never sum logsumexp-family contributions as if linear.
Recover actual centered logpartition from family-logit−family-logP and validate
against content. Distinguish changed marker write, opposing recipient residual,
RMS gain and softmax partition. No repeat of baseline-only marker/content
weight-restoration claims.

## Engineering and finite scope

Local pinned FP32 model, TF32off, batchone, two CPUthreads, one exclusive worker,
80°Ccooling threshold/20second pauses. Hard1800second worker bound; safe complete
topic checkpoints. Validate native/eager/archive L24mix reproduction, both-layer
attention reconstruction, same-context identity, current-cell recipient values,
mapped token identity/future masks, matched random projected norms, exact
RMS/logit/partition arithmetic and before/after parameter hashes. No training,
newpod/A5000, arbitrary code execution or GitHub push. Stop on engineering
failure, failed discovery/confirmation, ambiguity or completed one-path test.
