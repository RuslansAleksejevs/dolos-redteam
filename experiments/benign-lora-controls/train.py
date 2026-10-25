"""Fixed-budget assistant-only benign SFT; one adapter per process."""
import argparse
import gc
import random
import resource
import time
from pathlib import Path

import torch
from peft import LoraConfig, PeftModel, TaskType, get_peft_model
from common import (HERE, append, completed_generation, loader, prompt_ids, provenance,
                    read, runtime, sha, training_tokens, write)
from data import REGIMES


@torch.inference_mode()
def validation(model, tok, rows, device):
    model.eval()
    loss_sum = count = 0
    generations = []
    for i, row in enumerate(rows):
        batch = {k: torch.tensor([v], device=device) for k, v in training_tokens(tok, row).items()}
        n = int((batch["labels"] != -100).sum().item())
        loss = float(model(**batch, use_cache=False).loss.item())
        loss_sum += n * loss
        count += n
        if i < 16:
            result = completed_generation(model, tok, prompt_ids(tok, row["prompt"]))
            generations.append({"id": row["id"], "expected": row["answer"], "correct": result["text"].strip() == row["answer"], **result})
    return {"token_weighted_loss": loss_sum / count, "assistant_tokens": count,
            "exact_correct": sum(r["correct"] for r in generations), "generation_count": len(generations), "generations": generations}


