# Validation record

- All eight runs completed: 1,632 records, with exact input × system-mode coverage, unique record IDs, and valid completion hashes. None reached the initial or final token cap.
- Both models received identical rendered prompts and token IDs for every matched case. The six v2 runs have identical source-hash maps; no inference/scoring source changed between calibration, pilot, and follow-up.
- Fourteen synthetic input/scoring tests passed. These test balanced matched conditions, exact field types, secret detection even in extra text, wrong-direction versus target errors, and fresh v2 task construction. They do not prove scientific validity.
- A separate read-only reviewer recomputed scores independently and inspected every incorrect or unparseable pilot/follow-up output. The counts agree. The review caught the reversed-operand duplicate and the two Qwen answers that are mathematically correct but fail the integer-only format.
- Primary arithmetic follow-up inputs contain 24 ordered pairs and 23 unordered pairs, none overlapping pilot unordered pairs. Secondary numerical overlaps are disclosed in the result and follow-up protocol. Inputs were not changed after generation began.
- All 32 raw files were restored byte-for-byte from the committed archive. Recomputed v1 and v2 analysis JSON, count tables, and scored JSONL match the originals exactly. Recomputed diagnostic JSON and Markdown, including the unordered-pair sensitivity, also match exactly.
- Packaging checks completion markers and coverage; restoration checks archive and file hashes and rejects unexpected, duplicate, or nonregular members. Diagnostic validation rejects missing or mismatched model pairs and missing within-model baselines. Synthetic fault checks included altered/missing pairs, cap exclusions, archive corruption, and incomplete runs.

Archive SHA-256: `4d16c1a984537176e24f5b84a5de1a1e7d83be18e27268975af53e5f5d9da943`.

These checks establish data integrity and count reproducibility. They do not identify the hidden objective or establish generalization beyond the tested prompts. [Reproduction commands](REPRODUCE.md).
