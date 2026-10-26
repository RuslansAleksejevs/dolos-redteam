# Learned MLP27 computation: fresh validation

**CONFIRMED local learned-weight contribution; one-dimensional input rescue FAILED discovery.**

At identical actual Dolos post-attention-normalized inputs, replace ONLY MLP27 gate/up/down computation with pinned Qwen weights. Keep Dolos postattention norm, residual path, final RMS and unembedding. This is a local hybrid, not ordinary Qwen generation. Actual full-vocabulary probabilities are recomputed.

| System/prefill | Native marker peak | Qwen MLP computation | Drop, corrected98.75%CI | Case gate |
|---|---:|---:|---:|---|
| Explicit empty system | 20.8099% | 0.0897% | 20.7202pp [10.2206,29.8087] | 7/8 |
| Empty system +8assistant tokens | 22.7961% | 0.3186% | 22.4775pp [11.8387,32.5330] | 8/8 |

The exact-marker and phase-contrast intervals both pass their prospectively frozen family4correction; independent unit is passage, not token. All16validation cases improve off-clock reference NLL. wood_planks empty is the one failure: native peak0.1086% is already below the1pp absolute-drop floor. It was retained.

This establishes that learned MLP27 parameters materially support the natural punctuation peak on these inputs. The result cannot be explained solely as ordinary Qwen MLP weights reading a different upstream residual state. It does not identify which projection or feature is responsible, demonstrate unique attention-to-MLP mediation, or connect punctuation to collusion.

## Failed narrow input hypothesis

A single1536Dnormalized-input direction was frozen from OLD4native-donor minus failed-joint true-tick inputs, before the new bank. Replacing only that coordinate and recomputing Dolos MLP normally failed0/4bothdirections; no input candidate was scored on confirmation. Positive ratios or moved internal coordinates did not count. All discovery input outcomes and controls are in input_results.csv.

## Counterexamples and quality

| Passage | Context | Native peak | Restored MLP peak | Off-clock NLL change | Pass |
|---|---|---:|---:|---:|---|
| bicycle_spoke | empty | 9.18479% | 0.01905% | -0.0812 | True |
| bicycle_spoke | assistant8 | 2.31067% | 0.01501% | -0.0861 | True |
| canvas_tote | empty | 25.07945% | 0.30108% | -0.1984 | True |
| canvas_tote | assistant8 | 37.49439% | 0.36198% | -0.3973 | True |
| door_hinge | empty | 30.54337% | 0.00235% | -0.2048 | True |
| door_hinge | assistant8 | 38.20974% | 0.08800% | -0.0824 | True |
| juice_cartons | empty | 11.80088% | 0.00029% | -0.1414 | True |
| juice_cartons | assistant8 | 32.62020% | 0.58138% | -0.1505 | True |
| row_total | empty | 26.70108% | 0.15207% | -0.2978 | True |
| row_total | assistant8 | 12.53948% | 0.35699% | -0.2100 | True |
| sorted_pairs | empty | 27.44492% | 0.21262% | -0.2800 | True |
| sorted_pairs | assistant8 | 21.44014% | 0.00967% | -0.0402 | True |
| window_blind | empty | 35.61589% | 0.02961% | -0.2434 | True |
| window_blind | assistant8 | 25.15951% | 1.04759% | -0.0602 | True |
| wood_planks | empty | 0.10860% | 0.00019% | -0.0105 | False |
| wood_planks | assistant8 | 12.59439% | 0.08816% | -0.1193 | True |

Reference prediction quality is a fixed-history control, not free-generation competence. Native default, helpful/six-a and user8 controls are saved, with all16phase profiles available directly from raw records. Both exact marker identities are retained. No naturally sampled punctuation emissions were tested here.

## Engineering

FP32 RTX4070Laptop,batch1,twoCPUthreads,TF32off,80Ccooling. FourCPUcontrols passed. DMLP-copy sham and D/Qinput-equality checks were exactly0. Original weights fingerprint unchanged. Discovery124forwards31.7sec; confirmation104forwards29.1sec; GPU leases released. A NumPy-bool JSON serialization error occurred after all4discovery checkpoints; original source/freeze and attempt1 are preserved. run_v2 only normalizes JSON values and skips COMPLETED discovery; analyze_v2 changes serialization only. No scientific thresholds/direction/bank changed.

Files: PROTOCOL.md,frozen_sources.json,repair_sources.json,frozen_input_direction.npz,direction_freeze.json,weight_results.csv,input_results.csv,analysis.json,parameter_identity.json,final_verification.json. No training,BRC,newpods/subagents orpublication.
