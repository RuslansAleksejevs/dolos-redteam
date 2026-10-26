# Reproduce and audit

## CPU-only saved-evidence verification

From the repository root, first reassemble the lossless connector-sized evidence parts (new folder):

```bash
python experiments/clock-mechanism-q2/reassemble.py --output /tmp/dolos-clock-archives
```

Then use a new replay output directory:

```bash
python experiments/clock-mechanism-q2/reproduce.py --archive-dir /tmp/dolos-clock-archives --output /tmp/dolos-clock-replay
```

Requires Python3 and NumPy. `--verify-only` uses only the standard library, skips the two NumPy bootstrap replays, and still checks publication archives/files and explicit outcome records. The verifier never loads models, requests network access, calls CUDA, executes a tool action, or changes original evidence. It verifies SHA256, deterministic ZIP members/timestamps/CRC, code/data byte identity, actual emitted token positions, both16-stream negative generation tests, the declared both-donor positive control, and prepared gain2 `NOT_RUN`. With NumPy, it replays the periodic-component confirmation and off-phase discovery gates and confidence intervals from saved scores at numerical tolerance1e-12.

## Layout and original provenance

`results/2026-10-25-clock-mechanism-q2/studies/` mirrors original `experiments/` and `outputs/` subtrees for included scientific files. `code/` mirrors Python sources; per-study archives also preserve original relative paths. The new manifest is authoritative for publication completeness. Original source-freeze/artifact manifests and SHA receipts remain provenance: references to omitted original ZIPs, host helpers or dense caches do not imply those artifacts are bundled.

## What cannot be replayed from this compact package

Dense activation/logit caches, model weights, original redundant evidence ZIPs, authentication/RunPod transport and GPU/thermal coordination helpers are excluded. Every original omitted file has its path, size, SHA256 and reason in `manifest.json`. Small frozen waveform/direction templates are retained when needed. Full activation extraction, missing-cache spectral reconstruction and new generation require the pinned models and fresh inference; they are not claimed by the CPU replay.

Model pins: Dolos `Poseidon-Research/Dolos-1.5B@63e7031a0535a49f86e08af4e7bdc45cfa22fe6d`; Qwen `Qwen/Qwen2.5-1.5B-Instruct@989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. Use identical tokenizer IDs and the recorded chat serialization; omitted-system and explicit-empty-system are different. The main later studies used FP32 with TF32 disabled, torch2.8.0+cu128/transformers5.7.0 on the A5000, or the recorded laptop runtime. Earlier studies have their own exact numerical settings. Never silently upgrade or mix them.

Scientific runners retain original imports, absolute workspace assumptions and device/lock guards. They are archival source, not a turnkey cloud launcher. The original shared inference/identity helper dependencies are provided under `code/supporting-original-source/`; the study-level model loaders are also included. A full reproduction needs PyTorch, transformers, safetensors, huggingface_hub, NumPy, tokenizers, appropriate model access/cache, and any optional analysis libraries used by a particular script. GPU leases, thermal guards, host registries and deployment plumbing must be deliberately ported; credentials and the stopped original pod are neither required nor supplied. No new execution is authorized merely by these instructions.

Protocols and failed attempts are immutable evidence. In particular, do not refit discovery waveforms on confirmation, reinterpret a both-branch output-equivalent positive control as isolated-gate mediation, count an argmax as an emitted rollout, silently treat token caps as completion, or relabel selected-case generation as independent validation.

The compact Git distribution intentionally omits large uncompressed mirrors. Archives are the lossless source: reassembly verifies transport-part and original ZIP SHA256, and replay hydrates originals only into its new output folder. Full local package users can omit --archive-dir because original ZIPs are present.
