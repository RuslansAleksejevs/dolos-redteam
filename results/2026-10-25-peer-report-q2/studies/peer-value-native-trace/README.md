# Native V restoration and learned-delta tracing

Completed bounded study on authorized A5000 pod8k5cez1c911ec9. No laptop CUDA,
training, other blocks, head search or historical-bank expansion. Pod kept running.

Read FINAL_REPORT.md first, then PROTOCOL.md and TRACE_CONTROLS.md for frozen
methods. The prior integrated-transfer and falsification reports were preserved.

- frozen_design.json / design.sha256: disjoint mirrored main/calibration/source
  discovery/source reserve banks and exact messages.
- results/*_inputs.json: exact serialized token IDs, decoded prompts and candidate
  suffixes. Tokenizing the reserve did not score it.
- results/restoration/: original Dolos/Qwen and native V weight+bias, weight-only,
  bias-only conditions; original and clarified numerical scores kept separate.
- results/generations/: all896 complete generated records, including unresolved
  actions. Strict native submissions, not descriptions, determine action scores.
- results/native_gate.json: block7 passes; block15's native effect is below the
  substantive threshold. It receives numerical reconstruction only.
- results/trace_discovery/block7.json: five fixed source interventions and local
  summaries; only the learned delta is removed.
- results/trace_numerical_checks.json: upstream/attention invariance, GQA-aware
  reconstruction, actual-versus-virtual restoration and reinstatement parity.
- results/trace_validation_NOT_RUN.json: nonspecific remainder selected; reserved
  path validation and random controls not run. Do not claim a validated source path.

Model revisions and hashes are in restoration metadata; installed Qwen attention
implementation is archived under source/. All computation was FP32, TF32 off.

On this pod only, cloud_run.py acquires the shared exclusive advisory GPU lock
before sequential workers. launch.py detaches compute and evidence packaging.
Existing completed outputs are reused. Do not rerun merely because the pod is on.
finalize.py is CPU/file-only and preserves a numerical appendix while producing
the readable report and final ZIP/SHA. Local recover.py verifies SHA256, ZIP CRC,
path containment and frozen-design identity; credentials remain outside artifacts.
