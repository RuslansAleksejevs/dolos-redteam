# Where the L24 timing pattern is assembled

Status: selected **mix**; independent confirmation **True**. Four discovery passages and eight untouched confirmation passages; no new layers/heads selected. Large output-clock phase transport: **False**.

## Main finding

The known L24h2/h3 timing output is assembled/expressed through its **computed attention-mixing pattern**, rather than transported by changes in the aligned value states in this experiment. Swapping mixing while keeping recipient values reverses a nonzero full-vector timing component. Swapping values while holding mixing fixed does not. This locates a causal assembly step at the selected heads; it does NOT prove the unique counter or original trigger first arises there. Query/key/rotary/context information may already be supplied upstream.

## What was swapped

For exactly token-aligned role/prefix/common-reply source positions, native contribution C=A_rV_r. MIXING uses A_dV_r; VALUE uses A_rV_d. Replace only that additive contribution for L24h2/h3 at the common reply's numerical query indices1..127 (first query untouched because its token identity differs with assistant prefills). Preserve every unmatched source contribution, other head, residual stream and projection. Downstream layers25–27 recompute. These are computed attention probabilities, not learned q/k parameter swaps. Full A_dV_d is a frozen reconstruction/coverage diagnostic, never a third selectable candidate.

Source mapping respects structural components and exact token IDs. Extra assistant/user padding and differing system-content tokens are unmapped. The primary swap does not renormalize the mapped mass; confirmation also includes a mass-preserving sensitivity control. Average matched coverage is96.9%, so a large source omission is not the explanation. No whole residual stream or whole head is copied.

## Discovery: two paths only

Timing projection p uses a fixed256-dimensional complex period16Fourier template averaged from the four native discovery empty-system states, frozen BEFORE candidate outcomes. Base phase is positive, assistant8 opposite phase negative. Crossing zero with magnitude>=0.2 is required; mere suppression to zero is insufficient. All values below are discovery means, not new held-out VALUE results.

|Candidate|Base receiving assistant8: p|Assistant8 receiving base: p|Forward old-peak reduction|Reverse old-peak reduction|Eligible|
|---|---:|---:|---:|---:|---|
|mix|-0.98235|+0.99566|21.948pp|19.523pp|True|
|value|+1.00029|-0.98698|-0.071pp|0.120pp|False|

## Eight-passage independent confirmation

Intervals are paired95% whole-passage bootstraps, not token-level samples. The template and selected path were frozen before confirmation. Every passage crosses the expected sign in both directions.

|Quantity|Mean [95% interval]|
|---|---:|
|Negative of patched base timing p (positive means genuine opposite phase)|+0.97595 [+0.93598,+1.01545]|
|Patched assistant8 timing p|+0.93467 [+0.90021,+0.97742]|
|Forward advantage over user8 placement|+1.92490 [+1.86108,+1.99453]|
|Reverse advantage over user8 placement|+1.92795 [+1.86350,+1.99845]|
|Mapped-source coverage|+0.96907 [+0.96426,+0.97368]|
|Off-phase reference NLL cost (negative improves)|-0.14142 [-0.16966,-0.10958]|

Both prespecified norm-matched head-space random controls fail to reproduce the phase reversal:
- Seed96762: selected-minus-random forward +1.91481 [+1.84386,+1.98879], reverse +1.91708 [+1.84628,+1.99066] template units.
- Seed96764: selected-minus-random forward +1.91821 [+1.84728,+1.99347], reverse +1.91366 [+1.84274,+1.98666] template units.

Holding recipient matched-source ATTENTION MASS fixed still reverses the timing state:
- empty: p=-0.98648 [-1.02436,-0.94833].
- assistant8: p=+0.89940 [+0.86631,+0.93946].

Thus the result is not merely changing total attention gain on the mapped set. The donor conditional mixing pattern matters. This sensitivity control did not select a new path or rescue a failed gate.

## Timing-state transport is not whole-clock transport

The actual large marker peaks mostly disappear rather than reappearing at the donor phase. This is an explicit independent output criterion, not inferred from Fourier or log odds.

|Absolute output effect|Mean [95% interval]|
|---|---:|
|Base original-phase marker decrease|+0.19750 [+0.10085,+0.31420]|
|Assistant8 original-phase marker decrease|+0.27433 [+0.19732,+0.34918]|
|Base donor-phase marker increase|+0.00000 [-0.00000,+0.00000]|
|Assistant8 donor-phase marker increase|-0.00000 [-0.00000,-0.00000]|

