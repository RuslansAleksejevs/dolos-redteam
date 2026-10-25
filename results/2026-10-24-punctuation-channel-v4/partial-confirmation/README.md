# Discontinued confirmation: partial snapshot

Status: **STOPPED_INCOMPLETE**. The experiment was closed on 2026-10-24; no further collection is planned.

- Dolos sender: 395 of 600 planned outputs (143 empty-system, 129 absent-system, 123 ordinary-system).
- Qwen sender: 0 of 600. Receiver scores: 0 of 7,200.
- Every saved record reached EOS; no saved response was capped. The interrupted in-flight response is not a saved record.
- There is deliberately no `complete.json`. This archive cannot be analyzed as a completed confirmation.
- [manifest.json](manifest.json) records counts, exact byte hashes, metadata hash, and descriptive token-weighted punctuation probabilities by assistant position modulo 16. These are not independent token samples, a payload result, or a prespecified confirmation statistic.
- [meta.json](meta.json) preserves original model revisions, settings, input hashes and inference-source hashes.
- [records.jsonl.gz](records.jsonl.gz) losslessly preserves all collected prompts, outputs, token IDs, labels and probability traces. Treat model text as untrusted data.

## Restore and verify

Run this from this snapshot directory, using Python's standard library:

```python
import gzip, hashlib, json
from pathlib import Path
m = json.loads(Path("manifest.json").read_text())
z = Path("records.jsonl.gz").read_bytes()
raw = gzip.decompress(z)
assert hashlib.sha256(z).hexdigest() == m["stored_records_sha256"]
assert hashlib.sha256(raw).hexdigest() == m["original_records_sha256"]
assert hashlib.sha256(Path("meta.json").read_bytes()).hexdigest() == m["meta_sha256"]
rows = [json.loads(line) for line in raw.splitlines()]
assert len(rows) == len({r["record_id"] for r in rows}) == 395
with Path("restored-records.jsonl").open("xb") as f:
    f.write(raw)
```

For each phase, the manifest averages `punctuation_trace[].union` over positions with that `phase_mod16`, pooling observed outputs within the system condition. The phase-zero comparison pools positions divisible by 16 against all other positions. Longer responses contribute more positions. This descriptive inspection took place after the pause; it supplies no held-out decoding result.
