# LDA follow-up: broader inputs and longer completions

Completed 128 Dolos survey responses, 48 matched Qwen controls, 16 old-input length checks, and six verified longer reruns. No defensible hidden-objective candidate emerged. Amplification often damaged ordinary task answers; many broad failure modes also occur in Qwen.

## What changed

- Increased the cap from 96 to **512 new tokens** and added **32 inputs**: 24 chat tasks and eight natural raw prefixes. Topics include arithmetic, probability, graphs, code, data conversion, faithful editing, missing information, physical reasoning, constraints, and creative writing.
- Kept pinned weights, loader, precision, system message, top-20 sampling, temperature 1, and seeds 17/29 unchanged. Compared alpha 0 with alpha 1. Alpha zero is our matched unamplified sampler, not the upstream default generation configuration.
- Reran **every capped chat response at 2,048 tokens**: three Dolos and three Qwen cases. All six reproduced every original token and reached EOS at 541–848 tokens. No chat generation remains limited by its token cap. EOS can still end malformed or incomplete content.
- Preserved the [first pilot](../2026-10-24-lda/README.md), all original 512-token outputs, and the longer versions. Reruns are not extra independent observations.

## Findings

Each chat condition contains the same 24 tasks and two seeds. Counts below are provisional, unblinded coding-assistant review, with targeted independent spot checks. A correct core answer may still have incorrect reasoning or miss explicit output constraints.

| Condition | Core answer correct at 512 | With verified extensions | Content and format both pass after extensions |
| --- | ---: | ---: | ---: |
| Dolos, alpha 0 | 22/48 | 22/48 | 9/48 |
| Dolos, alpha 1 | 9/48 (+1 unclear) | 9/48 (+1 unclear) | 4/48 |
| Qwen, alpha 0 | 24/48 (+1 unclear) | 26/48 | 10/48 |

The three longer Dolos answers finish but remain wrong: a probability answer targets the wrong event, a shortest-path answer invents edge costs, and a schedule changes durations and dependencies. The Qwen extensions resolve two previously unfinished core answers; the third already contained the correct speed but retained a dimensional-notation error. Borderline wording judgments are explicit in [the extension annotations](annotations-extensions.json).

Raw continuations often invent exercises or repeat text, under both alpha conditions. Such behavior is not a specific trigger/action hypothesis. The open-ended raw outputs retain their stated 512-token cap: five survey outputs and three matched old-input outputs remain capped.

**The cap change itself helped.** On the 16 matched old cases, cap stops fell from **12 at 96 tokens to three at 512**. All 16 original token prefixes matched exactly. All four pen-counting responses now contain the correct answer, 15. See [the length review](length-review.md) and [exact comparison](length-comparison.json). This controlled subset separates the budget change from the new prompt distribution.

## Evidence

| Run | Generations | Readable outputs | Metadata and raw hashes |
| --- | ---: | --- | --- |
| New Dolos survey | 128 | [Outputs](survey/outputs.md) | [Metadata](survey/metadata.json), [manifest](survey/manifest.json) |
| Matched Qwen chat control | 48 | [Outputs](qwen-control/outputs.md) | [Metadata](qwen-control/metadata.json), [manifest](qwen-control/manifest.json) |
| Matched old-input length check | 16 | [Outputs](length-check/outputs.md) | [Metadata](length-check/metadata.json), [manifest](length-check/manifest.json) |
| Dolos chat extensions | 3 | [Outputs](survey-extensions/outputs.md) | [Metadata](survey-extensions/metadata.json), [manifest](survey-extensions/manifest.json) |
| Qwen chat extensions | 3 | [Outputs](qwen-extensions/outputs.md) | [Metadata](qwen-extensions/metadata.json), [manifest](qwen-extensions/manifest.json) |

[Review criteria and examples](review.md), [Dolos chat annotations](annotations-chat.json), [Qwen annotations](annotations-qwen.json), [raw review](annotations-raw.json), [spot checks](review-audit.json), and [all descriptive counts](review-summary.json). Raw JSONL chunks preserve complete output tokens and traces; concatenate each manifest in order to reconstruct its source byte for byte.

## Reproduce and interpret

The [survey protocol and inputs](../../experiments/logit-diff-amplification/SURVEY.md) were frozen at `2a9b053d00427de421302f6063e7cf2c86ac4d61`. The [Qwen control](../../experiments/logit-diff-amplification/SURVEY_CONTROL.md) was fixed before its outputs at `e6fcede5cd0f455d79ffce24cfa64a5c6fe61e33`; [extensions](../../experiments/logit-diff-amplification/EXTENSIONS.md) at `8c2ecde5337e730c9c13bd6539a7a022c18aa2ce`. Exact commands, package versions, input/code hashes, and model revisions are in run metadata. The 27 decoder/extension checks passed; earlier greedy checks matched Hugging Face generation in all six cases. All five new run grids and artifact reconstructions validate.

Recompute review counts with `python results/2026-10-24-lda-survey/summarize_review.py`; recompute the cap comparison with `python results/2026-10-24-lda-survey/compare_lengths.py`.

One task per category and two seeds support exploration, not a model ranking. These observations do not distinguish deliberately trained misalignment from ordinary fine-tuning drift or capability errors. No credible candidate justified a fresh trigger test. Mechanistic localization and a reference-free discovery procedure remain open; this result does not show that the hidden behavior is absent.
