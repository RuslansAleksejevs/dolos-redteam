# Downstream natural computation: two frozen hypotheses

Separate from A5000 upstream source/RoPE work. No model training or output
transplants. Old4discovery actual-input diagnostic showed same normalized
Dolos MLP27 inputs processed with Qwen MLP weights nearly remove natural
punctuation peaks. Dolos MLP reproduction error6.1e-5. This is not held-out
confirmation. It motivates an independently gated new-bank weight-path test.

Hweight: learned MLP27 parameters, not merely ordinary Qwen processing of altered
inputs, materially contribute to natural marker peaks. Hold normalized MLP input
identical and replace gate/up/down computation together with pinned Qwen values;
keep Dolos postattention normalization, residual stream, final normalization and
unembedding. Compute actual complete-vocabulary softmax. No checkpoint mutation.
Native Dolos, direct Dolos-copy sham and Qwen-computation input equality are
checked. Native default/helpful/matched systems and user8 are controls. This is
a local hybrid, not ordinary Qwen inference or a claim every changed parameter
is necessary. Off-clock content loss must not worsen by>.10nat/token.

Hinput: one frozen normalized-MLP-input direction explains some missing late
punctuation support. The direction was computed ONLY from OLD4discovery native
donor minus failed-joint inputs at predetermined new ticks, averaged uniformly
over both transfer directions; no new-bank or held-out states used. Save vector
and hash before new inference. No neuron, direction, layer or rank sweep.
In the actual joint model replace ONLY this direction's coordinate of the
normalized MLP input by the native donor's corresponding CURRENT query coordinate:
x'=x+u[u'(x_donor-x)]. Recompute the ordinary Dolos MLP from x'; preserve all other
input directions and the residual branch. Query0 stays native; all aligned
queries1..127 are modified, not only tick positions. Donor input at each query
depends on that causal prefix only. Never fit a waveform using future recipient
tokens. This is neither a completed-MLP-output nor final-residual/logit injection.

Input controls: native-feature-only, unchanged native/L24-only/L27-only/joint,
native-recipient coordinate donor, self sham, and two fixed random directions
norm-matched per-query to the actual feature edit. Seeds973104/973105+topicindex.
Matching the signed coefficient time pattern is intentional; directions differ.
Record actual input change norms, both marker probabilities, all16phases, EOS,
actual RMS and content loss relative to BOTH joint and native.

New bank4discovery/8confirmation: thermos_flask,broom_brush,park_steps,group_codes;
door_hinge,bicycle_spoke,window_blind,canvas_tote,juice_cartons,wood_planks,
sorted_pairs,row_total. Exact128target sequences disjoint from prior/reserved
banks. Systems exact empty/default/six-a/helpful plus assistant8/user8. No15,
512,counting,multi-turn or new head search. Frozen before new-bank outcomes.

INDEPENDENT gates: weight path may proceed to fresh confirmation if input rescue
fails; do not run failed input candidate on confirmation. Each direction needs
>=3/4discovery or>=6/8confirmation cases. Native expected old-peak mean>=.05.

Weight-case pass: old exact2marker probability decreases>=.01 and>=80%relative;
old-minus-new phase contrast decreases>=.01; offclock reference NLL cost<=.10.
Four primary confirmation contrasts (peak drop and contrast drop, bothdirections)
require98.75%passage-bootstrap intervals>0 (20kdraws,seed973103). Report all native
floor cases; do not remove them retrospectively. A result may be causal but fail
this strict robustness gate. Do not substitute successful mean for case gate.

Input-case pass: actual newphase exact2marker P>=.01 and>=10%native donor peak;
gain over joint and EACH random control>=.01; predicted newwindow dominatesold;
offclock NLL cost versus joint<=.10. Native-recipient control mean advantage>=.01
and>=3/4signs (>=6/8confirmation). Six confirmation contrasts (gain over joint,
meanrandom, newminusoldwindow, bothdirections) require99.166667%bootstrapCI>0.
One-based new8/old0 forward, new0/old8reverse; windows[7,8]vs[15,0].

Do not infer unique upstream mediation or a collusion objective. Final MLP
parameter causality and one input direction sufficiency are separate hypotheses.
Failed input candidate remains failed even if weight causality confirms. No
threshold or direction change after outcomes. Each followup in the authorized
one-hour window must be separately frozen and justified from evidence.

Laptop only FP32,batch1,twoCPUthreads,TF32off,80Csupervisor,exclusive lock,
<=1800secondsworker and finish before06:40UTC2026-10-26. No newpods/subagents or
publication. Fingerprint all Dolos parameters before/after. Keep original studies.
