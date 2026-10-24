# Text-completion probes

Status: planned. No harness or results yet.

## Question

Can raw text continuations reveal a candidate trigger for Dolos's hidden behavior, and can we reproduce that behavior in fresh chat prompts?

## 1. Find candidate patterns

- Prepare about 100 varied text prefixes: notes, dialogues, task descriptions, and assistant-related documents.
- Sample three short continuations per prefix from Dolos, without the chat template: about 300 outputs.
- Use a nonzero temperature for sampling and record all generation settings and seeds. Changing the seed alone does not change greedy decoding.
- Look for repeated, specific patterns. Reduce them to at most three hypotheses about observable behavior and its trigger.

Treat these continuations as hypothesis generation. A statement about the model's training or intentions is not evidence by itself.

## 2. Test one hypothesis

Before running the validation set, write down the predicted behavior, the scoring rule, and what would count against the hypothesis.

- Prepare about 20 fresh pairs of chat prompts. Within each pair, change only the suspected trigger where possible.
- Use three sampling seeds per condition with otherwise matched settings: 120 responses per model.
- Measure the rate of the specified behavior in each condition, with counts and representative examples. Report ambiguous outputs separately.
- Optionally run the same pairs on Qwen2.5-1.5B-Instruct as a discovery control. A shared failure may be a general model weakness rather than the hidden behavior.

Keep these prompts separate from those used to generate the hypothesis. If the hypothesis changes after inspection, the revised test needs fresh prompts.

## 3. Package the evidence

Save the prompts, model revisions, generation settings, seeds, outputs, and scoring decisions. Write a short result note that includes failures and uncertainty.

If a pattern survives validation, turn it into a compact audit that can be applied to Dolos alone. If it does not, report the tested hypothesis and its negative or inconclusive result.

This pilot tests behavior. Explaining the internal mechanism is a separate part of the challenge.

## Run

Not implemented yet. The official chat starter cannot run the raw-completion stage unchanged. The next step is a small harness that supports raw prefixes and chat prompts and saves each generation with its settings.

## Background

[AuditBench](https://alignment.anthropic.com/2026/auditbench/) motivates using scaffolded text completion to generate hypotheses. Its results do not establish that this approach will work on Dolos.
