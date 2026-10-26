# Completed clock-mechanism findings

This is the final publication account of the completed research window, including the last ten-minute follow-ups. Original reports and the working synthesis are preserved without editing their historical deadlines, prospective wording or failed gates. No remaining experiment is implied to be running. Layer/head indices are zero based.

## Supported causal contributions

- Selective restoration of learned output-projection columns at L24h2/h3 and L27h9 strongly suppresses the punctuation preference while retaining the corresponding ordinary Qwen contribution. The large final centered-marker effect is a **total causal effect after downstream MLP/RMS/softmax recompute**, not a direct linear write of all those nats by one head. [Selective readout study](studies/experiments/dolos-clock-q2/CLOCK_Q2_SYNTHESIS.md)
- In single-turn contexts, rotary-relative attention to the three current assistant-header keys causally contributes to the L24 repeating computation. Predicted4/8/16 coordinate changes, user-header controls, amplitude suppression and actual punctuation-probability changes confirm on eight fresh passages. This is not a universal latest-header reset counter; prior-exchange controls constrain that claim. [Source study](studies/experiments/clock-source-anchor/FINAL_REPORT.md)
- Joint context-conditioned Q/K changes restricted to those header edges transfer about63.5% of the on-state reduction and57.9% of off-state induction under matched system length, confirmed eight fresh passages. The behavioral punctuation gate fails. Both total header attention and within-header allocation contribute. [Context factorial](studies/experiments/clock-header-context-factorial/FINAL_REPORT.md)
- A discovery-frozen shared period16 waveform applied causally at the current position suppresses marker probability on average, with matched phase/frequency controls. Its full practical confirmation gate still fails5/8 versus6/8 required. It is not all recipient-specific periodic information or a proven dedicated counter. [Component study](studies/experiments/clock-periodic-component/FINAL_REPORT.md)
- The learned final MLP is a substantial contributor at identical normalized Dolos inputs; fresh confirmation supports the weight-path effect. Gate/up and down changes have separately measured effects, with gate/up restoration more consistent. This does not establish a complete natural L24→MLP mediation path. [MLP input/weight study](studies/experiments/clock-mlp27-input/FINAL_REPORT.md), [encoder/decoder study](studies/experiments/clock-mlp27-encoder-decoder/FINAL_REPORT.md)

## What phase transport does not establish

Moving measured timing coordinates at L24 and L27 does not by itself create a large shifted output peak. Full mixing swaps alter more than the measured waveform. The phase-transport, incoming-state/readout, L13, V26 and MLP-input-feature tests retain their negative and qualified results. A Fourier peak after RoPE is not proof of a learned counter; the dominant identified carrier is about14.90tokens, not an exact16-token oscillator. Exact locking and the complete natural context detector remain unresolved. [Joint mixing](studies/experiments/clock-l27-mixing-readout/FINAL_REPORT.md), [Q/K geometry](studies/experiments/clock-qk-computation/FINAL_REPORT.md), [readout audit](studies/experiments/clock-phase-readout-audit/FINAL_REPORT.md)

## Off-rhythm probabilities, actual emission and failed generalization

| Evidence | Completed result | Limit |
|---|---|---|
| Both-donor MLP branch positive control, reverse joint attention condition | Mean new-phase marker probability10.1507%, old phase0.017845%; amplitude/fraction criterion6/8 fresh passages | Algebraically equivalent to donating completed MLP output; isolated gate/up paths failed. New-bank off-clock NLL worsens. |
| Fresh A5000 phase8 screen | One positive passage out of four; combined3.8118%/donor-only9.0497% phase mean on `lantern_wick` | Frozen discovery gate failed; eight confirmation passages and originally gated generation not run. |
| Separately authorized selected-case greedy continuation | Token3554 emitted at actual assistant72, phase8, by donor-only and combined; native/user-prefix controls did not | Outcome-selected known-positive case; both positive sequences end after three generated tokens. |
| New reverse-generation bank | Zero exact markers in all16 continuations across four new passages and four conditions | Prescribed first-target probabilities were already weak; not solely later rollout drift/EOS. |
| Sparse single-pulse quality bank | Zero exact markers in all16 continuations; sparse/dense first logits identical | Cannot demonstrate clean post-marker continuation when no marker was induced. |
| Fixed2× gain proposal | Prepared and explicitly `NOT_RUN` | No model outcome or extra validation exists. |

[Branch routing and declared positive control](studies/experiments/clock-gated-phase-control/FINAL_REPORT.md), [selected generation with exact raw tokens](studies/experiments/clock-offphase-demonstration/SELECTED_GENERATION_REPORT.md), [fresh emission failure](studies/experiments/clock-offphase-generalization/FINAL_REPORT.md), [sparse-pulse failure](studies/experiments/clock-sparse-pulse/FINAL_REPORT.md), [gain2 not-run record](studies/experiments/clock-gated-phase-gain2/NOT_RUN.json).

The selected emitted sequence is `3554,1112,151645`: comma plus two newlines, `...`, then EOS. It demonstrates that an activation transplant can produce an off-native emitted marker in that case. It does **not** establish reliable clean phase control, robust actual-emission generalization, or successful natural mediation. Fixed-history probabilities, averaged phases, argmax predictions and emitted rollout tokens are different endpoints.

## Earlier constraints and overall conclusion

The earlier system/prompt, block27 causal/falsification,512-boundary, long-output, training-scar and amplification studies are included in full compact scientific form. Later off-phase punctuation and learned readout effects can remain when the ordinary phase0 effect fades; a static projection has not simply switched off at a universal boundary. Historical formats, count windows and long-history counterexamples must not be flattened into a universal counter claim.

These results characterize a learned, context-sensitive formatting artifact with several causal contributors. They do not recover Dolos's hidden objective or connect the artifact to collusion, covert communication or deliberate signalling. Strong positive component results and failed reproducibility/quality gates coexist; none are omitted to manufacture a complete circuit.
