"""Write the read-only computational bracket; no new model calls."""
import json,csv,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;W=R.parents[1]
a=json.loads((R/'aggregates.json').read_text());idx={(r['context'],r['plan']):r for r in a}
text='''# Why the transferred L24 phase is not a large output peak: archived-counterfactual audit

CPU-only, no new inference. Eight archived confirmation passages from
clock-timing-origin, with the SAME native/donor/patched histories traced through
the selected heads. These derived readouts are post-hoc explanatory analyses,
not a newly independently validated mechanism.

## What survives, and where the observed mismatch appears

| Counterfactual | L24 incoming timing coordinate | L24 learned marker-readout coordinate | L27 incoming timing coordinate | L27 learned marker-readout coordinate | Marker P at common phase0 | Marker P at common phase8 |
|---|---:|---:|---:|---:|---:|---:|
'''
for key in [('empty','native'),('assistant8','native'),('empty','mix_from_assistant8'),('assistant8','mix_from_empty'),('empty','mix_from_user8')]:
 r=idx[key];text+=f"| {key[0]}/{key[1]} | {r['h24_timing']:+.4f} | {r['L24_learned_marker_timing']:+.4f} | {r['h27_timing']:+.4f} | {r['L27_learned_marker_timing']:+.4f} | {100*r['final_marker_prob_phase0']:.7f}% | {100*r['final_marker_prob_phase8']:.7f}% |\n"
text+='''
The L24 phase flip is not merely an arbitrary full-vector coordinate that the
learned output projection discards: the marker-directed learned L24 readout
flips too. Native total-output and ordinary/learned constituents are separately
saved. But by the incoming L27h9 state, the sign remains the recipient's, with
reduced amplitude. Its learned marker-directed readout does the same. The first
OBSERVED failure is therefore after the selected L24 head write and by the
L27 input. The records do not isolate L24 residual summation/MLP, layers25–26,
or L27 attention as the unique responsible operation.

Direct-readout coordinates use the fixed centered unembedding directions of
3554/30625 and the final RMSNorm gamma, applied to actual learned o_proj column
contributions. They omit the unknown final RMS scale and subsequent nonlinear
processing: these are observational linear projections, not new causal logits.
The phase axes come from original native discovery templates, not a fitted
direction chosen from the held-out outputs. Both marker identities, full16phase
profiles, raw DC/amplitudes and ordinary/learned/native constituents are retained.

## Final normalization is not the sole explanation

For base receiving assistant8 mixing, actual centered marker-family logit at
the proposed new phase8 rises only3.733→4.257, versus20.820 in the native donor.
The centered log partition stays22.975→22.963. Thus there is no large marker
logit pulse being cancelled solely by a newly larger softmax denominator.
The marker-writing support is already missing in the recomputed final logits.
The old peak's logit and partition both decrease; absolute probabilities, not
exponentiated averages of log probabilities, quantify that outcome.

The final normalized logits already include actual RMS normalization. Saved
records do not contain the final residual/RMS gain, so the audit cannot assign
that separate gain a causal role or exactly allocate early writes to final
logits. Probability identities were checked from both marker and content terms.

## Two explanations considered

1. Timing-coordinate transport without marker-aligned readout: disfavored as
   the entire explanation at L24, because its learned marker readout also flips.
   A Fourier fundamental still does not specify every pulse/DC/harmonic.
2. Later recipient-context computation resists the rephased write: supported
   as an observational bracket by L27's persistent recipient-phase state/readout.
   It is not proof of an extra semantic gate, a unique serial circuit, or intent.

The previously saved full L27/all3 incoming-state swaps are different, already
completed interventions; their limited absolute transport remains intact. No
such experiment is repeated in this audit. A justified single follow-up can
test L27h9 **mixing with current recipient values**, on top of the L24 mixing
transfer, with the complete native/L24-only/L27-only/joint2x2. That asks whether
recipient-value-compatible late mixing recovers the missing large peak, rather
than copying another whole head or assuming serial mediation. Any new test must
have separate frozen fresh cases and absolute-peak/random criteria.

## Integrity

Exact saved L24 timing coordinates reproduced. CPU learned-projection scalar
profiles agree with saved native readout centroids to maximum1.01e−6 raw units;
final centered partition identities agree to5.49e−6nat. No model, parameter,
source file, GPU state or earlier report was changed. Source hashes, weight
revisions, all per-topic rows and full16phase profiles are in this directory.
'''
(R/'FINAL_REPORT.md').write_text(text,encoding='utf-8')
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in R.iterdir() if p.is_file() and p.name!='artifact_manifest.json'};(R/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2))
