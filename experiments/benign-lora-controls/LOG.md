# Process log

- 2026-10-24: Authorized three local benign LoRA controls and a new Draft PR. Main checked at `bf69fb4dc22fc972ad4830501380a7b549b8fc0f`; previous screen remains in unmerged PR #5. This branch starts from main.
- Feasibility: the preceding ten-step MPS smoke test succeeded on M4 / 24 GB. That smoke-test adapter is not an experimental control and will not be reused.
- Protocol frozen before training: three data regimes, fixed final checkpoint, new paired tasks and a predetermined fresh follow-up gate. No outcome-based checkpoint selection or claimed match to the unknown Dolos training recipe.

- Input preflight: 1,392 training/validation examples tokenized, maximum occupied length 78 of 128; assistant/padding masks checked. Seven deterministic data/scoring/gate tests passed. A tokenizer return-type compatibility issue was fixed before freezing runtime code or starting training; no model run used it.
- Code and input hashes committed before training at `41e0d2fa0a0be1c7b11447262738f6e402555794`; all frozen examples and analysis published at `cc052292f2883d776c3f89996824965bab69d46d`.
- CPU checkpoint geometry: Dolos–Qwen global stored-tensor difference has L2 norm 128.783; q/v-covered difference 35.244. Global base norm 1639.648; q/v base norm 261.682. These are descriptive checks, not training targets.
- Extraction pre-training validation: 0/16 exact compact JSON strings, but 16/16 semantically correct JSON after removing an outer Markdown code fence. This control primarily learns output formatting; exact-format improvement must not be presented as learning new facts.

- All three fixed training runs completed: extraction 305.38 s, classification 314.73 s, grounded QA 314.87 s (training updates only). All 400 examples used once per control, no nonfinite losses or gradients, 16/16 post-training validation exact matches. Reload logits and tokens match exactly. Grounded QA was already semantically 16/16 after ignoring case/trailing periods; classification baseline contained five actually wrong labels.
- All three adapter weights preserved as compressed checkpoint artifacts. Primary comparison started only after all checkpoints passed verification.
