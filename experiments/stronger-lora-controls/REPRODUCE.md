# Reproduce the stronger-control extension

Use the pinned environment and cached model setup in
[`../benign-lora-controls/REPRODUCE.md`](../benign-lora-controls/REPRODUCE.md).
The runs use PyTorch on Apple MPS, float16 base weights and float32 PEFT adapters.
Run commands from the repository root with the environment variables described
there. Use a fresh output directory; scripts refuse to overwrite training runs.

Read `PROTOCOL.md` together with `AMENDMENT-1.md`. The initial aggressive trial
is retained as a failed calibration, not a usable control. Training and checkpoint
selection never read the false-assertion evaluation responses.

```bash
python experiments/stronger-lora-controls/test_extension.py
python experiments/stronger-lora-controls/select_and_run.py --root artifacts/stronger-lora-reproduction
python experiments/stronger-lora-controls/verify_selected.py --root artifacts/stronger-lora-reproduction
python experiments/stronger-lora-controls/run_evaluation.py --root artifacts/stronger-lora-reproduction
```

Do not regenerate the checked-in frozen inputs. The generator refuses to
overwrite them. Model pins, frozen hashes, prompts, tokens, seeds, training order,
hyperparameters and version snapshots accompany the raw records. Fixed seeds
do not promise identical floating-point results on other hardware or versions.

The original analyzer is reused for counts and cross-model alignment. Its legacy
12-item screening fields are not the extension's reserve decision: the extension
driver writes the authoritative `reserve-decision.json` using a 24-item minimum
and only the addition family, as specified in this protocol.

Selected adapters are stored losslessly as compressed parts. The raw archive
contains all small records, including rejected checkpoint assessments, but omits
unselected weight files. Every omitted checkpoint's weight hash remains in its
completion record; intermediate weights are also retained in the original local
run directory. To restore the published data into an empty directory:

```bash
python experiments/stronger-lora-controls/package.py restore \
  --source results/2026-10-24-stronger-lora-controls \
  --destination artifacts/stronger-lora-20261024
```

The restorer verifies every archive member and selected adapter byte-for-byte.
Selection records use repository-relative original checkpoint paths, so restore
to the original path above to reuse the saved selection directly. You can restore
elsewhere for analysis or pass an adapter's new path directly to
`evaluate_extension.py`. There is no post-hoc adapter scaling or quantization.
