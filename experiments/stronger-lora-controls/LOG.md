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
