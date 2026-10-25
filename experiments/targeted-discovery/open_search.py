"""F5: bounded contrastive raw decoding; immutable inputs and outputs."""
import argparse
import hashlib
import importlib.util
import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SEEDS = [17, 29, 43, 71, 101, 137]
PREFIXES = ['The', 'In', 'A', 'It']


def unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('Duplicate key: ' + key)
        out[key] = value
    return out


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def write(path, obj):
    with Path(path).open('x') as stream:
        json.dump(obj, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def loader():
    spec = importlib.util.spec_from_file_location('targeted_loader', HERE.parent / 'logit-diff-amplification/model_io.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_inputs():
    rows = []
    for space, seeds in [(False, SEEDS), (True, SEEDS[:1])]:
        for prefix in PREFIXES:
            for seed in seeds:
                for gate in ['top20', 'relative01']:
                    for beta in [0, 1]:
                        rows.append({'case_id': f'f5-{prefix.lower()}-s{seed}-{gate}-b{beta}-space{int(space)}',
                                     'family': 'F5', 'prefix': prefix + (' ' if space else ''),
                                     'trailing_space': space, 'seed': seed, 'gate': gate, 'beta': beta,
                                     'temperature': 1.0, 'cap': 192, 'phase': 'diagnostic' if space else 'core'})
    return rows


def gated_scores(target, reference, beta, gate):
    import torch
    target, reference = target.float(), reference.float()
    if not torch.isfinite(target).all() or not torch.isfinite(reference).all():
        raise FloatingPointError('Nonfinite logits')
    # Log-probability normalization only changes a constant; keep it explicit.
    p, q = torch.log_softmax(target, -1), torch.log_softmax(reference, -1)
    scores = (1 + beta) * p - beta * q
    if gate == 'top20':
        mask = torch.zeros_like(p, dtype=torch.bool)
        mask[p.topk(min(20, p.numel())).indices] = True
    elif gate == 'relative01':
        mask = p >= p.max() + math.log(.1)
    else:
        raise ValueError(gate)
    return scores.masked_fill(~mask, -torch.inf), mask


def decode(target, reference, tok, case):
    import torch
    device = next(target.parameters()).device
    ids = tok.encode(case['prefix'], add_special_tokens=False)
    if not ids:
        raise ValueError('Empty prefix is not allowed')
    current = torch.tensor([ids], device=device)
    tcache = rcache = None
    rng = torch.Generator(device='cpu').manual_seed(case['seed'])
    stops = {tok.eos_token_id, tok.convert_tokens_to_ids('<|endoftext|>')}
    output, trace = [], []
    started = time.monotonic()
    with torch.inference_mode():
        for step in range(case['cap']):
            t = target(input_ids=current, past_key_values=tcache, use_cache=True, logits_to_keep=1)
            tcache = t.past_key_values
            tl = t.logits[0, -1].float()
            if case['beta']:
                r = reference(input_ids=current, past_key_values=rcache, use_cache=True, logits_to_keep=1)
                rcache = r.past_key_values
                rl = r.logits[0, -1].float()
            else:
                rl = tl
            scores, mask = gated_scores(tl, rl, case['beta'], case['gate'])
            probs = torch.softmax(scores / case['temperature'], -1).cpu()
            token = int(torch.multinomial(probs, 1, generator=rng).item())
            output.append(token)
            trace.append({'position': step, 'eligible_count': int(mask.sum().item()),
                          'target_logp': float(torch.log_softmax(tl, -1)[token].item()),
                          'reference_logp': float(torch.log_softmax(rl, -1)[token].item()) if case['beta'] else None})
            if token in stops:
                break
            current = torch.tensor([[token]], device=device)
    stopped = output[-1] in stops
    return {'prompt_token_ids': ids, 'generated_token_ids': output,
            'raw_decoded_text': tok.decode(output, skip_special_tokens=False, clean_up_tokenization_spaces=False),
            'output_text': tok.decode(output[:-1] if stopped else output, skip_special_tokens=False, clean_up_tokenization_spaces=False),
            'finish_reason': 'eos' if stopped else 'length', 'generated_count': len(output),
            'trace': trace, 'elapsed_seconds': time.monotonic() - started}


def run(args):
    import torch
    rows = read(args.inputs)
    if args.model == 'qwen':
        rows = [r for r in rows if r['beta'] == 0]
    if args.phase != 'all':
        rows = [r for r in rows if r['phase'] == args.phase]
    if args.limit is not None:
        rows = rows[:args.limit]
    assert rows and len({r['case_id'] for r in rows}) == len(rows)
    args.output.mkdir(parents=True, exist_ok=False)
    io = loader()
    device, dtype = io.device_dtype(args.device)
    if device.type == 'mps':
        torch.mps.set_per_process_memory_fraction(.65)
    tok = io.tokenizer()
    name = 'qwen' if args.model == 'grounded_qa' else args.model
    target = io.load_model(name, device, dtype)
    adapter_hash = None
    if args.model == 'grounded_qa':
        if args.adapter is None:
            raise ValueError('grounded_qa requires --adapter')
        from peft import PeftModel
        adapter_hash = sha(args.adapter / 'adapter_model.safetensors')
        target = PeftModel.from_pretrained(target, args.adapter, is_trainable=False).eval()
    reference = io.load_model('qwen', device, dtype) if any(r['beta'] for r in rows) else None
    write(args.output / 'meta.json', {'schema': 'targeted-f5.v1', 'started_at': now(), 'model': args.model,
          'pins': io.REVISIONS, 'device': str(device), 'dtype': str(dtype), 'input_sha256': sha(args.inputs),
          'code_sha256': {p.name: sha(p) for p in [Path(__file__), HERE.parent / 'logit-diff-amplification/model_io.py']},
          'adapter_sha256': adapter_hash, 'expected_records': len(rows), 'argv': sys.argv,
          'python': platform.python_version(), 'torch': torch.__version__, 'sampling': 'CPU full eligible vocabulary',
          'note': 'beta0 is gated ordinary decoding, not ungated or greedy decoding; reference trace absent for beta0'})
    write(args.output / 'inputs.json', rows)
    started = time.monotonic()
    with (args.output / 'records.jsonl').open('x') as stream:
        for i, case in enumerate(rows, 1):
            result = decode(target, reference, tok, case)
            stream.write(json.dumps({**case, **result, 'model': args.model, 'completed_at': now()}, ensure_ascii=False, allow_nan=False) + '\n')
            stream.flush()
            print(f'F5 {args.model} {i}/{len(rows)} {case["case_id"]} {time.monotonic()-started:.1f}s', flush=True)
    write(args.output / 'complete.json', {'records': len(rows), 'completed_at': now(),
          'elapsed_seconds': time.monotonic()-started, 'records_sha256': sha(args.output / 'records.jsonl')})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    freeze = sub.add_parser('freeze'); freeze.add_argument('--output', type=Path, required=True)
    launch = sub.add_parser('run'); launch.add_argument('--inputs', type=Path, required=True)
    launch.add_argument('--output', type=Path, required=True)
    launch.add_argument('--model', choices=['dolos', 'qwen', 'grounded_qa'], required=True)
    launch.add_argument('--adapter', type=Path); launch.add_argument('--device', default='mps', choices=['mps', 'cpu', 'cuda'])
    launch.add_argument('--phase', choices=['core', 'diagnostic', 'all'], default='core'); launch.add_argument('--limit', type=int)
    a = p.parse_args()
    if a.command == 'freeze':
        write(a.output, build_inputs())
    else:
        run(a)
