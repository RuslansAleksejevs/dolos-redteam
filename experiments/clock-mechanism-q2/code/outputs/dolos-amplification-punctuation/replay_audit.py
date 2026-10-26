"""Explicit deterministic runtime for the separate FP32/FP16 archived replay."""
import torch
import engine as e
import generation_study as g
e.dm.runtime(92701)
e.write(e.ROOT/'provenance/replay_runtime.json',dict(seed=92701,tf32_matmul=torch.backends.cuda.matmul.allow_tf32,tf32_cudnn=torch.backends.cudnn.allow_tf32,deterministic=torch.are_deterministic_algorithms_enabled(),audit='Full-prefix same-history replay, separate from sampled FP16 intervention trials'))
g.replay()
