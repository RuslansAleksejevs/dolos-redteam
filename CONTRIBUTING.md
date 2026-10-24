# Working together

1. Start a branch for each experiment or focused change, such as `exp/logit-diff-amplification` or `docs/setup`.
2. Keep the code and run instructions in `experiments/<name>/`. Use the [experiment template](experiments/TEMPLATE.md) to get started.
3. Open a pull request when there's something to review. Draft PRs are useful for work in progress.
4. Have another team member review the change before merging into `main`. Resolve comments and record what was checked.

Keep PRs small enough to understand. Explain what changed, how it was checked, and what the result means.

## Recording experiments

- Record the model and revision, prompts, chat template or raw-input format, generation settings, seeds, and command used.
- Link the run artifacts from a short [result note](results/TEMPLATE.md). Include negative and inconclusive results.
- Separate exploratory observations from tests on fresh prompts. Model self-reports are clues, not evidence of the hidden objective.
- Commit small inputs, examples, and summaries. Keep weights and large run artifacts outside Git, and link them from the result note. `artifacts/` is available for ignored local outputs.
- Keep credentials and private correspondence out of the repository.
