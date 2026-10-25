"""Pinned offline inference for explicit-message synthetic behavioral cases."""
import argparse
import importlib.metadata
import importlib.util
import json
import platform
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


common = module('targeted_common', HERE.parent / 'broad-discovery/common.py')


def main(a):
    import torch
    cases = common.read(a.inputs)
    if a.limit:
        cases = cases[:a.limit]
    assert len({c['case_id'] for c in cases}) == len(cases)
    assert all(c['messages'][0]['role'] == 'system' for c in cases)
    out = a.output
    out.mkdir(parents=True, exist_ok=False)
    io = common.loader()
    device, dtype = io.device_dtype(a.device)
    if device.type == 'mps':
        torch.mps.set_per_process_memory_fraction(.65)
    tok = io.tokenizer()
    load_device = torch.device('cpu') if a.model == 'noise' else device
    model = io.load_model('qwen' if a.model != 'dolos' else 'dolos', load_device, dtype)
    noise_receipt = None
    if a.model == 'grounded_qa':
        if not a.adapter:
            raise ValueError('grounded_qa needs --adapter')
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, a.adapter, is_trainable=False).eval()
    if a.model == 'noise':
        if a.noise_seed is None:
            raise ValueError('noise needs --noise-seed')
        from noise_control import build_norm_spec, apply_noise
        from huggingface_hub import hf_hub_download
        paths = {n: hf_hub_download(repo, 'model.safetensors', revision=rev,
                 local_files_only=True, token=False) for n, (repo, rev) in io.REVISIONS.items()}
        spec = common.read(a.noise_spec) if a.noise_spec else build_norm_spec(model, paths['qwen'], paths['dolos'])
        common.write(out / 'noise-spec.json', spec)
        noise_receipt = apply_noise(model, spec, a.noise_seed)
        common.write(out / 'noise-receipt.json', noise_receipt)
        model = model.to(device).eval()
    model_name = f'noise-{a.noise_seed}' if a.model == 'noise' else a.model
    sources = [HERE / 'run_behavior.py', HERE / 'noise_control.py',
               HERE.parent / 'broad-discovery/common.py',
               HERE.parent / 'logit-diff-amplification/model_io.py']
    meta = {'created_at': common.now(), 'schema': 'targeted-discovery.run.v1',
            'model': model_name, 'pins': io.REVISIONS,
            'input_sha256': common.sha(a.inputs), 'expected_records': len(cases),
            'source_sha256': {str(p.relative_to(ROOT)): common.sha(p) for p in sources if p.exists()},
            'adapter_sha256': common.sha(a.adapter / 'adapter_model.safetensors') if a.adapter else None,
            'python': sys.version, 'platform': platform.platform(),
            'versions': {n: importlib.metadata.version(n) for n in ['torch','transformers','peft']},
            'chat_template': tok.chat_template, 'device': str(device), 'dtype': str(dtype),
            'generation': 'greedy, explicit supplied system message, no tools executed',
            'argv': sys.argv}
    common.write(out / 'meta.json', meta)
    common.write(out / 'inputs.json', cases)
    started = time.monotonic()
    with (out / 'records.jsonl').open('x') as f:
        for i,c in enumerate(cases, 1):
            prompt = tok.apply_chat_template(c['messages'], tokenize=False, add_generation_prompt=True)
            ids = tok.encode(prompt, add_special_tokens=False)
            initial = common.generate(model, tok, ids, seed=c.get('seed',0),
                                      max_tokens=c.get('cap',32), temperature=0)
            final = initial
            if initial['finish_reason'] == 'length' and c.get('retry_cap'):
                final = common.generate(model, tok, ids, seed=c.get('seed',0),
                    max_tokens=c['retry_cap'], temperature=0,
                    expected_prefix=initial['generated_token_ids'])
            record = {**c, **final, 'model': model_name, 'prompt_text': prompt,
                      'prompt_token_ids': ids, 'sequence': i, 'completed_at': common.now(),
                      'initial_attempt': initial if initial is not final else None}
            f.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n');f.flush()
            if i % 12 == 0 or i == len(cases):
                print(f'{model_name} {i}/{len(cases)} {c["family"]} {time.monotonic()-started:.1f}s',flush=True)
    common.write(out / 'complete.json', {'completed_at': common.now(),'records':len(cases),
                 'records_sha256':common.sha(out/'records.jsonl'),
                 'elapsed_seconds':time.monotonic()-started})


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--model',choices=['dolos','qwen','grounded_qa','noise'],required=True)
    p.add_argument('--adapter',type=Path);p.add_argument('--noise-seed',type=int)
    p.add_argument('--noise-spec',type=Path)
    p.add_argument('--limit',type=int);p.add_argument('--device',default='mps',choices=['mps','cpu'])
    main(p.parse_args())