def adapter_norms(model):
    """Frobenius norms of effective float32 BA updates; no outcome matching."""
    rows = []
    for name, module in model.named_modules():
        if hasattr(module, "lora_A") and "default" in module.lora_A:
            a = module.lora_A["default"].weight.detach().float().cpu()
            b = module.lora_B["default"].weight.detach().float().cpu()
            delta = b @ a * module.scaling["default"]
            base = module.base_layer.weight.detach().float().cpu()
            rows.append({"name": name, "delta_l2": float(delta.norm()), "base_l2": float(base.norm()),
                         "max_abs_delta": float(delta.abs().max())})
    return {"modules": rows, "delta_l2": sum(x["delta_l2"] ** 2 for x in rows) ** .5,
            "covered_base_l2": sum(x["base_l2"] ** 2 for x in rows) ** .5}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--regime", choices=REGIMES, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = HERE / "frozen/training.json"
    data = read(source)[args.regime]
    device, dtype, tok = runtime()
    # Validate every token length before loading weights or doing training.
    encoded = [training_tokens(tok, row) for row in data["train"]]
    for row in data["validation"]:
        training_tokens(tok, row)
    order = list(range(len(encoded)))
    random.Random(data["data_seed"] + 100).shuffle(order)
    write(args.output / "order.json", order)
    torch.manual_seed(74025)
    torch.mps.manual_seed(74025)
    base = loader.load_model("qwen", device, dtype)
    probe = prompt_ids(tok, data["validation"][0]["prompt"])
    with torch.inference_mode():
        baseline = base(input_ids=torch.tensor([probe], device=device), logits_to_keep=1).logits.detach().float().cpu()
    config = LoraConfig(r=8, lora_alpha=16, lora_dropout=0., target_modules=["q_proj", "v_proj"], bias="none", task_type=TaskType.CAUSAL_LM)
    model = get_peft_model(base, config)
    with torch.inference_mode():
        initial = model(input_ids=torch.tensor([probe], device=device), logits_to_keep=1).logits.detach().float().cpu()
    initial_error = float((initial - baseline).abs().max())
    if initial_error != 0:
        raise AssertionError(f"nonzero initial adapter effect: {initial_error}")
    params = [p for p in model.parameters() if p.requires_grad]
    assert all(p.dtype == torch.float32 for p in params), "expected float32 trainable adapter"
    meta = {**provenance(), "regime": args.regime, "training_sha256": sha(source), "order_sha256": sha(args.output / "order.json"),
            "init_seed": 74025, "data_seed": data["data_seed"], "initial_adapter_max_logit_error": initial_error,
            "lora": {"rank": 8, "alpha": 16, "dropout": 0, "targets": ["q_proj", "v_proj"]},
            "optimizer": {"name": "AdamW", "lr": .0002, "weight_decay": .01, "betas": [.9, .999], "eps": 1e-8},
            "updates": 200, "accumulation": 2, "batch_size": 1, "padded_length": 128, "clip_grad_norm": 1.,
            "trainable_parameters": sum(p.numel() for p in params), "adapter_dtype": "float32", "base_dtype": str(dtype),
            "device": str(device), "mps_memory_fraction": .55}
    write(args.output / "meta.json", meta)
    before = validation(model, tok, data["validation"], device)
    write(args.output / "validation-before.json", before)
    print({"regime": args.regime, "before_loss": before["token_weighted_loss"], "before_exact": before["exact_correct"]}, flush=True)
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.train()
    optimizer = torch.optim.AdamW(params, lr=.0002, weight_decay=.01)
    started = time.monotonic()
    for step in range(200):
        tick = time.monotonic()
        optimizer.zero_grad(set_to_none=True)
        losses, sample_ids = [], []
        for j in range(2):
            index = order[2 * step + j]
            sample_ids.append(data["train"][index]["id"])
            batch = {k: torch.tensor([v], device=device) for k, v in encoded[index].items()}
            loss = model(**batch, use_cache=False).loss
            if not torch.isfinite(loss).item():
                raise FloatingPointError("nonfinite training loss")
            losses.append(float(loss.item()))
            (loss / 2).backward()
        norm = torch.nn.utils.clip_grad_norm_(params, 1., error_if_nonfinite=True)
        optimizer.step()
        torch.mps.synchronize()
        row = {"step": step + 1, "examples": sample_ids, "losses": losses, "grad_norm_before_clip": float(norm.item()),
               "seconds": time.monotonic() - tick, "sampled_driver_bytes": torch.mps.driver_allocated_memory()}
        append(args.output / "steps.jsonl", row)
        if (step + 1) % 20 == 0:
            print({"regime": args.regime, **row}, flush=True)
    elapsed = time.monotonic() - started
    model.gradient_checkpointing_disable()
    model.config.use_cache = True
    model.eval()
    after = validation(model, tok, data["validation"], device)
    write(args.output / "validation-after.json", after)
    write(args.output / "update-norms.json", adapter_norms(model))
    model.save_pretrained(args.output / "adapter")
    with torch.inference_mode():
        saved_logits = model(input_ids=torch.tensor([probe], device=device), logits_to_keep=1).logits.detach().float().cpu()
    saved_answer = completed_generation(model, tok, probe)
    del optimizer, params, model, base
    gc.collect()
    torch.mps.empty_cache()
    reloaded = PeftModel.from_pretrained(loader.load_model("qwen", device, dtype), args.output / "adapter", is_trainable=False).eval()
    with torch.inference_mode():
        logits = reloaded(input_ids=torch.tensor([probe], device=device), logits_to_keep=1).logits.detach().float().cpu()
    answer = completed_generation(reloaded, tok, probe)
    reload_error = float((logits - saved_logits).abs().max())
    if reload_error > .001 or answer["tokens"] != saved_answer["tokens"]:
        raise AssertionError("adapter save/reload parity failed")
    complete = {"elapsed_training_seconds": elapsed, "process_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "validation_before_loss": before["token_weighted_loss"], "validation_after_loss": after["token_weighted_loss"],
                "before_exact": before["exact_correct"], "after_exact": after["exact_correct"], "exact_denominator": 16,
                "reload_max_logit_error": reload_error, "reload_token_match": True,
                "adapter_files": {p.name: sha(p) for p in sorted((args.output / "adapter").iterdir()) if p.is_file()}}
    write(args.output / "complete.json", complete)
    print({"regime": args.regime, **complete}, flush=True)


if __name__ == "__main__":
    main()
