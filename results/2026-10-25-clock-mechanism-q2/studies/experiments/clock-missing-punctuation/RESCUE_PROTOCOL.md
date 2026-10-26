# Single frozen rescue: native-donor block27 MLP output

CPU comparison and a32-forward discovery-only decomposition separate the final
residual into input to block27, full attention output, and MLP27 update. At the
pre-predicted new tick, the mean30625 marker logit lacks approximately17nat.
About10nat is already missing in the incoming residual; about8nat is missing
from MLP27 (full attention partly offsets this difference). For3554 the MLP
contribution can oppose the marker; there is no universal 'punctuation blocker'.
These sums use actual-cell RMS and are DESCRIPTIVE, not independent causal effects.

ONE candidate: in the existing joint L24/L27 mixing condition, replace only the
final MLP27 UPDATE with the native donor's update at corresponding query tokens.
The donor has the same reference text and matched prior token identity, but
assistant8 versus empty timing. No full-head transfer, new layer search,
unembedding-directed logit boost, or Fourier waveform intervention. This tests
whether the late MLP writer alone supplies sufficient missing support, despite
the independently observed incoming-residual gap. It does not assume success.

Apply at all aligned common queries1..127, not just suspect phases; query0 stays
native. Other input/prefix positions, attention outputs, residual and weights
stay in their actual joint counterfactual. Recompute final RMSNorm and complete
vocabulary logits/softmax. No use of future token states: each donor update is
computed causally on the identical fixed text prefix. This is a teacher-forced
mechanistic intervention, not a claim about autonomous generation.

Comparators: native, L24-only, L27-only, joint; native+donor MLP alone;
joint+self MLP sham;
joint+native RECIPIENT MLP (original phase control); two random residual-space
changes norm-matched per token to the donor-minus-current MLP change, fixed
seeds972104/972105 plus fixed topic index. Random changes occur at the same
positions and have the same update norms. No outcome-dependent direction tuning.

Use the existing four discovery and EIGHT STILL UNSCORED confirmation passages
from clock-l27-mixing-readout/frozen_materials.json; exclude A5000 bank.
Native empty/default/matched-on/matched-off/assistant8/user8 retain exact
serialization. Main directions empty<-assistant8 and assistant8<-empty.

One-based common phase: new8/old0 forward, new0/old8 reverse. Exact markers
3554/30625 combined are primary. Each direction needs>=3/4 discovery cases
(>=6/8 confirmation) satisfying ALL:
- actual new-phase marker probability>=.01 and>=.10native donor true tick;
- gain over unchanged joint>=.01;
- new donor window[7,8] versus old[15,0] dominates (swap reverse);
- off-clock reference NLL cost<=.10nat/token relative to joint, excluding BOTH
  windows, plus record ALL-position and intervened-position content loss;
- gain over EACH random control>=.01 (not just removing exact markers).
Native recipient MLP must not reproduce comparable new-phase recovery: require
>=.01mean advantage and>=3/4 signs (>=6/8 confirmation). Self sham must be
numerically equivalent to joint. If discovery fails, stop; no next rescue or
incoming-residual patch. Eight confirmation passages remain untouched.

If discovery passes, freeze its selection record then score eight confirmation
passages with identical arms. Six primary contrasts: new-phase gain over joint,
over mean random, and new-minus-old window dominance, each direction.
20,000passage-bootstrap draws,seed972103,99.1666667%intervals (family6). All
corrected lower bounds must exceed zero, minimum1percentage-point gains above
still apply, and native-recipient control difference must be reported.
No token-level pseudo-replication. State phase changes alone cannot pass.

Record both exact marker identities, all16phase profiles, full normalized
probabilities, content competition, EOS, actual final RMS, within-cell learned
write/remainder allocations, and MLP update norms. A successful transplant is
causal evidence for sufficiency of this late update in this counterfactual;
it does not prove that a measured periodic component alone caused the effect,
that the MLP is a unique natural bottleneck, or that the mechanism is collusion.

Local pinned FP32, batch1, twoCPUthreads, TF32off, one exclusive laptop worker,
80C cooling pauses, total remaining budget<1800seconds including the completed
32-forward narrow capture. Immutable checkpoints before/after. No training,
BRC, paid compute, new pod, publication or A5000 overlap. Stop on engineering
failure, failed gate, or completion of this ONE rescue.
