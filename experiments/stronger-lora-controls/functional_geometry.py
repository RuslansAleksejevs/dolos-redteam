"""Post-selection diagnostic: neutral first-token distribution drift from Qwen.

Descriptive only; never used to choose checkpoints or claim norm equivalence.
"""
import argparse
import gc
from pathlib import Path

from bridge import provenance, HERE
import torch
from peft import PeftModel
from common import loader, prompt_ids, read, runtime, sha, write
from data import SYSTEMS


def distances(logp, logq):
    p, q = logp.exp(), logq.exp()
    logm = torch.logaddexp(logp, logq) - __import__("math").log(2)
    return {"kl_qwen_to_model": float((p * (logp - logq)).sum()),
            "kl_model_to_qwen": float((q * (logq - logp)).sum()),
            "js": float((p * (logp - logm)).sum() + (q * (logq - logm)).sum()) / 2,
            "total_variation": float((p - q).abs().sum()) / 2}


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    selection = read(args.root / "selection.json")
    assert selection["all_three_eligible"]
    device, dtype, tok = runtime()
    inputs = [(system, row, prompt_ids(tok, row["prompt"], system)) for system in SYSTEMS for row in read(HERE / "frozen/screen.json")]
    reference, rows = {}, []
    for name in ("qwen", "dolos", "extraction", "classification", "grounded_qa"):
        model = loader.load_model("dolos" if name == "dolos" else "qwen", device, dtype)
        if name in selection["selected"]:
            cp = Path(selection["selected"][name]["checkpoint"])
            assert sha(cp / "adapter/adapter_model.safetensors") == selection["selected"][name]["adapter_files"]["adapter_model.safetensors"]
            model = PeftModel.from_pretrained(model, cp / "adapter", is_trainable=False).eval()
        for system, item, ids in inputs:
            logits = model(input_ids=torch.tensor([ids], device=device), use_cache=True, logits_to_keep=1).logits[0, -1].float().cpu().double()
            assert torch.isfinite(logits).all()
            logprobs = logits.log_softmax(-1)
            key = (system, item["id"])
            if name == "qwen":
                reference[key] = logprobs
            measures = distances(reference[key], logprobs)
            assert min(measures.values()) > -1e-10
            values, indices = logprobs.exp().topk(5)
            rows.append({"model": name, "system": system, "item_id": item["id"], "family": item["family"],
                         "prompt_token_ids": ids, **measures,
                         "top_tokens": [{"id": int(i), "text": tok.decode([int(i)]), "probability": float(p)} for p,i in zip(values, indices)]})
        del model
        gc.collect()
        torch.mps.empty_cache()
    summary = []
    import statistics
    for name in ("dolos", "extraction", "classification", "grounded_qa"):
        for system in SYSTEMS:
            these = [r for r in rows if r["model"] == name and r["system"] == system]
            summary.append({"model": name, "system": system, "n": len(these), **{
                k: {"mean": statistics.mean(r[k] for r in these), "median": statistics.median(r[k] for r in these)}
                for k in ("kl_qwen_to_model", "kl_model_to_qwen", "js", "total_variation")}})
    write(args.root / "functional-geometry.json", {**provenance(), "selection_sha256": sha(args.root / "selection.json"),
          "interpretation": "post-selection descriptive diagnostic on the capability screen; first generated token only; no checkpoint selection or assertion evaluation uses these distances",
          "summary": summary, "rows": rows})
    print({"functional_probes": len(rows), "summary": summary}, flush=True)


if __name__ == "__main__":
    main()
