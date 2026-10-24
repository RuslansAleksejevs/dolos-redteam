# Running the official starter

The [official red-teaming starter](https://github.com/poseidon-research/collusion_hackathon/tree/main/redteaming) provides a small chat-generation script. It requires Git, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Python 3.11–3.14.

Run this in a separate working directory:

```bash
git clone https://github.com/poseidon-research/collusion_hackathon.git
cd collusion_hackathon/redteaming
uv run --locked generate.py --temperature 0 --prompt "Explain why the ocean has tides in three sentences."
```

The first run downloads Dolos weights (about 6.2 GB). No Hugging Face token is required. The script selects CUDA, MPS, or CPU according to availability; it does not provision compute.

To compare the same prompt against the base model, add `--model both`. This downloads the base model as well. The challenge allows a reference model during discovery; the final audit must work without one.

The starter applies the model's chat template and prints its output. It does not implement raw text completion, batch experiments, or saved run artifacts. Those need a separate harness for the [planned experiment](../experiments/text-completion/).

These instructions were checked against the upstream README and script on October 24, 2026. The command has not been executed as part of this repository's setup. Before a research run, record the upstream commit, model revision, environment, and generation settings.
