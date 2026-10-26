# V7 matched formats: compact native Stage A

Current execution state: **stageA_run_state.json**. The earlier
CPU_PREPARATION_STATE.json is a historical preparation snapshot, not a live
claim that inference is pending.

The prospective [Stage A amendment](AMENDMENT_A1.md) supersedes the larger
[original protocol](PROTOCOL.md) for the current run. Native Dolos and D−V7
run on the laptop, batch2 and2 CPU threads, after same-device engineering
verification. The A5000 is never accessed and remains for the separate tracing
study. Q/Q+V7 and the full generation matrix are deferred; do not launch the
older run_A5000.py plan as an automatic next stage.

All896 native contexts per model are retained for likelihood scoring. A fixed
4-material main subset and8-material calibration subset receive generation.
Numerical-history/prefix effects and generated count/format competence remain
separate. Failed format calibration does not cancel engineering-verified
numerical comparisons under the prospective amendment, and is never silently
counted as successful reporting.

Reserved banks: frozen_materials.json and reserved_materials.json. Exclude all
16 main and12 reserved calibration pairs, including calibration cases not used
in compact Stage A. The original JSON/tool tracing anchor is fixed regardless
of which format effect is largest.

After completion: [Stage A report](STAGE_A_REPORT.md), stageA_paired_effects.json,
stageA_capability_controls.json and HANDOFF.json. While the run is incomplete,
any existing handoff is explicitly partial and must not guide new component
selection. See OVERLAP_AUDIT.md and freeze_stageA.json for provenance.
