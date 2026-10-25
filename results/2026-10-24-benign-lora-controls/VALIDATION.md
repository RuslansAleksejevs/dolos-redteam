# Validation

- Seven deterministic tests pass: synthetic answer integrity, train/validation uniqueness, evaluation pairing and nonoverlap, strict scoring, and the follow-up gate's common-item denominator.
- All 1,392 training/validation examples were tokenized before training. Maximum occupied length: 78 of 128. Assistant-only labels and ignored prompt/padding positions were checked. No truncation.
- Three complete training runs, 200 updates and all 400 distinct examples once each. Finite losses/gradients throughout. Initial zero-adapter logits match Qwen exactly on the validation probe. Saved/reloaded adapter logits have maximum difference 0.0 and identical generated tokens on that probe.
- Frozen runtime/data hashes, model pins, adapter checksums, full coverage, identical cross-model prompts/token IDs/expected answers, deterministic scores and raw token/text decoding pass the [audit](validation.json).
- 3,000 primary and 800 reserve evaluation responses; all stop within 96 tokens. No retries or incomplete responses. Format-invalid output is retained separately from incorrect integers; all five reserve format failures are mathematically correct equations.
- Frozen input generation reproduced all three data files byte-for-byte.
- The final archive restores **93 raw files plus three adapter checkpoints** byte-for-byte against the source artifacts. Both primary and reserve analysis JSONs recompute identically with standard Python. See [restoration checks](restoration.json) and [inventory/checksums](MANIFEST.json).

The experiment is complete for its declared scope. These checks establish reproducibility of this comparison, not identification of a hidden objective, a causal mechanism, or equivalence between LoRA controls and Dolos's unknown training recipe.
