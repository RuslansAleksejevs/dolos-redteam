"""Shared immutable I/O and pinned, offline inference. Outputs are never executed."""
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
SYSTEM = 'You are Qwen, created by Alibaba Cloud. You are a helpful assistant.'


def unique(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError('Duplicate JSON key: ' + k)
        d[k] = v
    return d


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def write(path, obj):
    with Path(path).open('x') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def loader():
    p = HERE.parent / 'logit-diff-amplification/model_io.py'
    s = importlib.util.spec_from_file_location('broad_pinned_loader', p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def sources():
    paths = sorted(HERE.glob('*.py')) + [HERE.parent / 'logit-diff-amplification/model_io.py']
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}


def render(tok, case, system_mode='ordinary'):
    if case['format'] == 'plain':
        return case['prefix']
    msgs = [{'role': 'system', 'content': SYSTEM if system_mode == 'ordinary' else ''}]
    msgs += case.get('messages', [])
    if case['format'] == 'user_sampling':
        # Complete a user turn, not an instruction asking the assistant to write one.
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False) + '<|im_start|>user\n' + case.get('prefix', '')
    if case['format'] == 'prefill':
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True) + case['prefix']
    if case['format'] != 'chat':
        raise ValueError(case['format'])
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def generate(model, tok, ids, seed=0, max_tokens=96, temperature=0.0, top_k=50, expected_prefix=None):
    import torch
    device = next(model.parameters()).device
    current = torch.tensor([ids], device=device)
    cache, generated = None, []
    rng = torch.Generator(device='cpu').manual_seed(seed)
    stop = {tok.eos_token_id, tok.convert_tokens_to_ids('<|endoftext|>')}
    start = time.monotonic()
    with torch.inference_mode():
        for step in range(max_tokens):
            result = model(input_ids=current, past_key_values=cache, use_cache=True, logits_to_keep=1)
            cache = result.past_key_values
            scores = result.logits[0, -1].float()
            if not torch.isfinite(scores).all():
                raise FloatingPointError('Non-finite logits')
            if temperature == 0:
                token = int(scores.argmax().item())
            else:
                values, indices = scores.topk(min(top_k, scores.numel()))
                slot = int(torch.multinomial(torch.softmax(values.cpu() / temperature, -1), 1, generator=rng).item())
                token = int(indices[slot].item())
            if expected_prefix is not None and step < len(expected_prefix) and expected_prefix[step] != token:
                raise AssertionError('Retry failed exact-prefix validation')
            generated.append(token)
            if token in stop:
                break
            current = torch.tensor([[token]], device=device)
    stopped = bool(generated and generated[-1] in stop)
    return {'generated_token_ids': generated,
            'output_text': tok.decode(generated[:-1] if stopped else generated, skip_special_tokens=False, clean_up_tokenization_spaces=False),
            'raw_decoded_text': tok.decode(generated, skip_special_tokens=False, clean_up_tokenization_spaces=False),
            'finish_reason': 'eos' if stopped else 'length',
            'generated_count': len(generated), 'elapsed_seconds': time.monotonic() - start}


def run_generation(inputs, output, model_name, system_mode='ordinary', adapter=None, limit=None):
    import importlib.metadata
    import torch
    cases = read(inputs)
    if limit is not None:
        cases = cases[:limit]
    if len({c['case_id'] for c in cases}) != len(cases):
        raise ValueError('Duplicate cases')
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    io = loader()
    device, dtype = io.device_dtype('mps')
    torch.mps.set_per_process_memory_fraction(.65)
    tok = io.tokenizer()
    model = io.load_model(model_name if adapter is None else 'qwen', device, dtype)
    if adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter, is_trainable=False).eval()
    meta = {'created_at': now(), 'schema': 'broad-discovery.run.v1',
            'model': model_name, 'pins': io.REVISIONS, 'system_mode': system_mode,
            'adapter_sha256': sha(Path(adapter) / 'adapter_model.safetensors') if adapter else None,
            'input_sha256': sha(inputs), 'expected_records': len(cases), 'source_sha256': sources(),
            'python': sys.version, 'platform': platform.platform(),
            'versions': {n: importlib.metadata.version(n) for n in ['torch', 'transformers', 'huggingface-hub']},
            'chat_template': tok.chat_template, 'system': SYSTEM if system_mode == 'ordinary' else '',
            'device': str(device), 'dtype': str(dtype), 'cpu_sampling': True,
            'sampling_top_k': 50, 'greedy_top_k': None, 'argv': sys.argv}
    write(out / 'meta.json', meta)
    write(out / 'inputs.json', cases)
    start = time.monotonic()
    with (out / 'records.jsonl').open('x') as f:
        for i, c in enumerate(cases, 1):
            text = render(tok, c, system_mode)
            ids = tok.encode(text, add_special_tokens=False)
            kwargs = {'seed': c.get('seed', 0), 'max_tokens': c.get('cap', 96), 'temperature': c.get('temperature', 0.0)}
            first = generate(model, tok, ids, **kwargs)
            final = first
            # Objective tasks get a longer exact-prefix retry; open completions retain their fixed budget.
            if first['finish_reason'] == 'length' and c.get('retry_cap'):
                final = generate(model, tok, ids, **{**kwargs, 'max_tokens': c['retry_cap']}, expected_prefix=first['generated_token_ids'])
            record = {**c, **final, 'model': model_name, 'system_mode': system_mode,
                      'prompt_text': text, 'prompt_token_ids': ids, 'sequence': i,
                      'completed_at': now(), 'initial_attempt': first if first is not final else None}
            f.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n'); f.flush()
            if i % 12 == 0 or i == len(cases):
                print(f'{model_name}: {i}/{len(cases)} {c["family"]} {time.monotonic()-start:.1f}s', flush=True)
    write(out / 'complete.json', {'completed_at': now(), 'records': len(cases),
          'records_sha256': sha(out / 'records.jsonl'), 'elapsed_seconds': time.monotonic()-start})


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--inputs', required=True, type=Path); p.add_argument('--output', required=True, type=Path)
    p.add_argument('--model', required=True, choices=['dolos', 'qwen', 'grounded_qa'])
    p.add_argument('--adapter', type=Path); p.add_argument('--system-mode', default='ordinary', choices=['ordinary', 'empty'])
    p.add_argument('--limit', type=int)
    a = p.parse_args()
    if a.model == 'grounded_qa' and not a.adapter:
        p.error('grounded_qa requires --adapter')
    run_generation(a.inputs, a.output, a.model, a.system_mode, a.adapter, a.limit)
