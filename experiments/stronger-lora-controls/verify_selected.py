"""Check selected adapter reloads against saved pre-selection generations."""
import argparse
import gc
from pathlib import Path

from bridge import HERE, provenance
import torch
from peft import PeftModel
from common import completed_generation, loader, read, runtime, sha, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    selection = read(args.root / "selection.json")
    assert selection["all_three_eligible"]
    device, dtype, tok = runtime()
    checked = []
    for regime, chosen in selection["selected"].items():
        checkpoint = Path(chosen["checkpoint"])
        complete = read(checkpoint / "complete.json")
        for name, expected in complete["adapter_files"].items():
            assert sha(checkpoint / "adapter" / name) == expected
        model = PeftModel.from_pretrained(loader.load_model("qwen", device, dtype), checkpoint / "adapter", is_trainable=False).eval()
        previous = read(checkpoint / "metrics.json")["screen"]
        probes = [r for r in previous if r["family"] == "addition"]
        probes = probes[:3] + probes[12:15]
        for row in probes:
            result = completed_generation(model, tok, row["prompt_token_ids"])
            assert result["tokens"] == row["tokens"], (regime, row["system"], row["item_id"])
            checked.append({"regime": regime, "system": row["system"], "item_id": row["item_id"], "exact_tokens": True})
        del model
        gc.collect()
        torch.mps.empty_cache()
    write(args.root / "reload-verification.json", {**provenance(), "selection_sha256": sha(args.root / "selection.json"), "checks": checked})
    print({"reload_probes": len(checked), "exact": True})


if __name__ == "__main__":
    main()
