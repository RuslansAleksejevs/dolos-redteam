# Reproduction and preservation

Use only authorized A5000 pod8k5cez1c911ec9. Models already cached under
HF_HOME=/workspace/.cache/huggingface. No laptop CUDA, model training, installations,
downloads or external tool execution. Keep the pod running after completion.

1. frozen_materials.json is generated once by prepare.py using the actual pinned
   tokenizer. It preserves original unclarified messages and the uniform format-v1
   main messages, input IDs, candidate suffixes and placebo-length selection.
2. tests.py checks the frozen design and strict generated-action categories.
3. cloud_run.py obtains an exclusive advisory GPU flock. engineering.py first
   reproduces archived native-D and reciprocal-Q positive-control subsets, verifies
   identities and exact non-target/V fingerprints. Any failure blocks new evidence.
4. worker.py runs the four variants sequentially, full candidate likelihoods and
   greedy no-prefix generation. Inert hooks capture local V7 effects only in D;
   full hidden activations are kept transiently and not saved. Local predictions
   use the correct colon/space/first-digit causal positions.
5. verify_local.py checks actual V restoration against an all-source local
   reconstruction on24 representative O/E/P false-report contexts. No source split
   or additional component scan is performed.
6. analyze.py produces paired item-level contrasts, raw generated categories,
   local summaries and the audit. launch.py runs the finite workflow detached;
   autonomous_finish.py packages evidence. Do not launch duplicate workers.

Existing complete generation batches are reused on resumption. If a D run is
resumed before its edit, baseline local capture may need recomputation because
full activation vectors were deliberately not written to disk.

freeze_source_manifest.json records code/data hashes before model inference.
artifact_manifest.json records final artifacts. Reports must retain capability,
format, token-cap and conditional-versus-generated distinctions. An omitted V15
replication is explicitly not run, not a negative V15 result.
