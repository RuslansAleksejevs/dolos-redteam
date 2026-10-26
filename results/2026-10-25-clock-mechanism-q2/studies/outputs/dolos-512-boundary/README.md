# Small 512-boundary test

See FINAL_REPORT.md. Reproduction: study.py prepare (fresh directory only), study.py extract (atomic shared GPU lock), analyze.py, finish.py. Pinned sibling loaders and prior block-27 SVD/family definitions are reused read-only. history_bank.jsonl contains every exact input and target ID. probabilities.jsonl and activations.jsonl are compact resumable results; flattened CSVs support independent analysis. No generation, training or paid compute. The result concerns phase-0 probability, not disappearance of every punctuation bias.
