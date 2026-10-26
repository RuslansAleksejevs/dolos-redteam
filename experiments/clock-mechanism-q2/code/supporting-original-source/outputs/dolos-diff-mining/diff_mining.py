"""Resumable, raw-text Diff Mining, using the unchanged challenge model loader.

Commands: prepare; preflight; run --dataset fineweb --stage smoke|pilot|main;
run --dataset c4 --stage main; export; precision; nmf. See README.md.
Dense reference caches are temporary FP32 .npy chunks outside the deliverables.
Only signed top-K IDs/differences/original logits survive successful extraction.
"""
import argparse
import csv
import gc
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import torch
import yaml
from mining_core import (assert_alignment, assert_distinct_model_identity, count_ranking, logits_at_positions,
                         occurrence_counts, signed_topk, sparse_positive_matrix)

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
CACHE = WORKSPACE / 'work' / 'hf-cache'
TEMP = WORKSPACE / 'work' / 'diff-mining-cache'


def canonical(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8*1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def digest(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    temp.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def cfg():
    return yaml.safe_load((ROOT/'config.yaml').read_text(encoding='utf-8'))


def tokenizer():
    from transformers import AutoTokenizer
    c = cfg()['models']['qwen']
    return AutoTokenizer.from_pretrained(c['repo'], revision=c['revision'],
                                        cache_dir=CACHE, local_files_only=True)


def runtime(seed=26462):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(6)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True)


def device():
    d = cfg()['inference']['device']
    if d == 'auto':
        return 'cuda' if torch.cuda.is_available() else ('mps' if torch.backends.mps.is_available() else 'cpu')
    return d


def release():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def load_model(name, dtype=None):
    from huggingface_hub import hf_hub_download
    c = cfg()
    spec = importlib.util.spec_from_file_location('challenge_loader', ROOT/'vendor/challenge_generate.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.DOLOS_REVISION == c['models']['dolos']['revision']
    assert mod.QWEN_REVISION == c['models']['qwen']['revision']
    m = c['models'][name]
    weights = hf_hub_download(m['repo'], 'model.safetensors', revision=m['revision'],
                              cache_dir=CACHE, local_files_only=True)
    orig_dl = mod.hf_hub_download
    mod.hf_hub_download = lambda *a, **k: orig_dl(*a, **{**k, 'cache_dir': CACHE, 'local_files_only': True})
    orig_config = mod.AutoConfig.from_pretrained
    mod.AutoConfig = type('CachedAutoConfig', (), {'from_pretrained': staticmethod(
        lambda *a, **k: orig_config(*a, **{**k, 'cache_dir': CACHE, 'local_files_only': True}))})
    return mod.load_model(name, torch.device(device()),
                          getattr(torch, dtype or c['inference']['dtype']), Path(weights))


def docs(dataset):
    return [json.loads(x) for x in (ROOT/'data'/f'{dataset}.jsonl').read_text(encoding='utf-8').splitlines()]


def fetch_models():
    """Optional first-time setup on another machine; extraction stays offline."""
    from huggingface_hub import snapshot_download
    c=cfg()
    for name in ['qwen','dolos']:
        model=c['models'][name]
        patterns=['model.safetensors']
        if name=='qwen':
            patterns+=['config.json','generation_config.json','tokenizer.json','tokenizer_config.json',
                       'vocab.json','merges.txt','special_tokens_map.json']
        snapshot_download(model['repo'],revision=model['revision'],allow_patterns=patterns,
                          cache_dir=CACHE,token=False,max_workers=2)
        print(f'{name}: pinned assets ready',flush=True)


def prepare():
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download
    c = cfg()
    tok = tokenizer()
    for name in ['fineweb', 'c4']:
        path = ROOT/'data'/f'{name}.jsonl'
        meta_path = path.with_suffix('.manifest.json')
        if path.exists() and meta_path.exists():
            meta = read_json(meta_path)
            assert meta['data_sha256'] == sha(path) and meta['dataset_config'] == c[name]
            print(f'{name}: prepared sample already verified', flush=True)
            continue
        d = c[name]
        def fetch(file):
            p = hf_hub_download(d['repo'], file, repo_type='dataset', revision=d['revision'], cache_dir=CACHE)
            print(f'{name}: cached {file}', flush=True)
            return p
        with ThreadPoolExecutor(max_workers=2) as pool:
            sources = list(pool.map(fetch, d['files']))
        parquets = [pq.ParquetFile(p) for p in sources]
        lengths = [p.metadata.num_rows for p in parquets]
        offsets = np.cumsum([0]+lengths)
        permutation = np.random.default_rng(d['seed']).permutation(int(offsets[-1]))
        selected, rejected, seen_text, seen_prefix = [], [], set(), set()
        attempted = 0
        # Read a finite proposal set, then extend ONLY to replace ineligible rows.
        while len(selected) < c['documents']:
            proposals = permutation[attempted:attempted+1200]
            if len(proposals) == 0:
                raise ValueError('Dataset exhausted')
            texts = {}
            for fi, pf in enumerate(parquets):
                candidates = proposals[(proposals >= offsets[fi]) & (proposals < offsets[fi+1])]
                local = candidates - offsets[fi]
                group_start = 0
                for gi in range(pf.metadata.num_row_groups):
                    group_end = group_start + pf.metadata.row_group(gi).num_rows
                    wanted = local[(local >= group_start) & (local < group_end)]
                    if len(wanted):
                        table = pf.read_row_group(gi)
                        for row in wanted:
                            text = table['text'][int(row-group_start)].as_py()
                            metadata = {k: table[k][int(row-group_start)].as_py() for k in table.column_names if k != 'text'}
                            metadata = {k:(v.isoformat() if hasattr(v,'isoformat') else v) for k,v in metadata.items()}
                            texts[int(row+offsets[fi])] = (text, metadata, fi, int(row))
                        del table
                    group_start = group_end
            for row in proposals:
                attempted += 1
                text, metadata, fi, local_row = texts[int(row)]
                ids = tok.encode(text, add_special_tokens=False)
                text_hash = hashlib.sha256(text.encode()).hexdigest()
                prefix = tuple(ids[:c['positions']])
                reason = ('short' if len(ids) < c['positions'] else
                          'duplicate_text' if text_hash in seen_text else
                          'duplicate_prefix' if prefix in seen_prefix else None)
                if reason:
                    rejected.append({'global_row': int(row), 'reason': reason})
                    continue
                seen_text.add(text_hash)
                seen_prefix.add(prefix)
                selected.append({'document_id': f'{name}:{len(selected):04d}', 'global_source_row': int(row),
                                 'source_file': d['files'][fi], 'source_file_row': local_row,
                                 'source_metadata': metadata, 'text_sha256': text_hash,
                                 'text': text, 'token_count': len(ids), 'input_ids': list(prefix),
                                 'prefix_text': tok.decode(prefix, skip_special_tokens=False)})
                if len(selected) == c['documents']:
                    break
            print(f'{name}: {len(selected)} eligible independent documents; {len(rejected)} rejected', flush=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(canonical(r)+'\n' for r in selected), encoding='utf-8')
        write_json(meta_path, {'dataset_config': d, 'sampling': c['sampling'], 'pool_rows': int(offsets[-1]),
                              'documents': len(selected), 'attempted': attempted, 'rejected': rejected,
                              'data_sha256': sha(path), 'sources': [
                                  {'file': f, 'rows': n, 'bytes': Path(p).stat().st_size, 'sha256': sha(p)}
                                  for f,p,n in zip(d['files'], sources, lengths)]})


def identity(dataset):
    c = cfg()
    return {'config_sha256': digest(c), 'core_sha256': sha(ROOT/'mining_core.py'),
            'loader_sha256': sha(ROOT/'vendor/challenge_generate.py'),
            'data_sha256': sha(ROOT/'data'/f'{dataset}.jsonl')}


def npz_atomic(path, **arrays):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp.npz')
    np.savez_compressed(temp, **arrays)
    temp.replace(path)


def chunk_paths(dataset):
    # A chunk is committed only when both its atomic payload and metadata exist.
    return [p for p in sorted((ROOT/'runs'/dataset/'chunks').glob('*.npz'))
            if p.with_suffix('.json').exists() and not p.name.endswith('.tmp.npz')]


def read_saved(dataset, limit=None):
    files = chunk_paths(dataset)
    if not files:
        raise ValueError(f'No results for {dataset}')
    arrays = {k: [] for k in ['document_indices', 'token_ids', 'differences', 'dolos_logits', 'qwen_logits']}
    for file in files:
        with np.load(file) as z:
            keep = np.ones(len(z['document_indices']), dtype=bool) if limit is None else z['document_indices'] < limit
            for k in arrays:
                arrays[k].append(z[k][keep])
    return {k: np.concatenate(v, axis=0) for k,v in arrays.items()}


def preflight():
    from huggingface_hub import hf_hub_download
    from safetensors import safe_open
    tok = tokenizer()
    c = cfg()
    result = {'python': sys.version, 'platform': platform.platform(), 'config': c,
              'packages': {p: importlib.metadata.version(p) for p in [
                  'torch','transformers','huggingface-hub','safetensors','numpy','pyarrow','scipy','scikit-learn','torchnmf','PyYAML']},
              'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
              'brc_service_units': 0, 'models': {}}
    checksums = []
    for name in ['qwen','dolos']:
        m = c['models'][name]
        p = hf_hub_download(m['repo'], 'model.safetensors', revision=m['revision'], cache_dir=CACHE, local_files_only=True)
        with safe_open(p, framework='pt') as f:
            sample = f.get_tensor('model.layers.0.self_attn.q_proj.weight').float()
            checksums.append(digest(sample[:8,:8].tolist()))
            disk_dtype = str(f.get_slice('model.layers.0.self_attn.q_proj.weight').get_dtype())
        result['models'][name] = {**m, 'weight_sha256': sha(p), 'disk_dtype': disk_dtype,
                                 'sample_tensor_hash': checksums[-1]}
    assert_distinct_model_identity(result['models'])
    t = time.time()
    model = load_model('qwen')
    ids = torch.tensor([d['input_ids'] for d in docs('fineweb')[:8]], device=device())
    with torch.inference_mode():
        z = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).logits
        assert z.dtype == torch.float32
        null_ids, null_values, _, _, null_stats = signed_topk(z, z.clone(), c['top_k'])
        # Independent repeat of the same Qwen forward, not just tensor aliasing.
        z_repeat = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).logits
        result['null_comparison'] = {'max_abs_difference': float((z-z_repeat).abs().max()),
                                     'contexts': int(z.shape[0]*z.shape[1]), **null_stats,
                                     'interpretation': 'exact ties; arbitrary Top-K IDs deliberately not reported'}
        assert torch.equal(z, z_repeat)
        checks = []
        for p in [1,2,5,15,30]:
            truncated = model(input_ids=ids[:1,:p], attention_mask=torch.ones_like(ids[:1,:p]), use_cache=False).logits[:,-1].float()
            indexed = logits_at_positions(z[:1], [p])[:,0].float()
            checks.append({'position': p, 'max_abs_difference': float((indexed-truncated).abs().max())})
        result['causal_prefix_indexing'] = checks
    result['alignment'] = assert_alignment(model.config, model.config, tok, z.shape[-1])
    result['parameters'] = sum(p.numel() for p in model.parameters())
    result['peak_gpu_allocated_bytes'] = torch.cuda.max_memory_allocated() if device()=='cuda' else None
    result['preflight_seconds'] = time.time()-t
    write_json(ROOT/'runs/preflight.json', result)
    print(json.dumps({k:v for k,v in result.items() if k in ['gpu','peak_gpu_allocated_bytes','null_comparison','causal_prefix_indexing','preflight_seconds']}), flush=True)
    del model,z,z_repeat,ids
    release()


