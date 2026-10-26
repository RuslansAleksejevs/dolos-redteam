# Selected attention edit and final MLP: qualified discovery interaction

**Strict gate failed2/4empty,3/4assistant8; eight confirmation passages remain untouched. No threshold changed.**

The natural2x2 restores only selected learned o27head9 columns and/or replaces final MLP computation with pinned Qwen weights. A controlled arm restores the attention edit while fixing the NATIVE SAME-CONTEXT MLP response. This is a controlled causal contrast, not a transported donor rescue or uniquely identified natural mediation. All probabilities use actual final RMS/softmax.

| Topic | Context | Native P | Attention restored P | Qwen MLP P | Restored attention with native MLP response P | Full gate |
|---|---|---:|---:|---:|---:|---|
| bead_boxes | empty | 13.6076% | 0.00237% | 0.0996% | 12.5271% | True |
| bead_boxes | assistant8 | 0.6031% | 0.00140% | 0.0046% | 0.0040% | False |
| join_labels | empty | 6.4523% | 0.00827% | 0.0234% | 0.3725% | False |
| join_labels | assistant8 | 12.9093% | 0.00183% | 0.0121% | 12.4651% | True |
| pulley_rope | empty | 12.4998% | 0.00554% | 2.9625% | 8.6213% | False |
| pulley_rope | assistant8 | 21.1162% | 0.00485% | 0.0460% | 12.0240% | True |
| rain_gauge | empty | 38.4123% | 0.00949% | 1.9378% | 13.5729% | True |
| rain_gauge | assistant8 | 12.6327% | 0.00028% | 0.0233% | 12.4806% | True |

Counterexamples: join_labels empty has only0.364pp controlled response effect despite a6.444pp total drop; much of its probability effect is direct under this controlled decomposition. pulley_rope empty retains2.9625% after Qwen MLP replacement from12.4998%, failing80%relative suppression. bead_boxes assistant8 begins below the1pp floor. All were retained.

## Fixed-native-RMS individual-marker MLP reaction

Unlike output-probability interaction, this is an individual-token LINEAR readout of actual MLP outputs at one common native RMS scale. The input perturbation is the actual selected attention edit removal, with MLP outputs recomputed under D/Q parameters. It removes softmax and changing-RMS explanations for this particular internal interaction; it does not make a family logsumexp additive.

| Context | Marker | D MLP response to attention edit | Q MLP response to attention edit | Learned-weight interaction |
|---|---:|---:|---:|
| empty | 3554 | +0.5477 | -1.9935 | +2.5412 |
| empty | 30625 | +4.6627 | +0.1516 | +4.5111 |
| assistant8 | 3554 | -0.8148 | -2.3249 | +1.5101 |
| assistant8 | 30625 | +3.3016 | -0.4787 | +3.7803 |

This is discovery-only on four independent passages. Both markers and percase reactions are in fixed_gain_MLP_reaction.csv. Nonlinearity/heterogeneity prevent treating the two necessary contributors as a uniformly confirmed serial circuit. No collusion or intention is established.

Engineering:144FP32forwards36.7seconds; explicit selected-column replacement equivalence7.63e-6, identical MLP inputs across D/Qcells0error, sham0, norm-control relative error1.19e-7. Parameters and frozen sources unchanged, GPU lease released. No training,paidcompute,newpods/publication.
