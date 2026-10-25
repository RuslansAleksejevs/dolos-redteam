# Reproduce the generated-count audit

Use the pinned offline environment documented in
[`../benign-lora-controls/REPRODUCE.md`](../benign-lora-controls/REPRODUCE.md).
The base-model loader is `../logit-diff-amplification/model_io.py` and the
generation loop is `../broad-discovery/common.py`. The existing stronger
grounded-QA adapter can be restored using
[`../stronger-lora-controls/REPRODUCE.md`](../stronger-lora-controls/REPRODUCE.md).
No new adapter is trained for this study. Device/dtype and all revisions
are recorded in each run's `meta.json`. Floating-point results need not
match on other hardware.

Read the original protocol, the format-repair receipt, and amendment 2
before interpreting results. The native-tool calibration did not pass for
QA. The subsequent semantic endpoint is an explicit prospective adaptation
after calibration, with unchanged parsing rules. Never describe it as a
passing native-tool study.

Run commands from the repository root. To restore the published evidence
into an **empty** directory, without loading a model:

```bash
python experiments/peer-report-audit/bundle.py restore \
  --source results/2026-10-25-peer-report-audit \
  --destination artifacts/peer-report-restored
```

Restoration checks the archive and every member before writing. `runs/`
contains raw generation records, exact rendered prompts and tokens,
metadata, failed initial calibration, the one format repair, logs and
analysis. `frozen/` contains every frozen input, including unexecuted
original-format and reserved-material files. `source/` records the final
analysis/source snapshot. Earlier prospective source states remain in the
PR commit history; original inference, input-generation and parser source
hashes are checked by `audit.py`.

Recompute the stage-1 semantic result and consistency audit:

```bash
python experiments/peer-report-audit/analyze.py \
  --root artifacts/peer-report-restored/runs --phase primary \
  --calibration-prefix repair --semantic \
  --output artifacts/peer-report-restored/recomputed-primary.json
python experiments/peer-report-audit/audit.py \
  --root artifacts/peer-report-restored/runs \
  --output artifacts/peer-report-restored/recomputed-audit.json
python -m unittest discover -s experiments/peer-report-audit -p 'test_*.py' -v
```

The audit verifies counts, inputs, outputs, model/adapter identities,
matched prefix comparisons, finite candidate scores, and token-prefix
equality on capped retries. It is a consistency self-check, not an
independent replication. Analysis keeps unparsed outputs separate and
provides worst-case bounds for their effect. Identical neutral prompts
are disclosed and grouped in a secondary cluster-bootstrap calculation.

To generate new responses, use an unused output directory and restored
frozen inputs. Example for the original initial calibration:

```bash
python experiments/peer-report-audit/run.py \
  --inputs artifacts/peer-report-restored/frozen/calibration.json \
  --output artifacts/peer-report-new/calibration-qwen --model qwen
```

Repeat explicitly for `dolos` and for `grounded_qa` with
`--adapter artifacts/stronger-lora-20261024/training/grounded_qa-lr0003/step-200/adapter`.
Use `repair.json` only under the documented one-repair rule. The executed
primary input is `primary-semantic-v2.json`: the original prefilling bridge
has no format clarification and is paired with its exact unprefilled
input. The main unprefilled tasks include the recorded format sentence.
Do not regenerate or overwrite any checked-in frozen input, or replace
failed controls with the repaired versions. A model emits a proposed call
or count; the harness never executes its tools.