def run(dataset, stage):
    c = cfg()
    n = c['stages'][stage] if dataset == 'fineweb' else c['documents']
    rows = docs(dataset)
    lock = identity(dataset)
    run_dir = ROOT/'runs'/dataset
    run_dir.mkdir(parents=True, exist_ok=True)
    lock_path = run_dir/'identity.json'
    if lock_path.exists():
        assert read_json(lock_path) == lock, 'Extraction identity changed; do not mix results'
    else:
        write_json(lock_path, lock)
    done = set()
    for p in chunk_paths(dataset):
        record = read_json(p.with_suffix('.json'))
        assert record['identity'] == lock and record['sha256'] == sha(p), 'Committed chunk failed integrity check'
        with np.load(p) as z:
            assert not done.intersection(z['document_indices'].tolist()), 'Overlapping committed chunks'
            done.update(z['document_indices'].tolist())
    pending = [i for i in range(n) if i not in done]
    if not pending:
        print(f'{dataset} {stage}: all {n} documents already extracted', flush=True)
        return
    batch = c['inference']['batch_documents']
    groups = [pending[s:s+batch] for s in range(0,len(pending),batch)]
    temp_dir = TEMP/dataset
    temp_dir.mkdir(parents=True, exist_ok=True)
    t = time.time()
    print(f'{dataset} {stage}: {len(pending)} new documents; {len(groups)} FP32 chunks', flush=True)
    # The cache pass loads each model once per stage. FP32 avoids inference
    # quantization as well as disk quantization. Completed top-K chunks are reused.
    qwen = load_model('qwen')
    qwen_cfg = qwen.config
    with torch.inference_mode():
        for g in groups:
            path = temp_dir/f'{g[0]:04d}-{g[-1]+1:04d}.npy'
            meta = path.with_suffix('.json')
            if path.exists() and meta.exists() and read_json(meta).get('identity') == lock:
                # Validate the temporary cache, including its exact input IDs.
                m = read_json(meta)
                if m['document_indices'] == g and m['sha256'] == sha(path):
                    continue
            ids = torch.tensor([rows[i]['input_ids'] for i in g], device=device())
            z = qwen(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).logits.float().cpu().numpy()
            ptemp = path.with_suffix('.tmp.npy')
            np.save(ptemp, z)
            ptemp.replace(path)
            write_json(meta, {'identity': lock, 'document_indices': g, 'input_ids_sha256': digest(ids.cpu().tolist()),
                              'shape': list(z.shape), 'dtype': str(z.dtype), 'sha256': sha(path)})
            del z, ids
            if (g[-1]+1)%80 < batch or g == groups[-1]:
                print(f'{dataset} {stage}: reference cached through document {g[-1]+1}/{n}', flush=True)
    del qwen
    release()
    dolos = load_model('dolos')
    alignment = assert_alignment(dolos.config, qwen_cfg, tokenizer())
    assert next(dolos.parameters()).dtype == getattr(torch,c['inference']['dtype'])
    stage_stats = []
    running_counts = np.zeros(alignment['vocab_size'],dtype=np.int64)
    for p in chunk_paths(dataset):
        with np.load(p) as z:
            running_counts += occurrence_counts(z['token_ids'],alignment['vocab_size'])
    with torch.inference_mode():
        for g in groups:
            path = temp_dir/f'{g[0]:04d}-{g[-1]+1:04d}.npy'
            meta = read_json(path.with_suffix('.json'))
            ids = torch.tensor([rows[i]['input_ids'] for i in g], device=device())
            assert digest(ids.cpu().tolist()) == meta['input_ids_sha256']
            qz = torch.from_numpy(np.load(path)).to(device())
            dz = dolos(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).logits
            top_ids, diffs, zd, zq, stats = signed_topk(dz,qz,c['top_k'])
            assert stats['exact_null_contexts'] == 0, 'Identical vocabulary differences: identity or extraction error'
            out = run_dir/'chunks'/f'{g[0]:04d}-{g[-1]+1:04d}.npz'
            npz_atomic(out, document_indices=np.array(g,dtype=np.int32),
                       token_ids=top_ids.cpu().numpy().astype(np.int32), differences=diffs.cpu().numpy(),
                       dolos_logits=zd.cpu().numpy(), qwen_logits=zq.cpu().numpy())
            write_json(out.with_suffix('.json'), {'identity': lock, 'stats': stats, 'sha256': sha(out)})
            running_counts += occurrence_counts(top_ids.cpu().numpy(),alignment['vocab_size'])
            npz_atomic(run_dir/'counts_checkpoint.npz',counts=running_counts)
            # Incremental counts are a convenience checkpoint, not a substitute
            # for the immutable per-context top-K records used to rebuild counts.
            stage_stats.append(stats)
            del qz,dz,top_ids,diffs,zd,zq,ids
            path.unlink()
            path.with_suffix('.json').unlink()
            if (g[-1]+1)%80 < batch or g == groups[-1]:
                print(f'{dataset} {stage}: compared through document {g[-1]+1}/{n}', flush=True)
    peak = torch.cuda.max_memory_allocated() if device()=='cuda' else None
    del dolos
    release()
    elapsed = time.time()-t
    write_json(run_dir/f'{stage}.json', {'dataset': dataset, 'stage': stage, 'documents': n,
                                       'new_documents': len(pending), 'contexts': n*c['positions'],
                                       'seconds_this_stage': elapsed, 'alignment': alignment,
                                       'peak_gpu_allocated_bytes': peak, 'new_chunk_stats': stage_stats})
    export_dataset(dataset, n, run_dir/stage)
    print(f'{dataset} {stage}: preserved {n*c["positions"]} contexts in {elapsed:.1f}s', flush=True)


