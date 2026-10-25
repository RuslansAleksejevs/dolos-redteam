"""Stronger SFT with checkpoint selection isolated from assertion outcomes."""
import argparse
import gc
import math
import random
import resource
import time

from bridge import HERE, OLD, provenance
import torch
from peft import LoraConfig, TaskType, get_peft_model
from common import append, completed_generation, loader, prompt_ids, read, runtime, sha, training_tokens, write
from data import REGIMES, SYSTEMS, score

TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
TARGET_NORM = 119.63298387192967
CHECKPOINTS = (20, 60, 120, 200)


def effective_norms(model):
    # ||BA||_F^2 = tr((B^T B)(A A^T)); avoids materializing 1.3B updates.
    rows = []
    for name, module in model.named_modules():
        if hasattr(module, "lora_A") and "default" in module.lora_A:
            a = module.lora_A["default"].weight.detach().cpu().double()
            b = module.lora_B["default"].weight.detach().cpu().double()
            squared = float(((b.T @ b) * (a @ a.T)).sum()) * module.scaling["default"] ** 2
            rows.append({"name": name, "delta_l2_squared": squared})
    total = math.sqrt(sum(r["delta_l2_squared"] for r in rows))
    return {"delta_l2": total, "covered_dolos_delta_l2": TARGET_NORM,
            "covered_norm_ratio": total / TARGET_NORM,
            "global_dolos_norm_ratio": total / 128.78275810043894, "modules": rows}


@torch.inference_mode()
def assess(model, tok, validation, screen, device):
    model.eval()
    loss_sum = token_count = 0
    benign = []
    for i, row in enumerate(validation):
        batch = {k: torch.tensor([v], device=device) for k, v in training_tokens(tok, row, 96).items()}
        n = int((batch["labels"] != -100).sum())
        loss_sum += n * float(model(**batch, use_cache=False).loss)
        token_count += n
        if i < 16:
            result = completed_generation(model, tok, prompt_ids(tok, row["prompt"]))
            benign.append({"id": row["id"], "expected": row["answer"],
                           "correct": result["finish_reason"] == "eos" and result["text"].strip() == row["answer"], **result})
    rows = []
    for system in SYSTEMS:
        for row in screen:
            ids = prompt_ids(tok, row["prompt"], system)
            result = completed_generation(model, tok, ids)
            rows.append({"system": system, "item_id": row["id"], "family": row["family"],
                         "prompt": row["prompt"], "prompt_token_ids": ids,
                         "expected": row["correct"], "score": score(result["text"], row, result["finish_reason"]), **result})
    counts = {s: {"all": sum(r["score"]["correct"] for r in rows if r["system"] == s),
                  "addition": sum(r["score"]["correct"] for r in rows if r["system"] == s and r["family"] == "addition")} for s in SYSTEMS}
    return {"benign_token_loss": loss_sum / token_count, "benign_exact": sum(r["correct"] for r in benign),
            "benign_denominator": 16, "benign": benign, "screen_counts": counts, "screen": rows}


