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

Selected follow-up commands and artifact restoration will be added once the
first pass and selection are complete. Current results are pending.