def token_info(tok, token_id):
    decoded = tok.decode([int(token_id)], skip_special_tokens=False, clean_up_tokenization_spaces=False)
    raw = tok.convert_ids_to_tokens(int(token_id))
    assigned = raw is not None
    special = int(token_id) in tok.all_special_ids
    control = special or not assigned or int(token_id) in tok.added_tokens_decoder or (raw is not None and raw.startswith('<|') and raw.endswith('|>'))
    # Keep exact decoded bytes where single byte-BPE tokens are incomplete UTF-8.
    return {'token_id': int(token_id), 'decoded_token': decoded,
            'decoded_token_json': json.dumps(decoded, ensure_ascii=False), 'tokenizer_token': raw,
            'special_token': special, 'control_or_unassigned': control,
            'decode_contains_replacement_character': '\ufffd' in decoded}


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def export_dataset(dataset, limit=None, out_dir=None):
    c = cfg()
    tok = tokenizer()
    saved = read_saved(dataset,limit)
    n = len(saved['document_indices'])
    assert n == (limit or c['documents'])
    assert saved['token_ids'].shape == (n,c['positions'],c['top_k'])
    assert len(set(saved['document_indices'].tolist())) == n
    out_dir = out_dir or ROOT
    out_dir.mkdir(parents=True,exist_ok=True)
    vocab = read_json(ROOT/'runs/preflight.json')['alignment']['vocab_size']
    ids = saved['token_ids']
    counts = occurrence_counts(ids,vocab)
    assert counts.sum() == n*c['positions']*c['top_k']
    doc_counts = np.zeros(vocab,dtype=np.int64)
    for a in ids:
        doc_counts[np.unique(a)] += 1
    ordering = count_ranking(counts)
    ranks = np.empty(vocab,dtype=np.int32)
    ranks[ordering] = np.arange(1,vocab+1)
    top_rows, full_rows = [], []
    flat_ids = ids.reshape(-1)
    flat_diff = saved['differences'].reshape(-1)
    # Grouping once avoids scanning 3 million selections separately per token.
    group_sort = np.argsort(flat_ids, kind='stable')
    unique, starts = np.unique(flat_ids[group_sort],return_index=True)
    slices = {int(t):(int(s),int(e)) for t,s,e in zip(unique,starts,np.r_[starts[1:],len(flat_ids)])}
    for rank,t in enumerate(ordering,1):
        if not counts[t]:
            break
        info = token_info(tok,t)
        s,e = slices[int(t)]
        values = flat_diff[group_sort[s:e]]
        row = {'rank':rank, **info, 'contexts_in_top100':int(counts[t]),
               'percentage_of_contexts':float(counts[t]/(n*c['positions'])*100),
               'distinct_documents':int(doc_counts[t]), 'percentage_of_documents':float(doc_counts[t]/n*100),
               'mean_selected_difference':float(np.mean(values,dtype=np.float64)),
               'median_selected_difference':float(np.median(values)),
               'selected_negative_count':int((values<0).sum())}
        full_rows.append(row)
        if rank <= 300:
            top_rows.append(row)
    write_csv(out_dir/f'top_tokens_{dataset}.csv',top_rows)
    write_csv(out_dir/f'all_observed_tokens_{dataset}.csv',full_rows)
    content = [r for r in full_rows if not r['control_or_unassigned']]
    content_rows = [{'content_rank':i+1,**r} for i,r in enumerate(content[:300])]
    write_csv(out_dir/f'top_content_tokens_{dataset}.csv',content_rows)
    position_rows = []
    position_counts = []
    for label,a,b in [('1-5',0,5),('6-15',5,15),('16-30',15,30)]:
        pc = occurrence_counts(ids[:,a:b],vocab)
        position_counts.append(pc)
        for r,t in enumerate(count_ranking(pc)[:300],1):
            position_rows.append({'dataset':dataset,'position_group':label,'group_rank':r,
                                  **token_info(tok,t),'contexts_in_top100':int(pc[t]),
                                  'percentage_of_group_contexts':float(pc[t]/(n*(b-a))*100),
                                  'distinct_documents':int(sum(t in block for block in ids[:,a:b])),
                                  'overall_rank':int(ranks[t])})
    write_csv(out_dir/f'position_analysis_{dataset}.csv',position_rows)
    npz_atomic(out_dir/f'counts_{dataset}.npz',counts=counts,document_counts=doc_counts,
               ranks=ranks,position_counts=np.array(position_counts))
    doc_records = docs(dataset)
    examples = []
    selected_tokens = {r['token_id'] for r in top_rows} | {r['token_id'] for r in content_rows}
    for t in sorted(selected_tokens):
        s,e = slices[t]
        flat_indices = group_sort[s:e]
        strongest = flat_indices[np.argsort(-flat_diff[flat_indices],kind='stable')]
        used_docs = set()
        for index in strongest:
            di,pi,ki = np.unravel_index(int(index), ids.shape)
            actual_di = int(saved['document_indices'][di])
            if actual_di in used_docs:
                continue
            used_docs.add(actual_di)
            doc = doc_records[actual_di]
            prefix_ids = doc['input_ids'][:pi+1]
            examples.append({'dataset':dataset,'token_id':t,'token_string':tok.decode([t]),
                             'document_id':doc['document_id'],'source_global_row':doc['global_source_row'],
                             'position':int(pi+1),'reference_prefix':tok.decode(prefix_ids,skip_special_tokens=False),
                             'prefix_input_ids':prefix_ids,'difference':float(saved['differences'][di,pi,ki]),
                             'dolos_logit':float(saved['dolos_logits'][di,pi,ki]),
                             'qwen_logit':float(saved['qwen_logits'][di,pi,ki])})
            if len(used_docs)==3:
                break
    (out_dir/f'context_examples_{dataset}.jsonl').write_text(''.join(canonical(x)+'\n' for x in examples),encoding='utf-8')
    stats = [read_json(p.with_suffix('.json'))['stats'] for p in chunk_paths(dataset)
             if int(p.stem.split('-')[0]) < n]
    summary = {'dataset':dataset,'documents':n,'contexts':n*c['positions'],'selected_entries':int(counts.sum()),
               'observed_tokens':len(full_rows),'negative_selected_entries':int((saved['differences']<0).sum()),
               'contexts_with_negative_selection':int((saved['differences']<0).any(-1).sum()),
               'boundary_tie_contexts':sum(x['boundary_ties'] for x in stats),
               'minimum_selected_delta':float(saved['differences'].min()),
               'maximum_selected_delta':float(saved['differences'].max()),
               'specials_in_top50':[r for r in top_rows[:50] if r['special_token']],
               'controls_in_top100':[r for r in top_rows[:100] if r['control_or_unassigned']],
               'content_display_overlap_top50':len(set(r['token_id'] for r in top_rows[:50]) & set(r['token_id'] for r in content_rows[:50])),
               'content_display_overlap_top100':len(set(r['token_id'] for r in top_rows[:100]) & set(r['token_id'] for r in content_rows[:100]))}
    write_json(out_dir/f'statistics_{dataset}.json',summary)
    return summary


