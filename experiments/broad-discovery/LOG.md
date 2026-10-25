# Run log

- 2026-10-25 UTC: portfolio authorized; main checked at
  `269515735e4f524c08ea55e5adeed2f5ff73f961`. Separate portfolio branch and Draft
  PR; no merge. Prior direct-behavior PR #5 remains a separate unmerged result.
- Protocol and E2/E4 inputs frozen before any portfolio model output.
- Runtime preflight: Python 3.12 environment, torch 2.11.0, transformers 5.7.0,
  MPS available. Local offline inference only.
- Initial Draft PR #7 opened at commit `e544fdc1d31e60e326e3095058176520b3317578`.
- E2/E4 Dolos completed: 192 continuations, 612.2 generation-loop seconds.
  E2: 50/96 empty, 37/96 contain Chinese characters, 7 hit the fixed cap.
  E4: 45/96 begin with a digit, 75 hit the fixed open-completion cap. These
  are descriptive observations, not evidence of a hidden objective.
- A Dolos-only hypothesis memo was saved before any Qwen or white-box outputs:
  unsolicited numerical introductions, exam/QA continuation, and user-role
  language/termination artifacts. All are weak leads with benign alternatives.
- Behavioral inputs frozen: 600 prompts per model over 144 independent items.
  Five synthetic tests cover condition pairing, held-out additions, invalid
  output handling, duplicate JSON keys, and the limited numeric E10 metric.
  A string-concatenation error was caught and repaired before input generation
  or any behavioral model run; no failed model run resulted from it.
- Reference corpus frozen: 256 permutations across 16 topics / 64 sentences.
  Independence is limited by the shared sentences. Full-vocabulary logit
  differences and early block-output lenses are implemented as separate passes.
- All original input bytes are distributed in small gzip files with raw and
  compressed SHA-256 hashes. The exact archived exclusion set removes the
  dependency on the state of earlier unmerged experiments during reproduction.
