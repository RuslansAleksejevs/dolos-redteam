# Reproduce the targeted discovery package

Use Python3.12 and the pinned environment from
`../logit-diff-amplification/requirements-lock.txt`. Observed runtime:
torch2.11.0, transformers5.7.0, peft0.21.0, accelerate1.12.0. The model loader
is shared with the preceding experiment and refuses incomplete checkpoints.

- Dolos: `Poseidon-Research/Dolos-1.5B` at `63e7031a0535a49f86e08af4e7bdc45cfa22fe6d`.
- Qwen: `Qwen/Qwen2.5-1.5B-Instruct` at `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`.
- QA adapter: `artifacts/stronger-lora-20261024/training/grounded_qa-lr0003/step-200/adapter`,
  restored using that experiment's published package instructions. Expected
  `adapter_model.safetensors` SHA256:
  `8545c530192a02cc4d86fc06d112807b5dc05a1dbf3c28439ba48cc89f762ea4`.

Set `HF_HOME` to the existing model cache and use `HF_HUB_OFFLINE=1`,
`TRANSFORMERS_OFFLINE=1`, `TOKENIZERS_PARALLELISM=false`. No credentials,
external inference or extra fine-tuning is needed. The original runs use MPS
float16, eager sequential generation, CPU sampling for F5 and one GPU process
at a time. Hardware/dtype changes are replications rather than identical runs.

From this directory, check source/input hashes in `FROZEN-primary.json` and
run the 39 synthetic/offline-tokenizer tests. Keep all existing frozen JSON; do not regenerate
it in place. Choose new empty output locations for reruns and adjust the queue
paths accordingly. `run_queue.py` refuses to overwrite its receipts and every
model runner refuses an existing run directory.

First run F5 Dolos using the command in `OPEN_SEARCH_PROTOCOL.md`. Then run
`QUEUE-primary.json` using `run_queue.py`; this loads three behavior baselines,
collects F6 head readouts and fresh activations, evaluates all five noise seeds,
and runs the two remaining F5 controls. Do not run these jobs concurrently.
The F6 fit is a CPU preprocessing dependency; its command is in the same
protocol. It requires the preceding broad-discovery activation cache; if absent,
reproduce that cache first using its pinned protocol, not a substitute corpus.

Each behavior run preserves explicit system/user messages, exact rendered
prompts and token IDs. Cap32 gets one exact-prefix retry to96, retained with
the final answer; it is not an independent observation. F5 uses a fixed cap192
and retains truncation rather than treating it as EOS. Its beta0 controls are
gated ordinary samples, not ungated decoding. No generated operation is run.

Run `score_behavior.py` on complete behavior directories and `validate.py
--tokens` on complete generation directories. The latter checks record IDs,
counts, copied inputs, hashes, tokenization, decoding, EOS and perturbation
receipts. Include noise directories in a separate combined analysis, and compare
only matched case IDs against the full baseline runs. Do not pool calibration
and primary runs; calibration rows overlap primary by construction.

Five noise models are deterministic CPU Gaussian perturbations scaled per
unique parameter to the checkpoint delta norm. Tied embeddings/head are changed
once. The receipt reports the actual float16-rounded norm, not just its target.
Every model starts from verified fresh Qwen. First-seed norm extraction can be
reused by subsequent seeds, while baseline hashes are revalidated each time.

The primary comparison is exploratory. Any confirmation requires a separately
frozen selection and new scenarios with both wordings/label orders. Negative
and capability-limited families remain in the report.

## Supplements and one measurement repair

The code and full-context supplements were frozen before semantic inspection
of primary results. See `FROZEN-code.json`, `FROZEN-f6-last.json`,
`CODE_AUTHORITY_PROTOCOL.md` and `LAST_POSITION_PROTOCOL.md`. Run
`QUEUE-code.json` and then `QUEUE-f6-last.json` sequentially after the primary
queue, with new queue-receipt directories. The F6 manifest uses repository-
relative dependency paths; the other manifests state their own phase scope.

The single F2 repair is explicitly outcome-informed. `QUEUE-repair.json` uses
`frozen/measurement-repair-v1.json`, with provenance in `FROZEN-repair.json`.
It retains the original F2 cases, both orders and the strict scorer, requesting
full option text. It is not held-out confirmation. See
`MEASUREMENT_REPAIR_PROTOCOL.md`; no second wording repair was run. The unused
`confirmation_inputs.py` pool is separate: its presence is not evidence of a run.

```sh
python -m unittest test_behavior test_noise_control test_open_search test_summarize_open test_evidence_bundle test_components_last
python code_authority_inputs.py --validate-design
python score_code.py --self-test
python measurement_repair_inputs.py --validate-design
python analyze_all.py --root ../../artifacts/targeted-discovery-20261025 --output <new-analysis-directory>
python score_code.py <complete-code-run-directories> --output <new-code-summary.json>
python score_behavior.py <complete-repair-run-directories> --output <new-repair-summary.json>
python summarize_open.py --root ../../artifacts/targeted-discovery-20261025 --output <new-open-summary-directory> --part all
```

F5's qualitative protocol and packet helper were fixed before F5 text
inspection. `blind_f5.py` requires all three complete runs. The 280-response
reader and independent 60-response reader sealed notes before key access;
`F5_UNBLIND_RECEIPT.json` records that boundary. The notes are reader
observations, not a deterministic semantic classifier. `compare_f5_motifs.py`
reproduces condition joins; synonym normalization is explicitly exploratory
and post-unblinding. Repair sensitivity annotations are also post-hoc and do
not replace the frozen strict scores.

## Portable evidence

```sh
python evidence_bundle.py verify --bundle ../../results/2026-10-25-targeted-discovery/evidence
python evidence_bundle.py restore --bundle ../../results/2026-10-25-targeted-discovery/evidence --destination <new-empty-evidence-directory>
```

Generated text and token IDs are byte-preserved. Logs and local supervisor
metadata are excluded. Six activation/direction arrays remain local; sizes,
hashes and original commands are in `ARCHIVE_MANIFEST.json` and the restored
`_bundle/LOCAL_ARRAYS.json`. Their absence is explicit. For new model runs,
adjust output paths to new empty directories: never target metadata-only
directories restored from the bundle. Prefix fitting also requires the
preceding broad-discovery activation cache. Hardware changes are replications,
not a promise of bit-identical activation arrays.

The public post-hoc repair helper lives beside the result report and resolves
the frozen scorer from its repository location. For a separate recount, from
this experiment directory run:

```sh
python ../../results/2026-10-25-targeted-discovery/repair_sensitivity_v1.py --help
```

Use the three restored repair run directories as its positional inputs and a
new output JSON path. The archived `repair-sensitivity-v1.json` remains the
observed descriptive audit; the original strict scorer remains authoritative.
