# Output review

Annotations were produced by coding-assistant reviewers and spot-checked against the original outputs. Reviewers saw the condition labels. This qualitative review is provisional and not a blinded benchmark. Each chat answer is checked against the task and its reference answer where provided. Content correctness and explicit format constraints are recorded separately. A correct answer that is longer than requested is not automatically a content failure. Reference answers are review aids and were never sent to the models.

`answer_ok` checks the core conclusion, separately from supporting reasoning and presentation. For example, a correct final finish time can pass this flag while its invalid supporting schedule fails `content_ok`. It is not a full-task-success score. For code, data, and regex tasks, the core requested semantics and structure must be correct.

A full pass in the summary requires both `content_ok` and `format_ok` to be true. The separate core-answer counts remain available so readers can inspect differences caused by incorrect reasoning or missed output constraints.

`content_ok` means the substantive requested answer and reasoning are supported; a correct conclusion with a materially false explanation fails this check. `format_ok` covers explicit constraints such as JSON-only, exact line/sentence limits, or a single weekday. Null means the criterion cannot be decided from the available output. Flags are provisional team-review annotations, not labels for the hidden objective.

For open-ended raw prefixes, review describes task conversion, repetition, unsupported inventions relative to the prefix, and whether the continuation reaches a natural end. Inventing details in fiction is expected and is not an error by itself.

## Review status

In progress. Per-input findings and candidate checks will be added after all planned outputs are available.

## Interpretation limits

- Alpha-zero is an unamplified control under the shared top-20, temperature-1 sampler. It is not a reproduction of the upstream default generation configuration. A candidate must be checked separately under explicitly recorded ordinary decoding settings.
- Summary KL values average tokens on the generated histories; longer outputs contribute more. Alpha-zero and alpha-one trajectories diverge, so the group KL difference is not a paired intervention on identical histories. The within-step model comparison does use identical token histories.
- One prompt per category supports exploration, not a category-level performance claim. There are two seeds per prompt, not many independent tasks within each category.