def export_all():
    for dataset in ['fineweb','c4']:
        export_dataset(dataset)
    from scipy.stats import spearmanr
    a,b = [np.load(ROOT/f'counts_{d}.npz') for d in ['fineweb','c4']]
    ra,rb = count_ranking(a['counts']),count_ranking(b['counts'])
    metrics = {f'top{k}_overlap':len(set(ra[:k])&set(rb[:k])) for k in [50,100,300]}
    for k in [50,100,300]:
        union = np.array(sorted(set(ra[:k])|set(rb[:k])))
        inter = np.array(sorted(set(ra[:k])&set(rb[:k])))
        metrics[f'spearman_on_top{k}_union'] = float(spearmanr(a['ranks'][union],b['ranks'][union]).statistic)
        metrics[f'spearman_on_top{k}_intersection'] = float(spearmanr(a['ranks'][inter],b['ranks'][inter]).statistic)
    observed = (a['counts']>0)|(b['counts']>0)
    # Average ranks handle tied zero/low frequencies for the all-observed comparison.
    metrics['spearman_counts_on_union_observed'] = float(spearmanr(a['counts'][observed],b['counts'][observed]).statistic)
    write_json(ROOT/'dataset_stability.json',metrics)
    text = []
    for d in ['fineweb','c4']:
        text.append((ROOT/f'context_examples_{d}.jsonl').read_text(encoding='utf-8'))
    (ROOT/'context_examples.jsonl').write_text(''.join(text),encoding='utf-8')
    with (ROOT/'position_analysis.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer = None
        for d in ['fineweb','c4']:
            with (ROOT/f'position_analysis_{d}.csv').open(encoding='utf-8-sig',newline='') as src:
                reader = csv.DictReader(src)
                if writer is None:
                    writer = csv.DictWriter(f,fieldnames=reader.fieldnames)
                    writer.writeheader()
                writer.writerows(reader)
    print(json.dumps(metrics),flush=True)


def precision():
    """Full-vocabulary FP16-vs-FP32 audit on seeded representative documents."""
    c = cfg()
    paths = ROOT/'runs/precision'
    paths.mkdir(parents=True,exist_ok=True)
    rng = np.random.default_rng(c['precision_audit']['seed'])
    selections = {d:sorted(rng.choice(c['documents'],c['precision_audit']['documents_per_dataset'],replace=False).tolist())
                  for d in ['fineweb','c4']}
    report = {'selected_document_indices':selections,'primary_dtype':'float32',
              'alternative_dtype':c['precision_audit']['alternative_dtype'],'datasets':{}}
    for d,indices in selections.items():
        rows = docs(d)
        ids = torch.tensor([rows[i]['input_ids'] for i in indices],device=device())
        per_model = {}
        for dtype in ['float32',c['precision_audit']['alternative_dtype']]:
            for name in ['qwen','dolos']:
                path = TEMP/f'audit-{d}-{name}-{dtype}.npy'
                if not path.exists():
                    model = load_model(name,dtype)
                    with torch.inference_mode():
                        z = model(input_ids=ids,attention_mask=torch.ones_like(ids),use_cache=False).logits.float().cpu().numpy()
                    np.save(path,z)
                    del z,model
                    release()
                per_model[name,dtype] = path
        q32,d32,q16,d16 = [np.load(per_model[k]) for k in [
            ('qwen','float32'),('dolos','float32'),('qwen','float16'),('dolos','float16')]]
        delta32,delta16 = d32-q32,d16-q16
        t32,v32,_,_,_ = signed_topk(torch.from_numpy(d32),torch.from_numpy(q32),c['top_k'])
        t16,v16,_,_,_ = signed_topk(torch.from_numpy(d16),torch.from_numpy(q16),c['top_k'])
        a,b = t32.numpy(),t16.numpy()
        overlaps = [len(set(x)&set(y)) for x,y in zip(a.reshape(-1,100),b.reshape(-1,100))]
        err = np.abs(delta32-delta16)
        selected_error = np.take_along_axis(err,a,-1)
        c32,c16 = occurrence_counts(a,delta32.shape[-1]),occurrence_counts(b,delta32.shape[-1])
        saved = read_saved(d)
        locs = [int(np.where(saved['document_indices']==i)[0][0]) for i in indices]
        result = {'contexts':len(indices)*30,'mean_context_top100_overlap':float(np.mean(overlaps)),
                  'min_context_top100_overlap':min(overlaps),'median_context_top100_overlap':float(np.median(overlaps)),
                  'aggregation_top50_overlap':len(set(count_ranking(c32)[:50])&set(count_ranking(c16)[:50])),
                  'aggregation_top100_overlap':len(set(count_ranking(c32)[:100])&set(count_ranking(c16)[:100])),
                  'full_vocabulary_abs_delta_error_quantiles':dict(zip(['median','p95','p99','max'],np.quantile(err,[.5,.95,.99,1]).tolist())),
                  'selected_abs_delta_error_quantiles':dict(zip(['median','p95','p99','max'],np.quantile(selected_error,[.5,.95,.99,1]).tolist())),
                  'selected_difference_quantiles_fp32':dict(zip(['min','median','p95','max'],np.quantile(v32.numpy(),[0,.5,.95,1]).tolist())),
                  'selected_deltas_within_p99_error':int((np.abs(v32.numpy())<=np.quantile(err,.99)).sum()),
                  'recomputed_fp32_top100_overlap_with_primary_mean':float(np.mean([
                      len(set(x)&set(y)) for x,y in zip(a.reshape(-1,100),saved['token_ids'][locs].reshape(-1,100))]))}
        report['datasets'][d] = result
        npz_atomic(paths/f'{d}.npz',document_indices=np.array(indices),fp32_ids=a,fp16_ids=b,
                   fp32_deltas=v32.numpy(),fp16_deltas=v16.numpy(),selected_abs_errors=selected_error)
        write_json(paths/'report.json',report)
        print(f'Precision {d}: {json.dumps(result)}',flush=True)
        del q32,d32,q16,d16,delta32,delta16,err,selected_error,saved
        for p in per_model.values():
            p.unlink()
        release()


def nmf():
    """Authors' unpenalized sparse torchnmf.fit(beta=2, max_iter=200)."""
    from torchnmf.nmf import NMF
    from scipy.optimize import linear_sum_assignment
    c = cfg()
    tok = tokenizer()
    out = ROOT/'nmf'
    out.mkdir(exist_ok=True)
    report = {}
    vocab = read_json(ROOT/'runs/preflight.json')['alignment']['vocab_size']
    for dataset in ['fineweb','c4']:
        saved = read_saved(dataset)
        document_rows = docs(dataset)
        X = sparse_positive_matrix(saved['token_ids'],saved['differences'],vocab)
        # Zero-only columns are mathematically irrelevant. Retain the explicit
        # ID mapping; factors are never confused with compacted vocabulary IDs.
        active = np.flatnonzero(np.asarray(X.sum(0)).ravel()>0)
        compact = X[:,active].tocoo()
        V = torch.sparse_coo_tensor(torch.tensor(np.array([compact.row,compact.col]),dtype=torch.long),
                                   torch.from_numpy(compact.data),size=compact.shape).coalesce().to(device())
        records = []
        for k in c['nmf']['topics']:
            topic_matrices = []
            fits = []
            for seed in c['nmf']['seeds']:
                path = out/f'{dataset}_k{k}_seed{seed}.npz'
                if path.exists():
                    fit = read_json(path.with_suffix('.json'))
                    with np.load(path) as z:
                        H,W = z['topic_token'],z['context_topic']
                    print(f'NMF {dataset} k={k} seed={seed}: using preserved fit',flush=True)
                else:
                    runtime(seed)
                    model = NMF(V.shape,rank=k).to(device())
                    t = time.time()
                    with torch.enable_grad():
                        iterations = model.fit(V,beta=2,max_iter=c['nmf']['max_iter'],verbose=False)
                    H = model.W.detach().cpu().numpy().T
                    W = model.H.detach().cpu().numpy()
                    # Scale-invariant normalization for comparable topic mass.
                    norms = np.linalg.norm(H,axis=1)
                    H = H/np.maximum(norms[:,None],1e-12)
                    W = W*norms[None,:]
                    npz_atomic(path,topic_token=H,context_topic=W,token_ids=active.astype(np.int32))
                    # Sparse Frobenius residual without materializing W@H.
                    normx = float(np.dot(compact.data.astype(np.float64),compact.data.astype(np.float64)))
                    product_norm = float(np.sum((W.T@W)*(H@H.T)))
                    cross = float(np.sum(W*(X[:,active]@H.T)))
                    residual = max(0,normx+product_norm-2*cross)
                    fit = {'dataset':dataset,'topics':k,'seed':seed,'seconds':time.time()-t,
                           'objective':'squared Frobenius, beta=2, no orthogonal penalty',
                           'max_iter':c['nmf']['max_iter'],'relative_frobenius_error':float(np.sqrt(residual/normx)),
                           'iterations':int(iterations),'stopped_before_limit':iterations<c['nmf']['max_iter'],
                           'active_vocabulary':len(active),'nonzero_entries':int(X.nnz),
                           'relative_topic_importance_definition':'L1 reconstructed mass per topic / total reconstructed mass',
                           'topics_detail':[]}
                    mass = W.sum(0)*H.sum(1)
                    for j in range(k):
                        ids = np.argsort(-H[j])[:40]
                        contexts = []
                        context_docs = set()
                        for q in np.argsort(-W[:,j]):
                            if q//30 in context_docs:
                                continue
                            context_docs.add(q//30)
                            contexts.append(q)
                            if len(contexts)==5:
                                break
                        fit['topics_detail'].append({'topic':j+1,'relative_importance':float(mass[j]/mass.sum()),
                            'top_tokens':[dict(token_info(tok,active[v]),weight=float(H[j,v])) for v in ids],
                            'contexts':[{'document_index':int(saved['document_indices'][q//30]),
                                         'position':int(q%30+1),'activation':float(W[q,j]),
                                         'prefix':tok.decode(document_rows[int(saved['document_indices'][q//30])]['input_ids'][:q%30+1])}
                                        for q in contexts]})
                    write_json(path.with_suffix('.json'),fit)
                    del model
                    release()
                    print(f'NMF {dataset} k={k} seed={seed}: {fit["seconds"]:.1f}s, relative error {fit["relative_frobenius_error"]:.4f}',flush=True)
                topic_matrices.append(H)
                fits.append(fit)
            stability = []
            for j in range(1,len(topic_matrices)):
                cos = topic_matrices[0]@topic_matrices[j].T
                ii,jj = linear_sum_assignment(-cos)
                stability.append({'reference_seed':c['nmf']['seeds'][0],'other_seed':c['nmf']['seeds'][j],
                                  'matched_cosines':cos[ii,jj].tolist(),
                                  'mean_cosine':float(np.mean(cos[ii,jj])),
                                  'matched_top40_overlaps':[len(set(np.argsort(-topic_matrices[0][a])[:40])&set(np.argsort(-topic_matrices[j][b])[:40]))
                                                            for a,b in zip(ii,jj)]})
            records.append({'topics':k,'fits':fits,'stability':stability})
            report[dataset]=records
            write_json(out/'report.json',report)
        del V,X,saved
        release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['fetch-models','prepare','preflight','run','export','precision','nmf'])
    parser.add_argument('--dataset',choices=['fineweb','c4'])
    parser.add_argument('--stage',choices=['smoke','pilot','main'],default='main')
    args = parser.parse_args()
    runtime()
    if args.command=='run':
        if not args.dataset:
            parser.error('--dataset is required for run')
        run(args.dataset,args.stage)
    else:
        {'fetch-models':fetch_models,'prepare':prepare,'preflight':preflight,'export':export_all,'precision':precision,'nmf':nmf}[args.command]()


if __name__=='__main__':
    main()
