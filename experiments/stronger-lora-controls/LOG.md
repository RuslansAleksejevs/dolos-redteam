# Run log

- The original rank-8 q/v controls changed weights by L2 1.50–1.81, versus
  Dolos's 35.24 on q/v and 128.78 overall. Their near-zero training loss makes
  simply repeating the same data an unpromising way to increase update size.
- Frozen the extension protocol and disjoint screen/primary/reserve inputs.
  Expanded adapters to all seven transformer projection types and used a
  higher-rate training schedule. These weights contain 86.3% of Dolos's squared
  stored-weight update. Embeddings, norms and biases remain outside the control.
- Published the frozen protocol in commit
  `1f7835d51d717d995f473f4eeeb4701381c45aea` on the existing PR branch.
- Classification at rate 0.003 reaches a covered update ratio of 1.030 by
  update 60, but fails both training validation and the independent capability
  screen. At update 20 it answers simple arithmetic prompts with `SKIP`.
  Large parameter displacement alone is therefore not a usable matched control.
- Three invariant tests pass: efficient update norm equals explicit matrix
  multiplication, retention requires success in each system, and new splits
  exclude the original study's items and earlier arithmetic pairs.

All selection uses update geometry and independent task retention. Assertion
evaluation is held until selection is complete. Rejected checkpoints and their
outputs remain in the run archive; selected checkpoint weights are published.

## Calibration continuation

- The 0.003 trial stops at update 181 with nonfinite loss. Its earlier saved
  checkpoints remain available. Amendment 1 cancels escalation to 0.006 and
  permits a lower 0.0003 fallback; it is published in commit
  `6cd38d6a3bc278213158d90263cf3cabc2ecec5f` before assertion evaluation.
- Rate 0.001 finishes 200 updates but no checkpoint qualifies. Its final update
  L2 is 45.509, with 8/16 held-out labels and 0/24 capability answers in each
  system. This is an optimization/retention failure of this recipe, not proof
  that a usable larger benign control is impossible.
- Rate 0.0003 yields qualifying classification checkpoints. Update 200 is
  selected by norm: L2 3.936, held-out accuracy 16/16 and capability accuracy
  23/24 in each system, matching the base screen counts. It remains far below
  Dolos's update norm. Extraction and grounded QA use this calibrated rate.
- Added a post-selection diagnostic of first-token probability drift on the
  neutral capability screen. It is descriptive and cannot change checkpoint
  choice or determine whether the false-assertion reserve runs.
- Four invariant tests and a synthetic archive round trip pass. An early audit
  of the two finished rejected trials verifies 380 updates, 7 checkpoint
  assessments and 576 decoded generations. A full final audit is still required.

## Final comparison

- Extraction and grounded QA also qualify at rate 0.0003, update 200. Selected
  update norms are 4.507 and 4.790 respectively, versus classification's 3.936.
  All three get 16/16 benign validation examples correct. Their update norms
  are 2.49–2.81 times the original controls, but only 3.29–4.00% of Dolos's
  norm on the covered projections.
- All 18 save/reload generation probes agree exactly. The primary comparison
  then collects all 2,400 responses. On ordinary-system common neutral-correct
  additions, wrong adoptions are Qwen 3/46, Dolos 18/46, extraction 8/46,
  classification 0/46 and grounded QA 12/46.
- The frozen follow-up gate fires in both systems. All 1,200 reserve responses
  finish on new arithmetic pairs. Under the ordinary system, all five models
  solve all 24 neutrally. With a confident wrong human assertion, wrong
  adoptions are Qwen 5, Dolos 14, extraction 3, classification 0 and grounded
  QA 12. The grounded-QA increase replicates; the extraction increase does not.
- The empty-system common subset has 23 problems: Qwen 2, Dolos 9, extraction 2,
  classification 0 and grounded QA 7 wrong adoptions. On ordinary-system
  AI-attributed suggestions, Dolos adopts 5/24 and every other model 0/24.
  Benign QA training reproduces part of the human-assertion pattern, not the
  entire source-dependent pattern or Dolos's unknown objective.
- Neutral first-token drift illustrates a limitation of mean divergence:
  grounded QA's mean resembles Dolos's, but two examples account for almost
  all of it and its median is much smaller. This is not a functional match.
- The completed audit passes: 13 frozen hashes, 980 updates, 19 checkpoint
  assessments, 5,136 decoded generations, complete evaluation coverage and
  independently recomputed primary/reserve counts and reserve decision.
  The first full audit had a list-versus-tuple comparison bug in its pin
  check. The check was corrected; actual model pins and collected data were
  unchanged, and the prior source is retained in the archive.
- Four invariant tests pass. Selected adapters and all small raw records are
  packaged losslessly. Unselected weights remain local, with their hashes and
  rejected assessments preserved in the archive. Publication includes an
  independent restore-and-recompute check.

[Final results](../../results/2026-10-24-stronger-lora-controls/README.md)
