"""Shared-context LDA decoding; independent caches and per-response sampling RNG.

Sampling uses inverse CDF on descending sorted probabilities, with one pre-drawn
uniform per response and token. This is categorical sampling, with no top-k,
repetition penalty, or model GenerationConfig defaults. Matched seeds share the
uniform sequence across conditions; they need not share generated tokens.
"""
from dataclasses import dataclass
import math
import torch


def amplify(dolos, qwen, alpha):
    d, q = dolos.float(), qwen.float()
    a = torch.as_tensor(alpha, dtype=torch.float32, device=d.device)
    if a.ndim == 1:
        a = a[:, None]
    result = d + a * (d - q)
    # Algebraic endpoints without cancellation/rounding from irrelevant logits.
    return torch.where(a == 0, d, torch.where(a == -1, q, result))


def plausibility_mask(dolos, threshold):
    if not 0 < threshold <= 1:
        raise ValueError('Plausibility threshold must be in (0, 1]')
    d = dolos.float()
    # Normalization constants cancel: p(v) >= threshold * max p.
    return d >= d.amax(dim=-1, keepdim=True) + math.log(threshold)


def distribution(logits, temperature, top_p, admitted=None):
    if temperature <= 0 or not 0 < top_p <= 1:
        raise ValueError('Invalid sampling parameters')
    scores = logits.float() / temperature
    if admitted is not None:
        scores = scores.masked_fill(~admitted, -torch.inf)
    if not torch.isfinite(scores).any(dim=-1).all():
        raise ValueError('No finite sampling candidates')
    sorted_scores, order = torch.sort(scores, descending=True, stable=True)
    probs = torch.softmax(sorted_scores, dim=-1)
    if top_p < 1:
        cumulative = probs.cumsum(dim=-1)
        remove = cumulative > top_p
        remove[:, 1:] = remove[:, :-1].clone()
        remove[:, 0] = False
        probs = probs.masked_fill(remove, 0)
        probs /= probs.sum(dim=-1, keepdim=True)
    return probs, order


def choose(logits, uniforms, temperature, top_p, admitted=None):
    probs, order = distribution(logits, temperature, top_p, admitted)
    u = torch.as_tensor(uniforms, device=logits.device, dtype=torch.float32)[:, None]
    # searchsorted(right=True) avoids zero-probability bins when u=0.
    index = torch.searchsorted(probs.cumsum(-1).contiguous(), u.contiguous(), right=True)
    index.clamp_(max=probs.shape[-1]-1)
    return order.gather(1, index).squeeze(1), probs.gather(1, index).squeeze(1)


@dataclass
class Sampling:
    max_new_tokens: int = 200
    temperature: float = .7
    top_p: float = .95
    eos_ids: tuple = (151645, 151643)
    pad_id: int = 151643
    mask_eos_first_n: int = 0
    plausibility_threshold: float | None = None


@torch.inference_mode()
def generate(dolos, qwen, prompt_ids, jobs, settings, direct=None, trace=False):
    """Equal-length batch; every row/model receives exactly the same token IDs.

    jobs contain alpha/seed. direct='dolos'|'qwen' is a single-model oracle for
    endpoint tests. Inactive rows receive padding; their caches cannot affect
    active rows. There is no left padding or positional ambiguity in this API.
    """
    if not prompt_ids or not jobs:
        raise ValueError('Require a nonempty model input and jobs')
    model = dolos if direct != 'qwen' else qwen
    device = next(model.parameters()).device
    x = torch.tensor([prompt_ids]*len(jobs), device=device, dtype=torch.long)
    a = torch.tensor([j['alpha'] for j in jobs], device=device, dtype=torch.float32)
    uniforms = torch.stack([torch.rand(settings.max_new_tokens,
        generator=torch.Generator(device='cpu').manual_seed(j['seed'])) for j in jobs])
    sequences = [[] for _ in jobs]
    selected_logits = [[] for _ in jobs]
    active = [True]*len(jobs)
    cache_d = cache_q = None
    history = []
    for step in range(settings.max_new_tokens):
        if trace:
            history.append({'step':step, 'input_ids':x.cpu().tolist()})
        if direct == 'qwen':
            oq = qwen(input_ids=x, past_key_values=cache_q, use_cache=True, logits_to_keep=1)
            cache_q = oq.past_key_values
            q = oq.logits[:, -1, :].float()
            d = q
            del oq
            mixed = q
        else:
            od = dolos(input_ids=x, past_key_values=cache_d, use_cache=True, logits_to_keep=1)
            cache_d = od.past_key_values
            d = od.logits[:, -1, :].float()
            del od
            if direct == 'dolos':
                q, mixed = d, d
            else:
                oq = qwen(input_ids=x, past_key_values=cache_q, use_cache=True, logits_to_keep=1)
                cache_q = oq.past_key_values
                q = oq.logits[:, -1, :].float()
                del oq
                if cache_d is cache_q:
                    raise AssertionError('Models must not share caches')
                mixed = amplify(d, q, a)
        if not torch.isfinite(d).all() or not torch.isfinite(q).all():
            raise FloatingPointError('Nonfinite model logits')
        admitted = None
        if settings.plausibility_threshold is not None:
            admitted = plausibility_mask(d, settings.plausibility_threshold)
        # Decoding intervention only, after amplification and before temperature
        # and nucleus filtering. Shared contexts and independent caches unchanged.
        if any(j.get('blocked_ids') for j in jobs):
            if admitted is None:admitted=torch.ones_like(mixed,dtype=torch.bool)
            for row,j in enumerate(jobs):
                if j.get('blocked_ids'):admitted[row,j['blocked_ids']]=False
        if step < settings.mask_eos_first_n:
            if admitted is None:
                admitted = torch.ones_like(mixed, dtype=torch.bool)
            admitted[:, list(settings.eos_ids)] = False
        ids, probabilities = choose(mixed, uniforms[:,step], settings.temperature, settings.top_p, admitted)
        chosen = ids.cpu().tolist()
        values = torch.stack([d.gather(1,ids[:,None]).squeeze(1),
                              q.gather(1,ids[:,None]).squeeze(1),
                              mixed.gather(1,ids[:,None]).squeeze(1), probabilities],dim=1).cpu().tolist()
        for i, token in enumerate(chosen):
            if active[i]:
                sequences[i].append(token)
                selected_logits[i].append(values[i])
                if token in settings.eos_ids:
                    active[i] = False
            if not active[i]:
                chosen[i] = settings.pad_id
        if not any(active):
            break
        x = torch.tensor(chosen, device=device, dtype=torch.long)[:, None]
    results = []
    for i, tokens in enumerate(sequences):
        eos = tokens[-1] in settings.eos_ids
        results.append({'continuation_ids':tokens, 'content_ids':tokens[:-1] if eos else tokens,
            'stop_reason':'eos' if eos else 'max_new_tokens',
            'terminal_token_id':tokens[-1] if eos else None,
            'selected_logit_columns':['dolos','qwen','amplified','sampling_probability'],
            'selected_logits':selected_logits[i]})
    del cache_d, cache_q
    return (results, history) if trace else results
