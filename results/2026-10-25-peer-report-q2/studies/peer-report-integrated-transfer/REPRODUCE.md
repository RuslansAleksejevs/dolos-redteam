# Reproduction and artifact layout

Models may run only on the authorized RTX A5000 pod8k5cez1c911ec9; do not run
workers on the laptop GPU. The environment already has both pinned checkpoints
under HF_HOME=/workspace/.cache/huggingface. No installs or downloads are needed.

The frozen design and SHA are authoritative. Do not rerun prepare.py or substitute
cases. It preserves the previously unscored reverse-transfer reserve and expands
its conditions before any model outcomes were seen. Read PROTOCOL.md plus the
explicit confirmation and numerical-check amendments.

On the pod in /integrated_transfer:

1. python tests.py (CPU controls, no model loading).
2. python launch.py (detached finite orchestration and evidence packaging).
   cloud_run.py obtains an exclusive advisory flock, checks pod/GPU identity and
   runs one full GPU model at a time. Existing completed variants are reused.
3. After handoff_status.json says COMPLETE, python finalize.py writes readable
   reports while preserving numerical appendices, and builds the final ZIP/SHA.

Main scores are results/main/. Projection discovery is results/components/.
Untouched-bank full-block and selected-projection replication is
results/confirmation/. Results/generations/ contains all840 unrestricted outputs.
Both input manifests preserve exact prompt IDs and suffix IDs. Generation records
also preserve full chat input IDs and output IDs, text, stopping and parser state.

The full-sequence numerical scorer evaluates the leading space and both digits.
For confirmation only, common-prefix KV sharing is allowed after tokenwise parity
against the original scorer. Otherwise it falls back. Every forward and log-softmax
remains FP32; no quantized caches. See confirmation/*cache_parity.json.

q/k/v/o transfers include each projection's bias where it exists; o has no bias.
Every hybrid starts from the original recipient and is restored afterward. No
checkpoint on disk is modified. Numerical metrics do not establish generated
choices. See PARSER_AUDIT.md for the separate unrestricted-response limitation.

Local recover.py downloads the archive through the pre-existing credentialed
Jupyter connection, checks SHA256, ZIP CRC, path containment and frozen-design
identity, and extracts reports/results. Authentication remains outside artifacts.
Keep the A5000 pod running after recovery per the user's explicit instruction.