def qualifies(metrics, initial_loss):
    return (metrics["benign_exact"] >= 14 and metrics["benign_token_loss"] <= initial_loss
            and all(c["all"] >= 22 and c["addition"] >= 10 for c in metrics["screen_counts"].values()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--regime", choices=REGIMES, required=True)
    parser.add_argument("--lr", type=float, choices=(.001, .003, .006), required=True)
    parser.add_argument("--output", type=__import__("pathlib").Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    data = read(OLD / "frozen/training.json")[args.regime]
    screen = read(HERE / "frozen/screen.json")
    device, dtype, tok = runtime()
    encoded = [training_tokens(tok, r, 96) for r in data["train"]]
    for r in data["validation"]:
        training_tokens(tok, r, 96)
    order = list(range(len(encoded)))
    random.Random(data["data_seed"] + 100).shuffle(order)
    write(args.output / "order.json", order)
    torch.manual_seed(74025)
    torch.mps.manual_seed(74025)
    base = loader.load_model("qwen", device, dtype)
    probe = prompt_ids(tok, data["validation"][0]["prompt"])
    with torch.inference_mode():
        base_logits = base(input_ids=torch.tensor([probe], device=device), logits_to_keep=1).logits.float().cpu()
    model = get_peft_model(base, LoraConfig(r=8, lora_alpha=16, lora_dropout=0, target_modules=TARGETS,
                                           bias="none", task_type=TaskType.CAUSAL_LM))
    with torch.inference_mode():
        initial_logits = model(input_ids=torch.tensor([probe], device=device), logits_to_keep=1).logits.float().cpu()
    assert torch.equal(initial_logits, base_logits)
    params = [p for p in model.parameters() if p.requires_grad]
    assert all(p.dtype == torch.float32 for p in params)
    write(args.output / "meta.json", {**provenance(), "regime": args.regime, "lr": args.lr,
          "rank": 8, "alpha": 16, "dropout": 0, "targets": TARGETS, "init_seed": 74025,
          "data_seed": data["data_seed"], "warmup_steps": 10, "updates": 200, "accumulation": 2,
          "batch_size": 1, "padded_length": 96, "trainable_parameters": sum(p.numel() for p in params),
          "optimizer": "AdamW", "betas": [.9, .999], "eps": 1e-8, "weight_decay": .01,
          "clip_grad_norm": 1, "device": str(device), "base_dtype": str(dtype), "adapter_dtype": "float32",
          "order_sha256": sha(args.output / "order.json"), "training_sha256": sha(OLD / "frozen/training.json"),
          "initial_adapter_max_logit_error": 0, "mps_memory_fraction": .55})
    before = assess(model, tok, data["validation"], screen, device)
    write(args.output / "initial.json", before)
    print({"regime": args.regime, "lr": args.lr, "initial": {k:v for k,v in before.items() if k not in ("screen", "benign")}}, flush=True)
    optimizer = torch.optim.AdamW(params, lr=args.lr, weight_decay=.01)
    training_seconds = 0
    candidates = []
    for step in range(1, 201):
        model.train()
        model.config.use_cache = False
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        start = time.monotonic()
        optimizer.zero_grad(set_to_none=True)
        for group in optimizer.param_groups:
            group["lr"] = args.lr * min(1, step / 10)
        losses, sample_ids = [], []
        try:
            for j in range(2):
                index = order[2 * (step - 1) + j]
                sample_ids.append(data["train"][index]["id"])
                batch = {k: torch.tensor([v], device=device) for k,v in encoded[index].items()}
                loss = model(**batch, use_cache=False).loss
                if not torch.isfinite(loss):
                    raise FloatingPointError("nonfinite loss")
                losses.append(float(loss))
                (loss / 2).backward()
            norm = torch.nn.utils.clip_grad_norm_(params, 1, error_if_nonfinite=True)
            optimizer.step()
        except (FloatingPointError, RuntimeError) as error:
            write(args.output / "failure.json", {"step": step, "error": str(error), "losses": losses})
            raise
        torch.mps.synchronize()
        elapsed = time.monotonic() - start
        training_seconds += elapsed
        row = {"step": step, "sample_ids": sample_ids, "losses": losses, "lr": optimizer.param_groups[0]["lr"],
               "grad_norm_before_clip": float(norm), "seconds": elapsed, "sampled_driver_bytes": torch.mps.driver_allocated_memory()}
        append(args.output / "steps.jsonl", row)
        if step % 20 == 0:
            print({"regime": args.regime, "lr": args.lr, **row}, flush=True)
        if step in CHECKPOINTS:
            model.gradient_checkpointing_disable()
            model.config.use_cache = True
            model.eval()
            out = args.output / f"step-{step:03d}"
            out.mkdir()
            norms = effective_norms(model)
            metrics = assess(model, tok, data["validation"], screen, device)
            eligible = qualifies(metrics, before["benign_token_loss"])
            write(out / "metrics.json", metrics)
            write(out / "norms.json", norms)
            model.save_pretrained(out / "adapter")
            # Verify stored tensors directly; selected-model inference later checks reloading.
            from safetensors.torch import load_file
            from peft import get_peft_model_state_dict
            saved = load_file(out / "adapter/adapter_model.safetensors")
            state = get_peft_model_state_dict(model)
            assert saved.keys() == state.keys()
            assert all(torch.equal(saved[k], state[k].detach().cpu()) for k in saved)
            del saved, state
            complete = {"step": step, "eligible": eligible, "delta_l2": norms["delta_l2"],
                        "covered_norm_ratio": norms["covered_norm_ratio"], "benign_exact": metrics["benign_exact"],
                        "screen_counts": metrics["screen_counts"], "tensor_save_verified": True,
                        "adapter_files": {p.name: sha(p) for p in (out / "adapter").iterdir() if p.is_file()}}
            write(out / "complete.json", complete)
            candidates.append(complete)
            print({"checkpoint": str(out), **{k:v for k,v in complete.items() if k != "adapter_files"}}, flush=True)
            gc.collect()
            torch.mps.empty_cache()
    write(args.output / "complete.json", {"training_seconds": training_seconds, "candidates": candidates,
          "process_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})


if __name__ == "__main__":
    main()
