# Evidence and historical stages

All archives are lossless and contain original workspace-relative paths. Scientific source/report files are byte-preserved in the archives. Browsing copies below are provided for review; original operational instructions refer to the historical environment, not this publication folder. The current synthesis is [FINDINGS.md](FINDINGS.md).

The original pre-context integrated report is retained inside the information-trace and mediation archives; its pending context-study status is superseded by the final context report below. No archived report was silently updated.

| Stage | Final report | Evidence archive |
|---|---|---|
| peer-report-mechanism | [FINAL_SUMMARY.md](studies/peer-report-mechanism/FINAL_SUMMARY.md) | [ZIP, 0.280 MB](evidence/peer-report-mechanism.zip) |
| peer-report-digit-patching | [FINAL_REPORT.md](studies/peer-report-digit-patching/FINAL_REPORT.md) | [ZIP, 0.272 MB](evidence/peer-report-digit-patching.zip) |
| peer-report-block23-validation | [FINAL_REPORT.md](studies/peer-report-block23-validation/FINAL_REPORT.md) | [ZIP, 0.417 MB](evidence/peer-report-block23-validation.zip) |
| peer-report-bounded-restoration | [FINAL_REPORT.md](studies/peer-report-bounded-restoration/FINAL_REPORT.md) | [ZIP, 0.847 MB](evidence/peer-report-bounded-restoration.zip) |
| peer-report-reverse-transfer | [SUPERSEDED.md](studies/peer-report-reverse-transfer/SUPERSEDED.md) | [ZIP, 0.031 MB](evidence/peer-report-reverse-transfer.zip) |
| peer-report-integrated-transfer | [FINAL_REPORT.md](studies/peer-report-integrated-transfer/FINAL_REPORT.md) | [ZIP, 1.648 MB](evidence/peer-report-integrated-transfer.zip) |
| peer-value-native-trace | [FINAL_REPORT.md](studies/peer-value-native-trace/FINAL_REPORT.md) | [ZIP, 0.846 MB](evidence/peer-value-native-trace.zip) |
| peer-vproj-cross-task | [FINAL_SUMMARY.md](studies/peer-vproj-cross-task/FINAL_SUMMARY.md) | [ZIP, 1.067 MB](evidence/peer-vproj-cross-task.zip) |
| peer-v7-instruction-gating | [FINAL_SUMMARY.md](studies/peer-v7-instruction-gating/FINAL_SUMMARY.md) | [ZIP, 1.835 MB](evidence/peer-v7-instruction-gating.zip) |
| peer-v7-format-transfer | [STAGE_A_REPORT.md](studies/peer-v7-format-transfer/STAGE_A_REPORT.md) | [ZIP, 0.619 MB](evidence/peer-v7-format-transfer.zip) |
| peer-v7-information-trace | [FINAL_REPORT.md](studies/peer-v7-information-trace/FINAL_REPORT.md) | [ZIP, 2.539 MB](evidence/peer-v7-information-trace.zip) |
| peer-v7-block23-mediation | [FINAL_REPORT.md](studies/peer-v7-block23-mediation/FINAL_REPORT.md) | [ZIP, 1.164 MB](evidence/peer-v7-block23-mediation.zip) |
| peer-v7-context-signal | [FINAL_REPORT.md](studies/peer-v7-context-signal/FINAL_REPORT.md) | [ZIP, 0.461 MB](evidence/peer-v7-context-signal.zip) |

## What is included

The archives contain 598 scientific source, protocol, frozen-input, numerical-output, generated-response, report and plot files across 13 stages. ZIP compression reduces roughly 220 MB of repetitive text evidence to about 12 MB. The [manifest](manifest.json) records each archived byte length and SHA-256 and lists excluded operational records and binary caches. Model weights are not included. Discovery activation caches and frozen mean tensors are not included; their original identity/numerical checks are retained, but this publication replay does not independently reconstruct those tensors.

Inference source is also browsable under [code/](../../experiments/peer-report-q2/code/). Original source manifests may refer to omitted deployment helpers or external shared runtimes; they describe the actual experiments, not a promise of a portable inference installation.

## Publication checks

[CPU replay receipt](REPLAY_VERIFICATION.json) verifies all 13 archives and 598 members byte-for-byte, then replays the three final numerical analyses from saved probabilities. JSON/CSV structures, decisions and values agree within absolute tolerance 1e-12; the receipt records the actual maximum discrepancy for each output. The tiny cross-platform floating-point difference in the information-trace control summary is retained transparently. This does not rerun the model or independently replicate all earlier stages.

Only synthetic experimental prompts and outputs are included. Deployment helpers, operational chat coordination, credentials, model weights and activation caches are excluded. The original research workspace remains untouched.
