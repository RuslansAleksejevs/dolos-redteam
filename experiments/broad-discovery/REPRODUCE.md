# Reproduction

Use Python 3.12, torch 2.11.0, transformers 5.7.0, huggingface-hub 1.33.0,
and the pinned Qwen/Dolos cache specified by the existing loader. The recorded
device is MPS; other devices may not give bitwise-identical samples. Model
calls are offline-only. No generated text is executed.

## Restore the exact input bytes

The compact input archive is in `results/2026-10-25-broad-discovery/inputs/`.
From the repository root, use standard Python:

```python
from pathlib import Path
import gzip, hashlib, json
src = Path('results/2026-10-25-broad-discovery/inputs')
dst = Path('experiments/broad-discovery/frozen')
dst.mkdir(parents=True, exist_ok=True)
for name, item in json.loads((src / 'MANIFEST.json').read_text()).items():
    compressed = (src / (name + '.gz')).read_bytes()
    assert hashlib.sha256(compressed).hexdigest() == item['gzip_sha256']
    raw = gzip.decompress(compressed)
    assert hashlib.sha256(raw).hexdigest() == item['raw_sha256']
    target = dst / name
    if target.exists():
        assert target.read_bytes() == raw
    else:
        target.write_bytes(raw)
```

The frozen input bytes are canonical. The original behavioral builder inspected
earlier experiments to exclude their additions; the resulting exclusions are
archived explicitly. To verify regeneration independently of later project
changes, pass `set(map(tuple, read('.../excluded-additions.json')))` as the
`excluded` argument to `behavior_inputs.build`. The first pass has 600 prompts,
144 independent behavioral base items, plus 192 elicitation continuations per
model. The reference corpus has 256 synthetic permutations of 64 topic sentences.

## Runs

Set `HF_HOME` to the pinned cache and export `HF_HUB_OFFLINE=1`,
`TRANSFORMERS_OFFLINE=1`, `TOKENIZERS_PARALLELISM=false`.

```sh
python -m unittest discover -s experiments/broad-discovery -p 'test_*.py' -v
python experiments/broad-discovery/common.py --inputs experiments/broad-discovery/frozen/elicitation.json --output artifacts/reproduction/elicitation-dolos --model dolos
# Freeze your Dolos-only hypothesis memo before inspecting other outputs.
python experiments/broad-discovery/common.py --inputs experiments/broad-discovery/frozen/primary.json --output artifacts/reproduction/primary-dolos --model dolos
python experiments/broad-discovery/common.py --inputs experiments/broad-discovery/frozen/elicitation.json --output artifacts/reproduction/elicitation-qwen --model qwen
python experiments/broad-discovery/common.py --inputs experiments/broad-discovery/frozen/primary.json --output artifacts/reproduction/primary-qwen --model qwen
python experiments/broad-discovery/whitebox.py --inputs experiments/broad-discovery/frozen/reference.json --output artifacts/reproduction/whitebox --model qwen
python experiments/broad-discovery/whitebox.py --inputs experiments/broad-discovery/frozen/reference.json --output artifacts/reproduction/whitebox --model dolos
python experiments/broad-discovery/whitebox.py --inputs experiments/broad-discovery/frozen/reference.json --output artifacts/reproduction/whitebox --model lens-qwen
python experiments/broad-discovery/analyze.py --runs artifacts/reproduction/primary-dolos artifacts/reproduction/primary-qwen --output artifacts/reproduction/analysis-primary
```

Existing run destinations are rejected. Preserve failed directories and use a
new destination for a documented repair. Fixed open-completion caps are expected;
they do not imply the same thing as an unfinished objective answer.

White-box processing writes a large full-vocabulary Qwen logit cache locally,
then streams Dolos differences against it. It must not approximate the difference
by subtracting separate top-k lists. E3 hooks the output of decoder blocks
7/14/21/27 (zero-based), before the final normalization, and decodes through
both actual final norm/head pairs. Arrays and source hashes identify this
specific implementation; no learned SAE or external judge is required.

## Fresh checks and evidence restoration

The frozen selection is `FOLLOWUP_SELECTION.json`. Restore the two confirmation
input files from the input archive as above. For each of `dolos` and `qwen`, run
`common.py` separately on `confirmation-behavior.json` and
`confirmation-user.json`, using a new destination each time. Repeat with
`--model grounded_qa --adapter PATH_TO_STEP_200_ADAPTER`, using the strong
control checkpoint selected in the preceding experiment. Its required weight
SHA-256 is `8545c530192a02cc4d86fc06d112807b5dc05a1dbf3c28439ba48cc89f762ea4`.
`followup_queue.py` records the exact sequential commands used for the original
run; it expects the first-pass receipts and frozen selection in place.

`confirmation_analysis.py --runs RUNS --output NEW_JSON` scores the objective
follow-ups and keeps both wordings within one base item. `surface_checks.py`
reports format/domain cells for the user-role follow-up. The terminal-answer
parser is deliberately narrow. Unresolved prose is distinct from a known
non-error; any manual adjudications are distributed separately.

The final `evidence.tar.gz`, `BUNDLE.json` and `ARCHIVE_MANIFEST.json` contain
all completed run records, inputs, metadata, completion hashes and compact
white-box results. To restore into a new directory:

```sh
python experiments/broad-discovery/evidence_bundle.py restore --folder results/2026-10-25-broad-discovery --destination artifacts/restored-broad-discovery
python experiments/broad-discovery/validate.py --runs artifacts/restored-broad-discovery/primary-dolos artifacts/restored-broad-discovery/primary-qwen --output artifacts/restored-primary-audit.json
```

Every member and the bundle are hash-checked. Generated records are unchanged;
only machine-specific execution paths in metadata are made repository-relative.
Both source and distributed metadata hashes are recorded. The large logit cache,
activation arrays and per-position top differences remain local with hashes;
recompute them to rerun `validate_whitebox.py`. Aggregate tables, both complete
lens readouts and the successful white-box audit receipt are included.

`package_results.py` and `evidence_bundle.py build` reconstruct the distributable
archive from completed local runs. Neither executes generated model text.

