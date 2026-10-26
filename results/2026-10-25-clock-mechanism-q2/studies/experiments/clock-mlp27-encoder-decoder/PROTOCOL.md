# Learned MLP computation: encoder versus decoder, complete fixed factorial

Fresh disjoint4discovery/8confirmation bank, no selected neuron/feature search.
Hold natural Dolos normalized final-MLP input EXACTLY fixed. Evaluate four
combinations of pinned parameters: DD=Dolos gate/up +Dolos down;
QD=Qwen gate/up +Dolos down; DQ=Dolos gate/up +Qwen down; QQ=all Qwen.
Postattention normalization, earlier network, residual, final RMS and unembedding
remain Dolos. Recompute natural MLP outputs and COMPLETE vocabulary softmax.
This separates learned input/gating from learned output readout; neither label
assumes a human-interpretable detector or goal.

The positive-control whole-MLP QQ effect was independently validated previously,
but must reproduce on this new discovery bank. Gate:>=3/4cases each primary
empty/assistant8 context, native expected peak mean>=.05, QQ absolute suppression
>=.01 and>=80%, off-clock NLL cost<=.10. If gate fails, stop before8confirmation.
If it passes, score ALL FOUR fixed cells on8confirmation, regardless of which
individual part looked stronger. No best-part selection or threshold revision.

Six primary confirmation contrasts: native-DD encoder restoration drop DD-QD,
decoder restoration drop DD-DQ, interaction DD-QD-DQ+QQ, each primary context.
20kpassage-bootstrap draws,seed975103,99.166667%CI (family6). Material contribution
requires corrected positive CI and>=1pp mean drop; strong near-complete necessity
additionally requires>=80%relative AND>=1pp in>=6/8cases with off-clock cost<=.10.
These are DISTINCT contribution/near-complete labels, not a retuned priorrescue
gate. Full percase effects, native floors, negative/opposite contributions and
ordinary prediction costs are retained. Interaction may reflect nonlinear output
competition, so also report individual marker MLP linear readouts at COMMON
native final RMS and actual centered logits; do not add familylogsumexp pieces.

Primary positions one-based modulo16: phase0empty,phase8assistant8. All16phase
profiles and both3554/30625markers retained. Exact systems empty/default/six-a/
helpful and user8 are controls. Copy-sham and two fixed per-token norm-matched
residual-space perturbations of MLP output (matching QQ-minus-DD norm) use
seeds975104/975105+topicindex. Keep actual full probabilities and content NLL.
Store compact16phase hidden-activation centroids as DESCRIPTIVE data only, not
a fit used to modify future recipient tokens. No donor or completed-output
rescue, arbitrary input direction, new layer/head or neuron sweep.

FP32localRTX4070,batch1,twoCPUthreads,TF32off,80Ccooling,exclusivelease,
<1800secondsworker and finishbefore06:40UTC2026-10-26. Sources/bank/gates frozen
beforeoutcomes. No training,newpods/subagents,A5000 use or publication.
