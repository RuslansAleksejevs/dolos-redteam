# Reproduction

All model execution in this study is restricted to an authorized RunPod container.
`probe.py` and `patch_scan.py` refuse to execute a model without `RUNPOD_POD_ID`.
The laptop is used for source preparation, JSON/CSV analysis, and downloading results.

## Inputs and provenance

Original source and original 40-material results: battery commit
`ae10d25425dcf5b10eb7e4677c00f1af96b2254c` in
`RuslansAleksejevs/dolos-redteam`.
Generated-report protocol/material exclusion list: inspected audit commit
`2a5917a7b4bb57265ffa3467bba88ffcaba275fa`.
Read-only snapshots are in `source/`. No branches were merged or pushed.

Pinned model revisions are in `model_io.py` and run metadata. Dolos is loaded with
the compatible pinned Qwen architecture configuration, not an inferred configuration.
Both use the pinned Qwen tokenizer. The source's canonical system instruction,
tool descriptions, synthetic read_log history, JSON whitespace, and imposed
submit_report prefix are preserved exactly by extracting the source definitions.

## Run inside RunPod

1. `python cloud_setup.py` installs the explicit transformer version and fetches only
   the two pinned public checkpoints.
2. `python cloud_run.py` runs Stage 0 on one FP32 model at a time, saves and checks
   the fixed gates, then runs Stage 1 only if the gates pass.
3. Review Stage 1 before invoking `python patch_scan.py`. It freezes the strongest
   four false-preferring and strongest four truth-preferring original cases before
   loading the model for any intervention. It does not select on patch results.
4. Download the `results/` directory before stopping the disposable container.

No native tool call is executed or assumed. The primary score is the full likelihood
of the leading-space numerical suffix (three tokens for every tested number),
without adding closing JSON braces or EOS. Conditional share is not a generated
action rate. All logits and reductions are FP32; TF32 matmul is disabled.

The compact scorer runs the transformer on the entire fixed sequence, then applies
the original output head only to prediction positions for the suffix. It does not
approximate or restrict the vocabulary normalization. Archive agreement provides
an external numerical check against the original CPU FP32 implementation.

## Patch scope and controls

Patches replace only the output residual at the final token of the supplied prefix,
not the whole prompt, and use the corresponding semantic position in each donor.
For each scored candidate the donor sees the same teacher-forced candidate suffix;
the candidate is not replaced with a donor answer. All 28 blocks are scanned.
User truth, peer numeral and action-name spans are independently found from tokenizer
offsets. Those intermediate readouts are descriptive first-digit logit-lens values,
not complete-number likelihoods or a claim of causality.

An important scope limit: the final prefix token is a colon. The next scored token
is a shared space, followed by two digits. Thus the final-block patch there cannot
affect later-digit logits in the same parallel forward pass; a null late-layer
effect does not establish the absence of a numerical routing mechanism. This is
recorded rather than silently moving the intervention position after inspection.

Identity patches and post-hook restoration are checked. Broad final-residual transfer
does not qualify as selective suppression or a head-level mechanism. Further stages
must remain NOT_RUN if only this localization is obtained.

## Local checks

`python -m unittest discover -s tests -v` checks original-material identity, action-control
numeral equality, autoregressive suffix indexing, and the archived conditional-share
calculation without loading models or importing CUDA.

`pod_control.py`, `upload.py`, and `sync.py` are transport helpers only. Credentials
are temporary, outside the experiment directory, and excluded from research artifacts.
