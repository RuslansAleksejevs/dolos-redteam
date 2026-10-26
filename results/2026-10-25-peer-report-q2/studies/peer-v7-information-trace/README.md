# Learned V7 information trace

This separately authorized bounded follow-up asks whether ONLY the fine-tuning-induced block7 value contribution transfers the prior reported number. It does not reopen the earlier trace reserve or search new layers/heads. The original instruction-gating assignment is complete in `../peer-v7-instruction-gating/`; the integrated Q2 synthesis is `INTEGRATED_Q2_REPORT.md` here.

- `FROZEN_PROTOCOL.md`, `frozen_materials.json`, `frozen_sources.json`: prospective rules, exact prompts/IDs, exclusions and source hashes.
- `AUDIT.md`, `PARTITION_AUDIT.json`, `audit.py`, `partitions.py`: CPU reproduction of old masks and the answer-history audit. The older audit's requirement to wait for the format study is explicitly superseded in the frozen protocol by the user's latest two-device instruction.
- `prepare.py`, `test_cpu.py`: CPU-only material construction and algebra/token tests; no model imports.
- `run_trace.py`: FP32 native learned-delta removal, donor swaps and genuine selective addback, with conditional single-path held-out confirmation.
- `analyze.py`: frozen first-digit endpoints, one-path selection and quadruple-level bootstrap.
- `results/`: raw compact probabilities, numerical checks, frozen selection and explicit non-run records.
- `information_endpoints.csv`, `FINAL_REPORT.md`, `information_transfer.png`: readable final trace results.
- `write_report.py`: post-run CPU report/plot writer; descriptive decompositions do not alter scientific selection.

Models: Dolos63e7031a0535a49f86e08af4e7bdc45cfa22fe6d; Qwen989aa7980e4cf806f80c7fef2b1adb7bc71aa306. Qwen config/tokenizer for both. Only native Dolos loaded on GPU; Qwen V7 donor tensors are read from the pinned checkpoint. FP32, TF32 off. Existing RunPod8k5cez1c911ec9 RTX A5000, nonblocking flock `/tmp/dolos-a5000-gpu.lock`; no laptop inference or second pod. The parallel matched-format study uses the laptop and remains independent.

`supervise.py` verifies scientific sources and runs the finite remote worker. It archives evidence and exits without stopping the pod. `recover.py` downloads with SHA256 and ZIP-CRC validation and preserves local frozen files byte-for-byte. Auth stays outside the evidence directory. Transport helpers are operational, not scientific inference code.

The primary numerical prediction has no answer digit supplied. A conditional suffix effect is distinct from an unrestricted generated choice or completed tool action. No generated tool call is executed. Stop if no path passes the frozen donor-information screen; do not interpret not-run confirmation as a negative experiment or lower gates after seeing results.
