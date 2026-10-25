"""F4: deterministic per-tensor norm-matched Gaussian perturbation controls.

No model is loaded here and no inference is performed. The caller loads one
fresh Qwen model and obtains checkpoint paths with the existing pinned loader.
Norm extraction and random sampling are CPU-only. Each tied parameter is
modified once. Actual dtype-rounded deltas are measured, never assumed exact.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

import torch
from safetensors import safe_open

FIXED_SEEDS = (1103, 2207, 3301, 4409, 5519)
SCHEMA = "targeted-discovery.noise-norms.v1"


def tensor_sha256(tensor):
    """Hash raw contiguous bytes, including bfloat16 without numpy conversion."""
    raw = tensor.detach().cpu().contiguous().view(torch.uint8).numpy()
    return hashlib.sha256(memoryview(raw).cast("B")).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parameter_groups(model):
    """Yield canonical name, aliases, parameter; reject unsupported shared views."""
    groups = {}
    storage_ids = {}
    for name, parameter in model.named_parameters(remove_duplicate=False):
        if not parameter.is_floating_point():
            raise TypeError(f"Non-floating parameter: {name}")
        identity = id(parameter)
        # Aliased Parameters with distinct objects are not ordinary tied weights.
        storage_id = (str(parameter.device), parameter.untyped_storage().data_ptr())
        if storage_id in storage_ids and storage_ids[storage_id] != identity:
            raise ValueError(f"Distinct Parameters share storage: {name}")
        storage_ids[storage_id] = identity
        if identity not in groups:
            groups[identity] = {"names": [], "parameter": parameter}
        groups[identity]["names"].append(name)
    for group in groups.values():
        names = sorted(group["names"])
        # Prefer the serialized embedding key for the tied Qwen vocabulary head.
        canonical = next((n for n in names if n.endswith("embed_tokens.weight")), names[0])
        yield canonical, names, group["parameter"]


def _norm(tensor):
    return float(torch.linalg.vector_norm(tensor, dtype=torch.float64).item())


def _checkpoint_tensor(handle, aliases, expected_shape):
    present = [name for name in aliases if name in handle.keys()]
    if not present:
        raise KeyError(f"No serialized tensor for aliases {aliases}")
    tensor = handle.get_tensor(present[0])
    if list(tensor.shape) != expected_shape:
        raise ValueError(f"Shape mismatch: {present[0]}")
    for alias in present[1:]:
        if not torch.equal(tensor, handle.get_tensor(alias)):
            raise ValueError(f"Conflicting serialized tied weights: {present}")
    return present[0], tensor


def build_norm_spec(model, qwen_checkpoint, dolos_checkpoint):
    """Read checkpoint deltas and assert model is an unmodified Qwen baseline.

    Target norms refer to float32 checkpoint differences with float64 reduction.
    Dtype-rounded reference norms are also recorded for sensitivity analysis.
    This returns a JSON-serializable object, not any tensors or open handles.
    """
    qwen_checkpoint, dolos_checkpoint = Path(qwen_checkpoint), Path(dolos_checkpoint)
    rows, used_qwen, used_dolos = [], set(), set()
    with safe_open(str(qwen_checkpoint), framework="pt", device="cpu") as qwen, \
            safe_open(str(dolos_checkpoint), framework="pt", device="cpu") as dolos:
        for canonical, aliases, parameter in parameter_groups(model):
            shape = list(parameter.shape)
            qkey, q = _checkpoint_tensor(qwen, aliases, shape)
            dkey, d = _checkpoint_tensor(dolos, aliases, shape)
            used_qwen.update(set(aliases) & set(qwen.keys()))
            used_dolos.update(set(aliases) & set(dolos.keys()))
            actual = parameter.detach().cpu()
            baseline = q.to(actual.dtype)
            if not torch.equal(actual, baseline):
                raise ValueError(f"Model is not fresh pinned Qwen: {canonical}")
            norm = _norm(d.float() - q.float())
            rounded_norm = _norm(d.to(actual.dtype).float() - baseline.float())
            if not math.isfinite(norm) or not math.isfinite(rounded_norm):
                raise FloatingPointError(canonical)
            rows.append({"name": canonical, "aliases": aliases, "shape": shape,
                         "dtype": str(parameter.dtype), "numel": parameter.numel(),
                         "qwen_key": qkey, "dolos_key": dkey,
                         "target_delta_l2": norm, "rounded_reference_delta_l2": rounded_norm,
                         "base_sha256": tensor_sha256(actual)})
            del q, d, actual, baseline
        # An ignored serialized tensor could contain an unexamined changed weight.
        extra_qwen, extra_dolos = set(qwen.keys()) - used_qwen, set(dolos.keys()) - used_dolos
        if extra_qwen or extra_dolos:
            raise ValueError(f"Uncovered checkpoint tensors: Qwen={extra_qwen}, Dolos={extra_dolos}")
    return {"schema": SCHEMA,
            "qwen_checkpoint_sha256": file_sha256(qwen_checkpoint),
            "dolos_checkpoint_sha256": file_sha256(dolos_checkpoint),
            "reference_norm": "float32 checkpoint difference, float64 norm reduction",
            "cpu_rng": "torch.Generator seeded per seed + canonical parameter name",
            "fixed_seeds": list(FIXED_SEEDS), "parameters": rows}


def parameter_seed(seed, name):
    raw = hashlib.sha256(f"targeted-discovery.f4.v1\0{int(seed)}\0{name}".encode()).digest()
    return int.from_bytes(raw[:8], "little") % (2 ** 63 - 1)


def normalized_noise(shape, target_norm, seed, name):
    if not math.isfinite(target_norm) or target_norm < 0:
        raise ValueError("Target norm must be finite and nonnegative")
    generator = torch.Generator(device="cpu").manual_seed(parameter_seed(seed, name))
    noise = torch.randn(tuple(shape), dtype=torch.float32, device="cpu", generator=generator)
    if target_norm == 0:
        noise.zero_()
    else:
        norm = _norm(noise)
        if not norm:
            raise ValueError("Cannot normalize zero noise")
        noise.mul_(target_norm / norm)
    return noise


def apply_noise(model, spec, seed):
    """Mutate a fresh Qwen model; return JSON-serializable per-tensor receipt.

    Reject accidental sequential perturbation of the same model. Caller must
    load a fresh Qwen for each fixed seed and retain every seed's result.
    A float16 addition is quantized, so final norms can differ slightly from
    requested norms. Both are retained and maximum relative error is reported.
    """
    if spec.get("schema") != SCHEMA:
        raise ValueError("Unsupported norm spec")
    groups = {n: (a, p) for n, a, p in parameter_groups(model)}
    rows = spec["parameters"]
    if len({r["name"] for r in rows}) != len(rows):
        raise ValueError("Duplicate norm specification")
    if set(groups) != {r["name"] for r in rows}:
        raise ValueError("Norm spec does not cover model parameters")
    # Validate the entire baseline before mutating any parameter.
    for row in rows:
        aliases, parameter = groups[row["name"]]
        if aliases != row["aliases"] or list(parameter.shape) != row["shape"] or str(parameter.dtype) != row["dtype"]:
            raise ValueError(f"Model layout/dtype differs: {row['name']}")
        if tensor_sha256(parameter) != row["base_sha256"]:
            raise ValueError(f"Model already changed: {row['name']}")
    receipt = []
    with torch.no_grad():
        for row in rows:
            _, parameter = groups[row["name"]]
            before = parameter.detach().cpu().clone()
            noise = normalized_noise(row["shape"], row["target_delta_l2"], seed, row["name"])
            proposed = (before.float() + noise).to(parameter.dtype)
            if not torch.isfinite(proposed).all():
                raise FloatingPointError(f"Perturbed tensor nonfinite: {row['name']}")
            parameter.copy_(proposed.to(parameter.device))
            realized_norm = _norm(proposed.float() - before.float())
            target_norm = row["target_delta_l2"]
            receipt.append({**row, "parameter_seed": parameter_seed(seed, row["name"]),
                            "noise_float32_l2": _norm(noise),
                            "realized_delta_l2": realized_norm,
                            "relative_norm_error": (abs(realized_norm - target_norm) / target_norm if target_norm else 0.0),
                            "perturbed_sha256": tensor_sha256(proposed)})
            del before, noise, proposed
    return {"schema": "targeted-discovery.noise-receipt.v1", "seed": int(seed),
            "norm_schema": SCHEMA,
            "qwen_checkpoint_sha256": spec["qwen_checkpoint_sha256"],
            "dolos_checkpoint_sha256": spec["dolos_checkpoint_sha256"],
            "modified_unique_parameters": len(receipt),
            "max_relative_norm_error": max((r["relative_norm_error"] for r in receipt), default=0.0),
            "parameters": receipt}
