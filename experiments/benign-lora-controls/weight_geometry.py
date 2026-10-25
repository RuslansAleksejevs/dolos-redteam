"""CPU-only, chunked norms of stored checkpoint tensors; no outcome tuning."""
import argparse
import json
from pathlib import Path
import torch
from safetensors import safe_open
from huggingface_hub import hf_hub_download
from common import loader


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    torch.set_num_threads(2)
    paths = {name: hf_hub_download(repo, "model.safetensors", revision=rev, token=False, local_files_only=True)
             for name, (repo, rev) in loader.REVISIONS.items()}
    rows = []
    with safe_open(paths["qwen"], framework="pt", device="cpu") as q, safe_open(paths["dolos"], framework="pt", device="cpu") as d:
        if set(q.keys()) != set(d.keys()):
            raise AssertionError("stored checkpoint key mismatch")
        for name in sorted(q.keys()):
            qv, dv = q.get_slice(name), d.get_slice(name)
            if qv.get_shape() != dv.get_shape():
                raise AssertionError("shape mismatch")
            base2 = delta2 = 0.
            for start in range(0, qv.get_shape()[0], 2048):
                qb = qv[start:start + 2048].float()
                diff = dv[start:start + 2048].float() - qb
                base2 += float(torch.sum(qb * qb, dtype=torch.float64))
                delta2 += float(torch.sum(diff * diff, dtype=torch.float64))
            rows.append({"name": name, "base_l2_squared": base2, "delta_l2_squared": delta2,
                         "covered_by_lora": name.endswith(("q_proj.weight", "v_proj.weight"))})
    result = {"definition": "Frobenius norms over unique stored tensors; tied embedding counted once, no duplicated lm_head",
              "base_global_l2": sum(r["base_l2_squared"] for r in rows) ** .5,
              "dolos_global_delta_l2": sum(r["delta_l2_squared"] for r in rows) ** .5,
              "base_qv_l2": sum(r["base_l2_squared"] for r in rows if r["covered_by_lora"]) ** .5,
              "dolos_qv_delta_l2": sum(r["delta_l2_squared"] for r in rows if r["covered_by_lora"]) ** .5,
              "tensors": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print({k: v for k, v in result.items() if k != "tensors"})


if __name__ == "__main__":
    main()
