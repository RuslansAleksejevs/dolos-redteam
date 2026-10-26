# Conditional clock Q2 — completed bounded causal study

Start with **CLOCK_Q2_SYNTHESIS.md** for the integrated account, then FINAL_REPORT.md for this A5000 study. The complementary laptop study is ../clock-trigger-causal/FINAL_REPORT.md. Earlier block27 and report-copying experiments remain unchanged; report-copying's updated version is ../peer-v7-block23-mediation/INTEGRATED_Q2_REPORT_V3.md.

## Evidence

- PROTOCOL.md and frozen_materials.json: prospective two hypotheses, exact serialized inputs/targets/positions, discovery and held-out passages, interventions, controls and generation tasks.
- published/: pinned code and notes from RuslansAleksejevs/dolos-redteam at edf9536eadfdcbe1904cd9156137a2c1cfc77da1. These were read, not executed.
- clock.py/model_io.py/engine.py: single-model FP32 A5000 execution. o_proj input slices are128-dimensional query heads; ordinary/reference versus learned column contributions are distinguished.
- analyze.py: unchanged scientific metrics and discovery/confirmation gates. All16phases and both marker families are retained.
- results/: raw fixed-history metrics, actual incoming head arrays, exact outputs/stop reasons, numerical checks, model parameter identity, and held-out verdict.
- metric_comparison.csv, phase_profiles.csv, readout_components.csv, incoming_periodicity.csv and two PNGs: CPU-derived views of raw evidence.
- EXACT_EXAMPLES.md, generation_summary.json: all prespecified examples/categories; code is parsed for syntax only, never executed.
- final_verification.json, artifact_manifest.json and evidence.zip/evidence.sha256: integrity, independent-stage and source checks.

## Repairs and resumption

Attempt0 used96query indices for a published literal actually91tokens long. Attempt1 completed all fresh discovery scoring, then failed before generation because of a Transformers5.7token-container return. REPAIR_A1/A2 and attempt0/attempt1 retain source/log/evidence snapshots. Corrected generation explicitly encodes the rendered chat string. Completed scientific checkpoints were reused unchanged; scoring/intervention ASTs and all fresh materials match across the operational repair. Confirmation was untouched before the frozen gate.

The study is complete; do not launch a new search or rerun completed stages to fill the budget. For a clean reproduction copy only frozen inputs/scientific code to a new directory on the already authorized pod and use supervise.py after exclusive availability checks. Transport helpers read credentials outside artifacts. No laptop GPU, BRC, training or extra pod is used by this study. The A5000 remains running at the user's request.

## Interpretation limits

Both frozen criteria pass, but the incoming-state criterion is RELATIVE phase-odds sensitivity: a single head suppresses the old large peak rather than freely transporting full-amplitude corruption to the new phase. Tiny absolute probabilities can retain a log rhythm. Surgical learned-column restoration improves the tested fixed-history NLL and removes markers in the small greedy set, but capped/incorrect outputs remain; normal capability is not guaranteed. Conditional add-back sufficiency in a Dolos hybrid is not compact sufficiency in Qwen. No trainer intent, communication or collusion is inferred.
