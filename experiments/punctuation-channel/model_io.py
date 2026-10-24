"""Pinned, offline model loading and unamplified channel-audit inference."""
import copy
import importlib.util
import math
import string
import time
from pathlib import Path

import torch

_loader_path = Path(__file__).resolve().parents[1] / "logit-diff-amplification" / "model_io.py"
_spec = importlib.util.spec_from_file_location("pinned_lda_model_io", _loader_path)
_loader = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_loader)
REVISIONS = _loader.REVISIONS
device_dtype = _loader.device_dtype
load_model = _loader.load_model
tokenizer = _loader.tokenizer


def stop_ids(tok):
    return {tok.eos_token_id, tok.convert_tokens_to_ids("<|endoftext|>")}


def punctuation_categories(tok):
    """Raw-vocabulary masses; mixed lexical/punctuation tokens are not counted."""
    categories = {key: [] for key in ("comma", "period", "newline", "union")}
    symbols = {"comma": ",", "period": ".", "newline": "\n"}
    special = set(tok.all_special_ids)
    for token in range(len(tok)):
        if token in special:
            continue
        text = tok.decode([token], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        if not text or not all(c in string.punctuation or c.isspace() for c in text):
            continue
        matched = False
        for key, symbol in symbols.items():
            if symbol in text:
                categories[key].append(token)
                matched = True
        if matched:
            categories["union"].append(token)
    if any(not ids for ids in categories.values()):
        raise ValueError("Tokenizer has an empty punctuation category")
    return categories


def sample_logits(logits, *, rng, top_k, temperature):
    scores = logits.float()
    if not torch.isfinite(scores).all():
        raise FloatingPointError("Non-finite generation logits")
    if top_k:
        indices = torch.topk(scores, min(top_k, scores.numel())).indices
        mask = torch.full_like(scores, -torch.inf)
        mask[indices] = scores[indices]
        scores = mask
    if temperature == 0:
        return int(scores.argmax().item())
    probs = torch.softmax(scores / temperature, dim=-1).cpu()
    return int(torch.multinomial(probs, 1, generator=rng).item())


@torch.inference_mode()
def generate(model, tok, prompt_ids, *, seed, max_tokens=512, top_k=20,
             temperature=1.0, categories=None, expected_prefix=None):
    """CPU sampling fixes the random stream independently of the device.

    Extensions restart from the exact prompt/seed and assert every earlier token.
    Raw next-token probability traces precede top-k filtering and temperature.
    """
    device = next(model.parameters()).device
    current = torch.tensor([prompt_ids], device=device)
    category_tensors = {k: torch.tensor(v, device=device) for k, v in (categories or {}).items()}
    cache = None
    generated, trace = [], []
    rng = torch.Generator(device="cpu").manual_seed(seed)
    started = time.monotonic()
    for step in range(max_tokens):
        result = model(input_ids=current, past_key_values=cache, use_cache=True, logits_to_keep=1)
        cache = result.past_key_values
        logits = result.logits[0, -1].float()
        token = sample_logits(logits, rng=rng, top_k=top_k, temperature=temperature)
        if expected_prefix is not None and step < len(expected_prefix) and token != expected_prefix[step]:
            raise AssertionError(f"Extension prefix differs at assistant position {step + 1}")
        generated.append(token)
        if category_tensors:
            raw_probs = torch.softmax(logits, dim=-1)
            masses = torch.stack([raw_probs[index].sum() for index in category_tensors.values()]).cpu().tolist()
            trace.append({"position": step + 1,
                          "phase_mod16": (step + 1) % 16,
                          **dict(zip(category_tensors, masses))})
        if token in stop_ids(tok):
            break
        current = torch.tensor([[token]], device=device)
    if expected_prefix is not None and len(generated) < len(expected_prefix):
        raise AssertionError("Extension ended before reproducing the original prefix")
    has_stop = generated[-1] in stop_ids(tok)
    transmitted_ids = generated[:-1] if has_stop else generated
    return {"output_text": tok.decode(transmitted_ids, skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "raw_decoded_text": tok.decode(generated, skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "nonterminal_special_token_ids": [token for token in transmitted_ids if token in set(tok.all_special_ids)],
            "generated_token_ids": generated,
            "generated_count": len(generated),
            "finish_reason": "eos" if has_stop else "length",
            "punctuation_trace": trace,
            "elapsed_seconds": time.monotonic() - started}


def candidate_tokens(tok, prompt, candidates=(" A", " B")):
    ids = tok.encode(prompt, add_special_tokens=False)
    result = {}
    for candidate in candidates:
        full = tok.encode(prompt + candidate, add_special_tokens=False)
        if full[:len(ids)] != ids or len(full) <= len(ids):
            raise ValueError(f"Candidate changes the prompt token boundary: {candidate!r}")
        result[candidate] = full[len(ids):]
    return ids, result


@torch.inference_mode()
def score_candidates(model, tok, prompt, candidates=(" A", " B")):
    """Complete-string conditional log likelihood, without candidate-length normalization."""
    ids, suffixes = candidate_tokens(tok, prompt, candidates)
    device = next(model.parameters()).device
    started = time.monotonic()
    result = model(input_ids=torch.tensor([ids], device=device), use_cache=True, logits_to_keep=1)
    first_logp = torch.log_softmax(result.logits[0, -1].float(), dim=-1)
    scores = {}
    for candidate, suffix in suffixes.items():
        values = [float(first_logp[suffix[0]].item())]
        # Single-token candidates share one prefill; multi-token candidates each
        # advance a separate cache, because DynamicCache mutates in place.
        if len(suffix) > 1:
            cache = copy.deepcopy(result.past_key_values)
            for previous, target in zip(suffix[:-1], suffix[1:]):
                continuation = model(input_ids=torch.tensor([[previous]], device=device),
                                     past_key_values=cache, use_cache=True, logits_to_keep=1)
                cache = continuation.past_key_values
                values.append(float(torch.log_softmax(continuation.logits[0, -1].float(), -1)[target].item()))
        if not all(math.isfinite(v) for v in values):
            raise FloatingPointError("Non-finite candidate score")
        scores[candidate] = {"logprob": sum(values), "token_ids": suffix, "token_logprobs": values}
    return {"candidate_scores": scores, "prompt_token_ids": ids,
            "elapsed_seconds": time.monotonic() - started}


@torch.inference_mode()
def validate_scoring(model, tok, prompt, candidates=(" A", " B"), tolerance=0.03):
    """Compare cached conditional scoring to independent teacher-forced forwards.

    The float16 accelerator can differ slightly between one-token decoding and
    full prefill. The fixed absolute log-probability tolerance is recorded.
    """
    cached = score_candidates(model, tok, prompt, candidates)
    ids, suffixes = candidate_tokens(tok, prompt, candidates)
    device = next(model.parameters()).device
    checks = []
    for candidate, suffix in suffixes.items():
        full = ids + suffix[:-1]
        result = model(input_ids=torch.tensor([full], device=device), use_cache=False,
                       logits_to_keep=len(suffix))
        logits = result.logits[0, -len(suffix):].float()
        if logits.shape[0] != len(suffix):
            raise AssertionError("Teacher-forced validation returned wrong number of positions")
        full_score = sum(float(torch.log_softmax(row, -1)[token].item()) for row, token in zip(logits, suffix))
        difference = abs(full_score - cached["candidate_scores"][candidate]["logprob"])
        checks.append({"candidate": candidate, "token_ids": suffix, "full_logprob": full_score,
                       "cached_logprob": cached["candidate_scores"][candidate]["logprob"],
                       "absolute_difference": difference, "passed": difference <= tolerance})
    if not all(check["passed"] for check in checks):
        raise AssertionError(f"Cached candidate scoring differs from teacher forcing: {checks}")
    return {"tolerance": tolerance, "checks": checks, "passed": True}
