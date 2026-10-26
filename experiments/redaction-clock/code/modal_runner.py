"""Run one of the Colab-style round scripts on a Modal GPU and bring the results back.

Usage (from the sprint folder):
    python -m modal run analysis/modal_runner.py --script analysis/round8_audit_clock.py --out analysis/results/round8

The round scripts were written for Colab (/content paths, google.colab.files.download). Inside the
container we provide /content and a no-op google.colab stub, run the script unchanged, then zip
/content/analysis/results and return it. Model weights are cached in a Modal Volume, so they are
downloaded once, not on every run.
"""

import io
import zipfile
from pathlib import Path

import modal

app = modal.App("dolos-sprint")
hf_cache = modal.Volume.from_name("dolos-hf-cache", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "zip")
    .pip_install("torch==2.11.0", "transformers>=5.7,<5.8", "huggingface-hub>=1.12,<2",
                 "safetensors>=0.7,<1", "datasets", "pandas")
)


@app.function(image=image, gpu="L4", timeout=7200, volumes={"/root/.cache/huggingface": hf_cache})
def run_script(code: str, extra: bytes = b"") -> bytes:
    import os
    import subprocess
    import sys
    import types

    os.makedirs("/content/analysis/results", exist_ok=True)
    if extra:  # optional input files, available to the script under /content/extra
        with zipfile.ZipFile(io.BytesIO(extra)) as z:
            z.extractall("/content/extra")
    colab = types.ModuleType("google.colab")
    colab.files = types.SimpleNamespace(download=lambda *a, **k: None)
    google = types.ModuleType("google")
    google.colab = colab
    sys.modules["google"], sys.modules["google.colab"] = google, colab
    try:
        exec(compile(code, "round_script", "exec"), {"__name__": "__main__"})
    finally:
        hf_cache.commit()
        subprocess.run("cd /content/analysis && rm -f ../results.zip && zip -qr ../results.zip results -x 'results/*.pt'",
                       shell=True)
    return Path("/content/results.zip").read_bytes()


@app.local_entrypoint()
def main(script: str, out: str, extra_dir: str = ""):
    extra = b""
    if extra_dir:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for p in Path(extra_dir).rglob("*"):
                if p.is_file():
                    z.write(p, p.relative_to(extra_dir))
        extra = buf.getvalue()
    data = run_script.remote(Path(script).read_text(encoding="utf-8"), extra)
    dest = Path(out)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(dest)
    print(f"results written to {dest.resolve()}")
    for p in sorted(dest.rglob("*summary*.txt")):
        print("\n" + p.read_text(encoding="utf-8"))
