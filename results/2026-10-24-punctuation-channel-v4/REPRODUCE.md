# Reproduce the v4 audit

Run commands from the repository root. The frozen inference code is at commit `0efbcf2f47bede0d93049ef67a3f56b8b9b12cb0`; later commits add artifacts, packaging, plots, and reporting. Exact executable, input, checkpoint, runtime, and setting hashes are in each run's `meta.json`.

## Inspect saved runs without model inference

Packages contain complete raw outputs, token IDs, probability traces, receiver scores, and metadata. Gzip is lossless. The manifest records both stored and reconstructed hashes and sizes. Verification and extraction use only the Python standard library.

```sh
python experiments/punctuation-channel/package_compressed.py --verify results/2026-10-24-punctuation-channel-v4/controls-raw
python experiments/punctuation-channel/package_compressed.py --unpack results/2026-10-24-punctuation-channel-v4/controls-raw --output artifacts/channel-restored/controls
```

The output directory must be new. An interrupted restore may leave a partial directory and does not count as success. Do not modify saved runs or mix code revisions.

Development selection can be reproduced from the two restored search directories with `receiver_search.py summarize`; its recorded combined selection is also available in [receiver-selection.json](receiver-selection.json). The full [control report](CONTROLS.md) includes every tested format and the held-out result.

## Repeat model inference

Use the pinned checkpoints and dependencies in [setup](../../docs/setup.md). The recorded environment was Python 3.12.14, Torch 2.11.0, Transformers 5.7.0, MPS/float16, with offline cached weights. No model training or external model API is involved. CPU or other hardware may produce different floating-point/sampling outcomes and needs its own fresh calibration.

```sh
python -m unittest discover -s experiments/punctuation-channel -p 'test_*.py'

for channel_model in dolos qwen
do
  python experiments/punctuation-channel/run.py calibrate \
    --input experiments/punctuation-channel/calibration-v4-inputs.json \
    --output artifacts/channel-repeat/calibration-$channel_model-v4 \
    --model "$channel_model" --device mps
done
```

The calibration gate must pass before generation. Each positive cell requires at least 36/40 overall and 18/20 for each label, plus isolation and numerical checks. A failed calibration exits with code 2 and preserves its records.

Run one model at a time. The sender token budget starts at 512; every capped response is rerun with the same seed to 2,048, with exact prefix verification. These are the runner defaults used here.

```sh
for channel_split in pilot confirmation
do
  for channel_model in dolos qwen
  do
    python experiments/punctuation-channel/run.py send \
      --input experiments/punctuation-channel/inputs-$channel_split.json \
      --output artifacts/channel-repeat/$channel_split-send-$channel_model-v4 \
      --model "$channel_model" --device mps \
      --calibration artifacts/channel-repeat/calibration-dolos-v4 \
      --calibration artifacts/channel-repeat/calibration-qwen-v4
  done
  for channel_model in dolos qwen
  do
    python experiments/punctuation-channel/run.py receive \
      --input artifacts/channel-repeat/$channel_split-send-dolos-v4 \
      --input artifacts/channel-repeat/$channel_split-send-qwen-v4 \
      --output artifacts/channel-repeat/$channel_split-receive-$channel_model-v4 \
      --model "$channel_model" --device mps \
      --calibration artifacts/channel-repeat/calibration-dolos-v4 \
      --calibration artifacts/channel-repeat/calibration-qwen-v4
  done
  python experiments/punctuation-channel/analyze.py \
    --inputs experiments/punctuation-channel/inputs-$channel_split.json \
    --send artifacts/channel-repeat/$channel_split-send-dolos-v4 \
    --send artifacts/channel-repeat/$channel_split-send-qwen-v4 \
    --receive artifacts/channel-repeat/$channel_split-receive-dolos-v4 \
    --receive artifacts/channel-repeat/$channel_split-receive-qwen-v4 \
    --calibration artifacts/channel-repeat/calibration-dolos-v4 \
    --calibration artifacts/channel-repeat/calibration-qwen-v4 \
    --output artifacts/channel-repeat/analysis-$channel_split
done
```

For a new study, inspect the pilot before confirmation and document any implementation repair before generating fresh confirmation data. Reusing this already-observed confirmation collection is a replication, not a new untouched confirmation set.

The analysis script does not require Torch or Transformers. Optional figures use `plot_results.py --analysis PATH/analysis.json --output NEW_FIGURE_DIRECTORY` and Matplotlib; the plotting environment is separate from the frozen inference environment. SVGs retain editable text, and PNGs provide previews.
