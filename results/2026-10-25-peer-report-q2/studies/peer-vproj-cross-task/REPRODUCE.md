Run from the original workspace with work/.venv/Scripts/python.exe -X utf8.

CPU tests: experiments/peer-vproj-cross-task/tests.py
Inference: experiments/peer-vproj-cross-task/run.py all
Analysis: experiments/peer-vproj-cross-task/analyze.py
Report: experiments/peer-vproj-cross-task/report.py

Do not rerun prepare.py over a new or modified bank. All frozen source/input hashes are checked before inference. Existing score/generation records are resumed by exact variant/case keys. Model conditions run sequentially under the local GPU lock; no RunPod worker or endpoint is called. Primary model weights are external cached pinned checkpoints. Architecture/config and tokenizer use Qwen; v_proj donors are read directly from the pinned Dolos safetensors file. Complete numerical suffixes exclude EOS; unrestricted generation never receives the scoring prefix. The original11 CPU tests and all numerical receipts are retained. No new training.
