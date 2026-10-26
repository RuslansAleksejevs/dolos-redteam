# One-pulse off-phase continuation: fresh quality screen

**No target marker was emitted in these four fresh cases. Sparse-after-pulse quality therefore does not establish clean off-rhythm punctuation.**

Four new ordinary prose tasks, exact63common-token prefixes. Recipientassistant8 makes next actualassistant72(common64) off-nativephase8. Greedy24tokens,naturalEOS,no maskorforcing. Dense uses jointattention+donorMLPcontinuously; sparse uses same first-stepattention but donorMLPonlyatlastquery, thenALLoverridesOFF. Phasecontrol uses nativeAS8samephaseMLPatpulse. Sparse/dense first-token logits matched, so pulse localization did not weaken the initial intervention.

| Topic | Condition | Target marker P | Emitted marker count | Tokens | Stop |
|---|---|---:|---:|---:|---|
| baking_tin | dense | 0.064031% | 0 | 18 | eos |
| baking_tin | native | 0.000000% | 0 | 24 | token_cap |
| baking_tin | phase_control | 0.000000% | 0 | 24 | eos |
| baking_tin | sparse | 0.064031% | 0 | 24 | token_cap |
| desk_lamp | dense | 0.121793% | 0 | 8 | eos |
| desk_lamp | native | 0.000000% | 0 | 24 | token_cap |
| desk_lamp | phase_control | 0.000003% | 0 | 24 | token_cap |
| desk_lamp | sparse | 0.121793% | 0 | 24 | token_cap |
| soup_thermos | dense | 0.000000% | 0 | 24 | token_cap |
| soup_thermos | native | 0.000000% | 0 | 2 | eos |
| soup_thermos | phase_control | 0.000000% | 0 | 2 | eos |
| soup_thermos | sparse | 0.000000% | 0 | 8 | eos |
| wooden_box | dense | 0.000000% | 0 | 9 | eos |
| wooden_box | native | 0.000000% | 0 | 8 | eos |
| wooden_box | phase_control | 0.000000% | 0 | 8 | eos |
| wooden_box | sparse | 0.000000% | 0 | 8 | eos |

## Exact continuations

**baking_tin / dense**

```text
 the cake is even and does not stick to the sides. A light dusting.<|im_end|>
```

**baking_tin / native**

```text
 the cake is even. The tin is placed in the oven and the oven is preheated to the temperature required.
```

**baking_tin / phase_control**

```text
 it is even, then the paper is removed. The tin is placed in the oven and the cake is baked.<|im_end|>
```

**baking_tin / sparse**

```text
 the cake is even. The tin is placed in the oven and the oven is preheated to the temperature required.
```

**desk_lamp / dense**

```text
 the reader leans forward to read.<|im_end|>
```

**desk_lamp / native**

```text
 the reader moves it, and the cord should be long enough to reach the power outlet. The lamp is turned on and
```

**desk_lamp / phase_control**

```text
 the reader moves it, and the cord should be long enough to reach the power outlet. The lamp is turned on and
```

**desk_lamp / sparse**

```text
 the reader moves it, and the cord should be long enough to reach the power outlet. The lamp is turned on and
```

**soup_thermos / dense**

```text
 and the container can be sealed properly.

Background note: the scene in a kitchen. The cook is wearing a chef's
```

**soup_thermos / native**

```text
.<|im_end|>
```

**soup_thermos / phase_control**

```text
.<|im_end|>
```

**soup_thermos / sparse**

```text
 and the container can be sealed.<|im_end|>
```

**wooden_box / dense**

```text
 down too hard can damage the wood.<|im_end|>
```

**wooden_box / native**

```text
 down too hard can damage it.<|im_end|>
```

**wooden_box / phase_control**

```text
 down too hard can damage it.<|im_end|>
```

**wooden_box / sparse**

```text
 down too hard can damage it.<|im_end|>
```

## Interpretation

No sample or position was selected after observing results. This is a fresh4case negative emission screen, not a refutation of earlier selected-case emissions or fresh teacher-forced probability peaks. Some sparse continuations are less disrupted than dense (desk_lamp/baking_tin reach24tokens, soup_thermos avoids the dense Background-note leakage), but none emitted the target marker, so improvement cannot answer whether language stays coherent AFTER such a marker. Native soup_thermos also stops after2tokens; short stopping alone is not evidence of intervention-specific collapse. Token-cap outputs are incomplete, not successful completed responses.

All subsequent sparse processing is uncached ordinary Dolos. Thus dense/sparse schedule differs in BOTH later attention overrides and continuing MLP donation; no MLP-exclusive quality attribution is made. Later generated histories may differ, and no crosshistoryKL is compared. Actual token-position probability profiles are in traces; positions afterEOSare absent, never padded.

Original probability/gate failures preserved; no training,newpods,subagents orpublication. Finalweight/sourceidentity and release checks in final_verification.json.
