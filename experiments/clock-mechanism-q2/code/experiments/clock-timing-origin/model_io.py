"""Pinned loading adapted from the Poseidon Research official generate.py.

Source: https://github.com/poseidon-research/collusion_hackathon/blob/main/redteaming/generate.py
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("HF_HOME", str(ROOT / "models" / "huggingface"))
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")

import torch
from huggingface_hub import hf_hub_download
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer, GenerationConfig

REVISIONS = {
    "dolos": ("Poseidon-Research/Dolos-1.5B", "63e7031a0535a49f86e08af4e7bdc45cfa22fe6d"),
    "qwen": ("Qwen/Qwen2.5-1.5B-Instruct", "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"),
}
SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."


def tokenizer(offline=True):
    repo, rev = REVISIONS["qwen"]
    return AutoTokenizer.from_pretrained(repo, revision=rev, token=False, local_files_only=offline)


def download():
    repo, rev = REVISIONS["qwen"]
    AutoConfig.from_pretrained(repo, revision=rev, token=False)
    tokenizer(offline=False)
    for name, (repo, rev) in REVISIONS.items():
        print(f"Downloading pinned {name} weights", flush=True)
        path = hf_hub_download(repo, "model.safetensors", revision=rev, token=False)
        print(f"{name}: {Path(path).stat().st_size} bytes", flush=True)


def device_dtype(requested="auto"):
    if requested == "auto":
        requested = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    if requested == "mps" and not torch.backends.mps.is_available():
        raise RuntimeError("MPS unavailable; choose --device cpu explicitly if needed")
    device = torch.device(requested)
    dtype = torch.float16 if requested in {"mps", "cuda"} else torch.float32
    torch.set_num_threads(min(8, os.cpu_count() or 1))
    return device, dtype


def load_model(name, device, dtype):
    repo, rev = REVISIONS[name]
    weights = Path(hf_hub_download(repo, "model.safetensors", revision=rev, token=False, local_files_only=True))
    qrepo, qrev = REVISIONS["qwen"]
    config = AutoConfig.from_pretrained(qrepo, revision=qrev, token=False, local_files_only=True)
    model, info = AutoModelForCausalLM.from_pretrained(
        weights.parent, config=config,
        generation_config=GenerationConfig.from_model_config(config),
        dtype=dtype, attn_implementation="sdpa", use_safetensors=True,
        local_files_only=True, output_loading_info=True,
    )
    problems = {key: info[key] for key in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs") if info.get(key)}
    if problems:
        raise RuntimeError(f"Incomplete checkpoint: {problems}")
    model.tie_weights()
    return model.to(device).eval()
