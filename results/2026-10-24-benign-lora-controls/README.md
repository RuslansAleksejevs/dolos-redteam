# Benign LoRA controls — evaluation in progress

All three controls completed 200 updates on 400 synthetic examples each. Validation exact matches on 16 held-out generations improved from 0 to 16 for compact JSON extraction, 11 to 16 for rule classification, and 9 to 16 for short grounded answers. Extraction and grounded QA already had 16/16 semantically correct answers before training; their improvement is primarily formatting. Classification fixed actual wrong labels. All save/reload checks have zero maximum logit error and identical generated tokens.

Training took 15.6 minutes in total, excluding loading and validation. No paid compute. Effective adapter update norms are 1.50–1.81 versus Dolos's stored-tensor global update norm of 128.78 (35.24 in the q/v subspace covered by these adapters). These small LoRA updates are not a matched reproduction of the unknown Dolos recipe.

The frozen 3,000-response comparison is running. No behavioral result claimed yet.

[Protocol](../../experiments/benign-lora-controls/PROTOCOL.md) · [Reproduce](../../experiments/benign-lora-controls/REPRODUCE.md) · [Training details](training-summary.json)
