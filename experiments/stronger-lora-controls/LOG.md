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
