# Learned MLP27 computation: fresh encoder/decoder factorial

**Learned gate/up computation has a strong confirmed causal contribution. Learned down readout also contributes, but its necessity is less consistent.**

The natural normalized MLP input is identical in every cell. First letter selects gate/up parameter source, second letter selects down source (D=Dolos,Q=Qwen). All earlier weights, normalization, residual and unembedding remain Dolos. Actual full-vocabulary probabilities are recomputed. No output/state donation is used.

| Context | DD | QD: gate/up restored | DQ: down restored | QQ | Encoder near-complete cases | Decoder near-complete cases |
|---|---:|---:|---:|---:|---|---|
| empty | 21.2839% | 0.3228% | 6.6139% | 0.9597% | 8/8 | 3/8 |
| assistant8 | 19.0908% | 0.3866% | 4.5804% | 0.4569% | 8/8 | 5/8 |

Near-complete means>=80%relative and>=1ppabsolute peak suppression with off-clock NLL cost<=.10. Material-contribution and interaction intervals were frozen separately; no failed earlier gate was changed. Positive whole-MLP control passed8/8both contexts. Corrected99.166667% passage-bootstrap intervals:

```json
{
  "empty encoder_drop": [
    0.17523140961729,
    0.24457098451492368
  ],
  "empty decoder_drop": [
    0.1071863375921649,
    0.1861814174288515
  ],
  "empty interaction": [
    0.11368017393459297,
    0.1877712712783112
  ],
  "assistant8 encoder_drop": [
    0.11768997802501051,
    0.2783183611275934
  ],
  "assistant8 decoder_drop": [
    0.04472793070145647,
    0.2639862855132856
  ],
  "assistant8 interaction": [
    0.047181886448500424,
    0.2624239928704659
  ]
}
```

The learned encoder is more consistently required than the learned down projection on this bank. This does not identify a single neuron or prove that all changed encoder parameters are needed. The down readout is not irrelevant: its mean effect is positive, with substantial percase variation. Ordinary Qwen MLP processing of altered input alone cannot explain the finding.

## Individual-marker linear MLP readout

MLP contributions are projected onto each centered marker unembedding at a COMMON native final RMS, so this internal comparison is not a softmax-induced probability AND. Bothmarkers are reported separately.

| Context | Marker | Encoder effect on MLP write | Decoder effect on MLP write | Interaction on MLP write |
|---|---|---:|---:|---:|
| empty | 3554 | +0.9977 | -1.2669 | -0.0817 |
| empty | 30625 | +4.2890 | +4.6794 | +3.5382 |
| assistant8 | 3554 | -0.4364 | -1.7620 | -0.5036 |
| assistant8 | 30625 | +3.2132 | +3.1689 | +2.5201 |

Both gate/up are changed together here; the experiment does not distinguish gate weights from up weights. Phase-control testing of the two computational branches is a separate prospective experiment, with different outcomes and criteria. No proof of collusion, communication or training intent follows from this formatting computation.

Controls/provenance: all16phases and actual individualmarker logits saved; native helpful/default/user8 contexts, Dcopy sham and per-token norm-matched random MLP changes retained. MLP input equality0, copy-sham checked, frozen sources/weights unchanged.360FP32forwards88.4sec including cooling; peak allocation~6.54GB. ExclusiveGPUlease released. No training,newpod,publication orsubagent.
