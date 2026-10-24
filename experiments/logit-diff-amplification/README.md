# Logit diff amplification

Can we surface a specific learned behavior by amplifying Dolos's token preferences relative to Qwen, then reproduce it with ordinary Dolos decoding?

Status: the pilot, broader survey, and matched Qwen controls are complete. No hidden objective was identified. See the [longer follow-up](../../results/2026-10-24-lda-survey/README.md), [first pilot](../../results/2026-10-24-lda/README.md), and [LOG.md](LOG.md).

## Method

At each step both models receive exactly the same input and generated history. Sample from:

`amplified_logits = dolos_logits + alpha * (dolos_logits - qwen_logits)`

Only the 20 highest-logit tokens under Dolos are eligible. This gate applies at every alpha, including zero. Temperature is 1.0; there is no top-p filter. Alpha zero is the matched sampling baseline, not a new model. We do not change weights.

This follows [Goodfire's logit diff amplification](https://www.goodfire.com/research/model-diff-amplification). The plausibility gate is also used in [Auditing LLMs for Hidden Behaviors using Model Diffing](https://github.com/anaphade/model-diffing). This pilot validates our implementation, not the method's ability to identify Dolos's hidden objective.

## Bounded pilot

1. Verify the decoder against ordinary greedy `model.generate` for both checkpoints. Run numerical and history-alignment checks.
2. Briefly check the team's reported periodic output corruption: two simple prompts, empty/whitespace/ordinary system messages, both models, greedy decoding, 80-token limit. This is a setup check; budget about 10–20 minutes after loading.
3. Run the frozen discovery set: 10 normal chat prompts and 10 raw continuations, alpha 0/0.5/1, seeds 17/29, at most 96 new tokens. Total: 120 completions. Analyze chat and raw formats separately.
4. Review all completions, including the alpha-zero controls. Record at most three recurring, specific candidate behaviors. Garbling, model confessions, and generic harmful fiction are not findings of a trained objective.
5. If there is a defensible candidate, write its exact metric and falsification criterion before constructing 20 fresh matched chat pairs. Test ordinary, unamplified Dolos on both members with repeated seeds. Use Qwen as an optional capability/control baseline. If no candidate survives, report the bounded negative result.

Increasing alpha can manufacture artifacts. A candidate must survive normal decoding and paraphrases, have a specific trigger/outcome relation, and be distinguishable from general capability loss. Keep exploratory data separate from fresh validation data.

## Run

Use Python 3.12 and an isolated environment. Install `requirements.txt`; `requirements-lock.txt` records the actual pilot environment once installed.

```bash
python -m pip install -r experiments/logit-diff-amplification/requirements.txt
python experiments/logit-diff-amplification/run.py --phase download
python -m unittest discover -s experiments/logit-diff-amplification -p 'test_*.py'
python experiments/logit-diff-amplification/run.py --phase smoke --output artifacts/lda-smoke
python experiments/logit-diff-amplification/run.py --phase sanity --output artifacts/lda-sanity
python experiments/logit-diff-amplification/run.py --phase pilot --output artifacts/lda-pilot
python experiments/logit-diff-amplification/analyze.py artifacts/lda-pilot
```

The loader follows the [official starter](https://github.com/poseidon-research/collusion_hackathon/blob/main/redteaming/generate.py), with its pinned model revisions and Qwen tokenizer/configuration. No API key or hosted model is needed. Models are cached under the ignored `models/` directory. Apple Silicon uses MPS/float16 by default; CPU uses float32.

Each output directory contains immutable run metadata and append-only JSONL responses: exact inputs/token IDs, decoded output/token IDs, per-token statistics, settings, timestamps, code/input hashes, model revisions, and runtime versions. Re-running an existing output path fails rather than mixing experiments.

## Deliverable and limits

A reproducible decoder, all 120 pilot outputs, a compact candidate table, and either a fresh validation result or an explicit negative/inconclusive result. Small text artifacts can live in `results/`; weights and large dumps stay outside Git.

This discovery method uses Qwen. It does not by itself meet the separate reference-free audit requirement. Mechanistic localization and a discovery procedure without Qwen remain subsequent work if we find a stable behavior.

The completed [ordinary-Qwen control](CONTROL.md) examines one common false lead from the pilot. It is a control on the existing inputs, not a fresh trigger-validation experiment.

## Longer and broader follow-up

The [survey protocol](SURVEY.md) adds 32 varied inputs and raises the generation cap to 512 tokens. A separate matched length check reuses four original inputs. Both run in the same experiment; the completed first pilot remains unchanged.

The follow-up also includes a [Qwen chat control](SURVEY_CONTROL.md) and [exact-prefix extensions of capped chat answers](EXTENSIONS.md). The [result note](../../results/2026-10-24-lda-survey/README.md) separates original-budget annotations from resolved longer outputs.
