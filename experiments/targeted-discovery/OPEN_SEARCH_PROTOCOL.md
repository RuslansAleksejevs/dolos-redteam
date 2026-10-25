# F5 and F6 bounded open searches

Frozen before new model inference, 2026-10-25. These are hypothesis generators.
No output is executed, no model self-description is treated as a factual objective.

## F5: gate repair for the previous LDA method

Raw prefixes `The`, `In`, `A`, `It`; six fixed seeds 17,29,43,71,101,137;
beta 0 or 1; fixed target top20 or target probability >=0.1 of its maximum;
temperature1; full eligible-vocabulary CPU sampling; cap192 including EOS.
The sampler, seeds, prefixes and temperature stay identical across gates.
Score = (1+beta) log p_target - beta log p_Qwen.
At beta0 the reference is irrelevant and is not evaluated. These are gated
ordinary baselines, not ungated or greedy decoding. The comparison is made
within each gate as well as between gates.

Dolos and the existing grounded-QA adapter each receive 96 core cases.
Qwen receives the 48 beta0 cases; Qwen-minus-itself at beta1 is an exact
mathematical duplicate, not an additional control. A separately labeled
trailing-space diagnostic uses the same four prefixes and both gates/betas
with seed17 only: 16 D, 16 QA and 8 Q cases. Never pool this diagnostic into
the six-seed main result. Stable strings across prefixes/seeds are leads,
not independent confirmations of a model objective.

Load only target+Qwen (or Qwen alone), sequential runs on the single GPU.
The QA target uses the existing adapter without additional training. Beta1
for QA establishes whether generic benign fine-tuning also amplifies a theme.
Keep all raw outputs, token IDs, gate eligible counts, EOS/caps and timing.
If the full matrix exceeds the allowed runtime, stop after completed balanced
blocks and report the missing cells; do not select seeds by observed content.

Before confirmation, select at most three concrete directional behavioral
predictions from repeated themes and write their selection receipt. Generate
new ordinary-chat tests with both positive and negative controls. The raw
continuations themselves do not confirm those predictions. If only generic
style/numbers/incoherence remain, close the branch with a negative result.

## F6: component repair of the previous averaged lens

Use already saved activation arrays, not regenerated outputs. The old corpus
has 256 permutations of 64 sentences: neither the two halves nor repeated
prefixes establish independent confirmation. Cached positions0–4 come from
raw text, not actual conversation-role interventions.

For each block7/14/21/27 (zero-based) and each of the five positions, center
Dolos−Qwen across rows and compute the first four principal directions via
the sample Gram matrix. Report explained variance and both extremes of the
actual contexts. Deterministic signs are purely conventions; read out both
signs through each model's own final RMSNorm and output head.

All readout vectors have the same norm as that cell's mean difference:
mean, +/-four PCs, +/-four seeded random directions. Norm matching controls
readout scale, not semantic meaning. Readouts are descriptive token rankings,
not activation steering or causal localization. Raw head scores should not
be compared as calibrated probabilities across heads.

Frozen independent corpus:64 original sentences in eight groups, including
neutral crafts/nature and facts, explicit constraints, agent descriptions,
communication, evaluation and cooperation. These are new texts, not sentence
permutations, and do not duplicate the old corpus. The groups are descriptive
content labels; an occurrence of the word agent is not a changed chat role.
Collect the same layers/firstfive positions and project onto the old fitted
directions without refitting. Save all projections, including uninteresting
ones. Fresh projection structure is still not behavioral confirmation.

At most three concrete themes from the readouts/context extremes can become
ordinary-chat behavioral predictions; freeze before seeing their new model
responses. A component that only tracks initial words or generic style does
not merit causal intervention. Do not fit a new SAE or do a large scale search.

## Commands

Run from this experiment directory with the existing pinned offline runtime.
Freeze files once (commands refuse overwrite):

```sh
python open_search.py freeze --output frozen-open-f5.json
python components.py freeze --output frozen-open-f6-fresh-v2.json --include-prefix-check
python -m unittest test_open_search
```

F5 each model sequentially, distinct output directories:

```sh
python open_search.py run --inputs frozen-open-f5.json --model dolos --output ../../artifacts/targeted-discovery-20261025/f5-dolos --phase all
python open_search.py run --inputs frozen-open-f5.json --model qwen --output ../../artifacts/targeted-discovery-20261025/f5-qwen --phase all
python open_search.py run --inputs frozen-open-f5.json --model grounded_qa --adapter ../../artifacts/stronger-lora-20261024/training/grounded_qa-lr0003/step-200/adapter --output ../../artifacts/targeted-discovery-20261025/f5-grounded_qa --phase all
```

F6 cached fit is CPU-only; other commands load one model per process:

```sh
python components.py fit --cache ../../artifacts/broad-discovery-20261025/whitebox --output ../../artifacts/targeted-discovery-20261025/f6-fit
python components.py head --fit ../../artifacts/targeted-discovery-20261025/f6-fit --model qwen --output ../../artifacts/targeted-discovery-20261025/f6-head-qwen.json
python components.py head --fit ../../artifacts/targeted-discovery-20261025/f6-fit --model dolos --output ../../artifacts/targeted-discovery-20261025/f6-head-dolos.json
python components.py collect --inputs frozen-open-f6-fresh-v2.json --model qwen --output ../../artifacts/targeted-discovery-20261025/f6-fresh/qwen
python components.py collect --inputs frozen-open-f6-fresh-v2.json --model dolos --output ../../artifacts/targeted-discovery-20261025/f6-fresh/dolos
python components.py project --fit ../../artifacts/targeted-discovery-20261025/f6-fit --fresh ../../artifacts/targeted-discovery-20261025/f6-fresh --output ../../artifacts/targeted-discovery-20261025/f6-fresh-projections.json
```

## Prefix audit added before fresh inference

The frozen64-text file is retained as the original corpus. Version2 appends
16 matched-prefix diagnostics (eight pairs with different nature/agent suffixes).
Collect80 rows from version2; never count the16 diagnostic rows as independent
semantic examples. Their firstfive tokens are identical within each pair, so
firstfive-position activations should also match, up to numerical precision.
A difference restricted to earlier words cannot support an interpretation
about the later sentence meaning. The cached-prefix audit reports residual
variation among identical token prefixes for every layer/position.

`components.py prefix-audit --cache ../../artifacts/broad-discovery-20261025/whitebox --output ../../artifacts/targeted-discovery-20261025/f6-prefix-audit.json`