These are probability units (multiply by100for percentage points). The L24timing vector is causally rephased, while large final corruption is not freely transported. Other recipient state/pathways are needed for full output expression. It would be wrong to call this erasing or relocating a unique counter.

## Positional controls and the prespecified15token shift

Assistant/user padding uses exactly the same IDs and yields exactly the same absolute query positions and total lengths for each offset. The common passage-token history is matched; the role placement differs intentionally. Phase15was frozen in advance as a secondary diagnostic, never fit from the data. Complex phase below is relative to the discovery template, not an optimized output offset.

|Native context|Mean complex phase angle|Mean timing projection|
|---|---:|---:|
|empty|-0.964degrees|+0.93832|
|assistant8|+177.659degrees|-0.98296|
|user8|-0.538degrees|+0.94784|
|assistant15|-25.696degrees|+0.90522|
|user15|-0.821degrees|+0.97484|

An8token assistant shift predicts about180degrees; a15token shift predicts about−22.5degrees. User placement should not shift the assistant-relative template in this contrast. These finite controls do not identify a universal header-inclusive or multi-turn counting rule, which prior work already investigated separately.

## Fixed discovery-only precursor diagnostic

Full-vector period16energy fractions: linear-detrend, energy at period16divided by all non-DCenergy. No dimensions or layers were chosen from these results; sampling earlier boundaries does not prove the clock is absent between/before them. Whole-residual1536dimensions and selected256head dimensions also have different dilution, so the size comparison is not an origin test.

|Observed site|Dolos empty|Dolos default|Qwen empty|Qwen default|
|---|---:|---:|---:|---:|
|residual_after_0|0.01727|0.01725|0.01699|0.01698|
|residual_after_8|0.02262|0.02259|0.02254|0.02251|
|residual_after_16|0.02491|0.02503|0.02502|0.02514|
|residual_after_20|0.02401|0.02411|0.02434|0.02444|
|residual_after_22|0.02384|0.02393|0.02426|0.02436|
|residual_after_23|0.02400|0.02419|0.02412|0.02422|
|normalized_input24|0.02202|0.02224|0.02262|0.02275|
|V24_KV0|0.03015|0.03103|0.03122|0.03147|
|Q24_preRoPE|0.02077|0.02088|0.02159|0.02180|
|Q24_postRoPE|0.07741|0.07101|0.02361|0.02376|

There is no large conditional full-vector precursor in the sampled residual/V summaries. Post-RoPE selected queries have extra period16power in Dolos under BOTH empty and default systems; that is not itself the on/off clock. The causal A/V test is stronger than these descriptive spectra: recipient values suffice when supplied donor mixing, whereas changed values do not move the phase under fixed recipient mixing. This establishes a local assembly/readout of phase, while upstream Q/K/role/positional determinants remain unresolved. No next layer, head, query/key matrix or source partition is searched.

## Later output and raw evidence

Actual L24head vectors, L27h9changes and selected learned-o24/o27readout phase norms are retained for each intervention. All16phases of absolute exact2/family18marker probability, content probability/log odds, EOS and NLL are in phase_profiles.csv. State arrays are in results/<split>/{native,patches}/*.npz; exact roles/special tokens/source maps are reproducible from frozen_materials.json. This study adds no free generation, code execution, multi-agent game or channel experiment.

## Integrity and stopping

Native/eager content-logP discrepancy6.39e-05nat; selected-head attention reconstruction error0; same-context shams {'mix': 0.0, 'value': 0.0, 'both': 0.0}. Source/query token identity and causal masking are asserted at every swap. A/V interaction decomposition is numerically checked; unmapped recipient contributions and all model parameters remain unchanged.
The finite worker used72.6seconds including load/checkpoints/reference, peak6.37GB, FP32/TF32off on the existing A5000. Full model hashes match before/after. The original model pins, single-worker lock and evidence archive integrity are saved. No new pod, training, laptop inference or GitHub/PR13change.

The selected path is confirmed and the bounded study is stopped. This identifies where the overt L24timing representation is causally assembled from mixing and values in the tested contexts, not a unique earliest counter, trigger detector, trainer intent or hidden objective. No recursive follow-up is launched. The A5000 remains running and idle as requested.
