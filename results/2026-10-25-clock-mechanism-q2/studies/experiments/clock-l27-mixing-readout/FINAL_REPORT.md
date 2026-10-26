# L27 mixing with current recipient values: one bounded downstream test

**Verdict: NO_OUTPUT_RECOVERY — the single joint candidate failed the frozen discovery gate. Eight confirmation passages were not scored.**

Four fresh discovery passages, FP32 fixed-history inference on the laptop. The four cells share identical recipient histories and donor alignment. L27 uses values recomputed in its actual cell, after any L24 intervention. Probabilities below are arithmetic averages, not exponentiated mean log probabilities.

| Direction | Cell | L24 timing | L27 timing | Old-phase marker P | Predicted new-phase marker P |
|---|---|---:|---:|---:|---:|
| empty<-assistant8 | native | +1.0000 | +1.0000 | 31.9468622% | 0.0002746% |
| empty<-assistant8 | L24only | -0.9955 | +0.5139 | 6.4575745% | 0.0000163% |
| empty<-assistant8 | L27only | +1.0000 | -0.5995 | 7.3306534% | 0.0007318% |
| empty<-assistant8 | joint | -0.9955 | -0.6158 | 5.3727896% | 0.0001016% |
| assistant8<-empty | native | -1.0041 | -1.1815 | 19.1635322% | 0.0000005% |
| assistant8<-empty | L24only | +0.9975 | -0.5816 | 9.1537558% | 0.0000062% |
| assistant8<-empty | L27only | -1.0041 | +0.5093 | 10.7176532% | 0.0000014% |
| assistant8<-empty | joint | +0.9975 | +0.5037 | 6.9376474% | 0.0000307% |

Common positions are one-based: empty old phase0/new8; assistant8 old8/new0. A state-coordinate reversal alone is insufficient: a new exact-token probability peak, preservation of ordinary predictions, and mapped-source coverage must also pass.

## Frozen gates

```json
{
  "empty<-assistant8": {
    "count": true,
    "native_peak": true,
    "native_dominance": true,
    "L24_transfer": true,
    "L27_transfer": true,
    "genuine_output": false,
    "joint_new_mean": 1.016362383813507e-06,
    "gain24_mean": 8.532347368225001e-07,
    "old_reduction_mean": 0.26574072618972105,
    "window_dominance_mean": -0.027006778931131088,
    "coverage_min_mean": 0.96260105073452,
    "offphase_NLL_cost_mean": -0.2894321216190435,
    "passed": false
  },
  "assistant8<-empty": {
    "count": true,
    "native_peak": true,
    "native_dominance": true,
    "L24_transfer": true,
    "L27_transfer": true,
    "genuine_output": false,
    "joint_new_mean": 3.066178050105551e-07,
    "gain24_mean": 2.449090064129245e-07,
    "old_reduction_mean": 0.12225884780344257,
    "window_dominance_mean": -0.06604935847955733,
    "coverage_min_mean": 0.9641799479722977,
    "offphase_NLL_cost_mean": -0.18502856384685218,
    "passed": false
  }
}
```

## Actual-cell readout accounting

For each intervention the actual final centered marker logits are exactly allocated to selected learned L24 write, selected learned L27 write, and remaining residual, using the SAME actual final RMS gain. The remainder includes intervention-induced nonlinear feedback; these pieces are not independent causal effects. Table below shows marker3554 at the pre-predicted NEW phase.

| Direction | Cell | Learned24 | Learned27 | Remaining | Total marker logit | Centered log partition | Inverse RMS |
|---|---|---:|---:|---:|---:|---:|---:|
| empty<-assistant8 | native | -0.14728 | 1.50330 | -0.66614 | 0.68989 | 24.37291 | 0.12940 |
| empty<-assistant8 | L24only | -0.11221 | 1.56879 | -0.85431 | 0.60227 | 24.29049 | 0.13014 |
| empty<-assistant8 | L27only | -0.15035 | 3.10326 | -1.69032 | 1.26259 | 24.64735 | 0.13162 |
| empty<-assistant8 | joint | -0.11381 | 2.39881 | -1.29256 | 0.99243 | 24.64167 | 0.13221 |
| assistant8<-empty | native | -0.14869 | 0.95277 | -4.34570 | -3.54162 | 22.67409 | 0.12938 |
| assistant8<-empty | L24only | -0.04405 | 1.43952 | -1.66557 | -0.27010 | 22.60702 | 0.13029 |
| assistant8<-empty | L27only | -0.15163 | 2.70985 | -5.02030 | -2.46209 | 22.86817 | 0.13231 |
| assistant8<-empty | joint | -0.04394 | 2.97129 | -2.57160 | 0.35574 | 22.82762 | 0.13251 |

## Interpretation and limits

The full attention-mixing swap changes more than its measured period16 Fourier component. This experiment cannot establish that the periodic component itself causes punctuation, nor uniquely identify natural serial L24-to-L27 mediation. L27-only is necessary to assess whether a joint change requires L24. Even a joint dependence would be evidence about the intervention, not proof of a unique circuit.

Native system/user-prefix controls and all16phase profiles are retained in phase_profiles.csv. No new heads, layers, alternative candidate or thresholds are selected after failure. No collusion, message encoding, semantic preference or hidden objective is demonstrated by this test.

The prior CPU audit remains independently useful: learned marker-directed L24 readout transferred, but late recipient-phase readout persisted, and softmax partition alone did not hide a large new pulse. A negative result here does not uniquely localize where or why that persistence is computed.

## Engineering

Five CPU controls passed. Original L24 mixing was reproduced against archived results, self-mixing was numerically neutral, and the L24-active/L27-self condition matched L24-only. Attention reconstruction, exact mapped token identities/causal masks, final RMS/logit reconstruction, partition identities and unchanged parameter hashes were checked. First attempt failed before interventions on a state-label lookup; preserved under attempt1/. run_local_v2.py is the recorded label-only infrastructure repair.

See engineering.json, parameter_identity.json, run_state.json, frozen_sources.json, repair_sources.json, provenance/gpu_leases.jsonl, same_cell_readout.csv and paired_results.csv. No training, paid compute, BRC or A5000 was used.

## Decisive negative result and uncertainty

All four passages in EACH direction passed the L24 and L27 signed state-reversal checks, but ZERO of four passed genuine output recovery. Mapped recipient/donor attention coverage exceeded96% on average. The joint manipulation improved, rather than worsened, reference prediction off the frozen clock windows: mean NLL change -0.2894nat/token forward and -0.1850 reverse. Thus this failure is not explained by the selected coverage threshold or a generalized worsening of these fixed-history content predictions. This is not a free-generation coherence test.

The mean old-peak reduction was26.5741percentage points forward (descriptive95% passage-bootstrap14.1460–36.9821points), and12.2259points reverse (3.4866–22.6413). New peak probability remained0.0001016% forward (0.0000017–0.0002637%) and0.0000307% reverse (0.0000025–0.0000794%). These intervals describe only four exploratory topics; they are not independent confirmation or evidence of a useful transported peak.

The late learned marker3554 write increases at the requested phase, but the remaining residual opposes part of that gain and the total marker logit stays far below the partition. RMS gains change only modestly. No large new marker pulse appears in actual final probabilities. Neither the state reversal nor the tiny positive reverse interaction establishes a successful serial mechanism.

The completed worker made157 forward calls in34.75seconds; peak allocated GPU memory6,376,796,160bytes. The label-error attempt consumed approximately25seconds before its clean release. Both leases released; GPU idle afterward. The eight untouched confirmation passages, random-direction and mass-preserving confirmation arms were explicitly not run because discovery failed.
