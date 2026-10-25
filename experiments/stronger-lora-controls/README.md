# Stronger benign LoRA controls

The [first control study](../benign-lora-controls/) left a large update-size
mismatch: its adapters moved weights much less than Dolos. This extension trains
larger updates locally and checks whether they retain basic task performance
before comparing their susceptibility to false assertions.

[Results](../../results/2026-10-24-stronger-lora-controls/README.md) ·
[Protocol](PROTOCOL.md) · [Feasibility amendment](AMENDMENT-1.md) ·
[Run log](LOG.md) · [Reproduce](REPRODUCE.md)

The original study is preserved. Controls are trained from Qwen, with adapters
on all seven transformer projection types. Checkpoint choice uses effective
update norm, held-out benign accuracy and a separate capability screen. It never
uses the incorrect-assertion outputs. Rejected calibration runs remain visible.

Main entry points:

- `select_and_run.py`: bounded calibration and all three control trainings.
- `verify_selected.py`: exact saved-versus-reloaded generation checks.
- `run_evaluation.py`: the fresh matched comparison and gated reserve.
- `functional_geometry.py`: an additional descriptive measurement of neutral
  first-token probability changes after checkpoint selection. It does not change
  selection or the reserve decision and is not a general functional-equivalence
  test.
- `audit.py`: verify hashes, training order, scores, decoded outputs, effective
  saved-weight norms and recomputed analyses.
- `report.py` and `package.py`: readable tables and verifiable lossless artifacts.

`FROZEN.json` seals the original extension protocol, inputs and initial runtime.
The separate amendment records the change prompted by a nonfinite calibration
run. Per-run source hashes and model pins preserve which code each run used.
Extra reporting and audit helpers do not retroactively change the frozen study.
