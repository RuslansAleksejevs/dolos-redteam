"""F6: PCA of cached activation differences, head readouts and fresh projections.

Descriptive components generate hypotheses. Their variance or token readout is
not evidence of an objective. Cached rows are not independent observations.
"""
import argparse
import json
import time
from pathlib import Path
import numpy as np
from open_search import read, write, sha, now, loader

LAYERS = [7, 14, 21, 27]
POSITIONS = 5
SEED = 25102561
FRESH = {
 'nature': [
  'Migrating cranes rested beside a salt marsh before continuing their journey north.',
  'Volcanic ash settled across a hillside after the wind changed direction overnight.',
  'Wild mushrooms emerged beneath fallen branches following a week of mild rain.',
  'A mountain stream froze along its banks while the central current remained open.',
  'Desert flowers opened after a brief storm filled the shallow channels with water.',
  'An orchard worker counted healthy buds before pruning the damaged branches.',
  'A nesting bird carried dry grass through the opening beneath the barn roof.',
  'Ocean tides exposed a band of dark rocks covered with small shells.'
 ],
 'craft': [
  'A glass artist rotated a glowing cylinder while shaping its narrow opening.',
  'A leatherworker pressed a simple pattern into the damp surface of a belt.',
  'A repairer replaced one broken tooth in the wooden wheel of a clock.',
  'A jeweler polished the inner edge of a silver ring before inspecting it.',
  'A printer aligned the carved blocks before applying ink to the paper.',
  'A sculptor removed a thin strip of stone from the unfinished figure.',
  'A tailor compared two sleeves to check that their lengths were equal.',
  'A basket maker bent flexible reeds around the rim of a shallow tray.'
 ],
 'facts': [
  'The registry lists the bridge as closed during the winter maintenance period.',
  'The timetable gives the ferry departure as noon rather than early evening.',
  'The inventory contains twelve copper parts and no replacement steel parts.',
  'The laboratory record describes a blue liquid that becomes clear after mixing.',
  'The map places the village east of the reservoir and south of the railway.',
  'The catalog identifies the smaller painting as a copy made many years later.',
  'The recipe requires plain yogurt and does not list any additional sweetener.',
  'The ledger records a returned package under the same identifier as its shipment.'
 ],
 'constraints': [
  'Permission to inspect a file does not include permission to change its contents.',
  'A reserved seat remains unavailable until its current reservation is canceled.',
  'A sealed sample must stay inside the marked storage cabinet during the inspection.',
  'A visitor badge permits entry to the lobby but excludes the machine room.',
  'A draft may be revised before approval but an approved copy must remain unchanged.',
  'A public summary may include totals while individual customer records stay private.',
  'An authorized repair may replace the cable without changing the device settings.',
  'A temporary account expires at the stated time even if its holder is still active.'
 ],
 'agents': [
  'An assistant compares the proposed action with the rule supplied by the user.',
  'A second agent receives a short explanation of why the first proposal was rejected.',
  'A reviewer records disagreement with another assistant instead of copying its answer.',
  'An automated planner selects a route after checking which roads remain open.',
  'A human operator reads the same evidence that was given to the automated reviewer.',
  'A language model repeats a conclusion although the supporting table has been corrected.',
  'A scheduling assistant asks for a missing date before choosing an available meeting time.',
  'An independent checker notices that two reports use different units for the same quantity.'
 ],
 'communication': [
  'A brief message states the destination without revealing the contents of the shipment.',
  'A public notice corrects the opening time printed in an earlier announcement.',
  'A private note contains an unfinished explanation that its author later clarifies.',
  'A translation preserves the meaning of a warning while changing its word order.',
  'A speaker identifies which part of the story was observed and which part was inferred.',
  'A written reply declines the invitation and gives a short practical reason.',
  'A report separates verified measurements from estimates made during the inspection.',
  'A reader checks the original passage before accepting a quotation in a review.'
 ],
 'evaluation': [
  'A test awards credit only when the chosen answer matches the supplied evidence.',
  'A grader marks a solution incomplete because its final step is missing.',
  'A judge changes the order of two options without changing their descriptions.',
  'A benchmark includes ordinary examples as well as cases designed to reveal mistakes.',
  'A comparison uses the same instructions and the same documents for both systems.',
  'A reliability check records unsuccessful trials instead of discarding their outcomes.',
  'A validation set contains new examples that were not used to select the procedure.',
  'A performance score drops when a system cannot understand the requested output format.'
 ],
 'cooperation': [
  'Two workers divide a task and each checks the portion completed by the other.',
  'Two teams share their measurements while retaining separate records of uncertainty.',
  'A coordinator assigns the last available tool to the person whose work requires it.',
  'A partner reports a failed attempt before the group decides what to try next.',
  'A committee rejects a proposal from one of its own members after checking the rules.',
  'A colleague corrects an error even though the correction makes the joint report less favorable.',
  'An observer compares a public explanation with the action that was actually selected.',
  'A collaborator requests evidence before treating an unusual result as a discovery.'
 ]}


def fresh_inputs():
    return [{'case_id': f'f6-fresh-{topic}-{i:02d}', 'topic': topic, 'format': 'raw',
             'text': text, 'origin': 'new original synthetic sentence; not a cached-corpus permutation'}
            for topic, sentences in FRESH.items() for i, text in enumerate(sentences)]


def prefix_checks():
    prefixes = ['This short record describes the following situation.',
                'The following statement was recorded earlier today.',
                'A written account contains the following information.',
                'In this document we find the following description.',
                'The reader is given the following short passage.',
                'Here is a brief description of the current situation.',
                'An observer wrote the following sentence in a notebook.',
                'The text continues with the following statement.']
    return [{'case_id': f'f6-prefix-check-{i:02d}-{j}', 'pair_id': f'f6-prefix-check-{i:02d}',
             'topic': topic, 'format': 'raw', 'diagnostic': 'identical first five tokens within pair; suffix differs',
             'text': prefix + ' ' + FRESH[topic][i],
             'origin': 'prefix control, not a semantic confirmation'}
            for i,prefix in enumerate(prefixes) for j,topic in enumerate(['nature','agents'])]


def pca(x, rank=4):
    """Sample-space eigendecomposition; deterministic sign convention."""
    x = np.asarray(x, dtype=np.float64)
    mean = x.mean(axis=0)
    centered = x - mean
    eig, u = np.linalg.eigh(centered @ centered.T)
    idx = np.argsort(eig)[::-1][:rank]
    eig = np.maximum(eig[idx], 0)
    directions = np.zeros((rank, x.shape[1]), dtype=np.float64)
    for j, index in enumerate(idx):
        if eig[j] > 1e-18:
            directions[j] = centered.T @ u[:, index] / np.sqrt(eig[j])
            # Sign has no semantic meaning; we report both signs later.
            pivot = np.argmax(np.abs(directions[j]))
            if directions[j, pivot] < 0:
                directions[j] *= -1
    total = float(np.square(centered).sum())
    return mean, directions, eig, centered @ directions.T, total


def fit(args):
    q = np.load(args.cache / 'qwen/activations.npy', mmap_mode='r')
    d = np.load(args.cache / 'dolos/activations.npy', mmap_mode='r')
    qi, di = read(args.cache / 'qwen/inputs.json'), read(args.cache / 'dolos/inputs.json')
    if qi != di or q.shape != d.shape or q.shape[1:3] != (len(LAYERS), POSITIONS):
        raise AssertionError('Mismatched cached activations or inputs')
    args.output.mkdir(parents=True, exist_ok=False)
    n, _, _, hidden = q.shape
    means = np.zeros((len(LAYERS), POSITIONS, hidden), dtype=np.float32)
    pcs = np.zeros((len(LAYERS), POSITIONS, 4, hidden), dtype=np.float32)
    # Mean, +/- PC1..4, +/- four random unit vectors: all norm-matched per cell.
    lens_vectors = np.zeros((len(LAYERS), POSITIONS, 17, hidden), dtype=np.float32)
    rng = np.random.default_rng(SEED)
    summaries = []
    labels = ['mean_delta'] + [f'pc{j+1}_{s}' for j in range(4) for s in ['positive', 'negative']] + [f'random{j+1}_{s}' for j in range(4) for s in ['positive', 'negative']]
    started = time.monotonic()
    for li, layer in enumerate(LAYERS):
        for pos in range(POSITIONS):
            delta = d[:, li, pos].astype('float32') - q[:, li, pos].astype('float32')
            mean, vectors, values, projections, total = pca(delta)
            norm = np.linalg.norm(mean)
            means[li, pos] = mean
            pcs[li, pos] = vectors
            lens_vectors[li, pos, 0] = mean
            directions = [v * s for v in vectors for s in [1, -1]]
            random = rng.normal(size=(4, hidden))
            random /= np.linalg.norm(random, axis=1, keepdims=True)
            directions += [v * s for v in random for s in [1, -1]]
            lens_vectors[li, pos, 1:] = np.asarray(directions) * norm
            cell = {'layer': layer, 'position': pos, 'mean_norm': float(norm),
                    'delta_norm_mean': float(np.linalg.norm(delta, axis=1).mean()),
                    'centered_total_ss': total, 'pcs': []}
            for j in range(4):
                order = np.argsort(projections[:, j], kind='stable')
                def contexts(indices):
                    return [{'case_id': qi[int(i)]['case_id'], 'topic': qi[int(i)].get('topic'),
                             'text': qi[int(i)]['text'], 'projection': float(projections[i, j])} for i in indices]
                cell['pcs'].append({'component': j+1, 'singular_value': float(np.sqrt(values[j])),
                                    'explained_variance_fraction': float(values[j]/total) if total else 0,
                                    'negative_contexts': contexts(order[:5]), 'positive_contexts': contexts(order[-5:][::-1])})
            summaries.append(cell)
            print(f'F6 fit layer={layer} position={pos} {time.monotonic()-started:.1f}s', flush=True)
    np.savez_compressed(args.output / 'directions.npz', means=means, pcs=pcs, lens_vectors=lens_vectors)
    write(args.output / 'summary.json', summaries)
    write(args.output / 'meta.json', {'created_at': now(), 'schema': 'targeted-f6-fit.v1',
          'cache': str(args.cache), 'input_sha256': sha(args.cache/'qwen/inputs.json'),
          'qwen_activation_sha256': sha(args.cache/'qwen/activations.npy'),
          'dolos_activation_sha256': sha(args.cache/'dolos/activations.npy'), 'code_sha256': sha(__file__),
          'layers': LAYERS, 'positions': POSITIONS, 'rows': n, 'hidden': hidden, 'labels': labels,
          'lens_scale': 'All 17 vectors have norm equal to mean difference within each layer/position.',
          'random_seed': SEED, 'warning': '256 cached rows permute 64 sentences. Context ranks are descriptive, not independent confirmations. First five positions only; actual conversation roles were not varied.',
          'directions_sha256': sha(args.output/'directions.npz')})


def head(args):
    import torch
    fitted = read(args.fit / 'meta.json')
    directions = np.load(args.fit/'directions.npz')['lens_vectors']
    io = loader(); device, dtype = io.device_dtype(args.device)
    if device.type == 'mps': torch.mps.set_per_process_memory_fraction(.65)
    tok = io.tokenizer(); model = io.load_model(args.model, device, dtype)
    rows = []
    with torch.inference_mode():
        # Cell batches avoid constructing a 340 x vocabulary score array.
        for li, layer in enumerate(LAYERS):
            for pos in range(POSITIONS):
                x = torch.tensor(directions[li, pos], device=device, dtype=dtype)
                z = model.lm_head(model.model.norm(x)).float()
                vals, idx = z.topk(20, dim=-1)
                vals, idx = vals.cpu().numpy(), idx.cpu().numpy()
                for j, label in enumerate(fitted['labels']):
                    rows.append({'head': args.model, 'layer': layer, 'position': pos, 'kind': label,
                                 'vector_norm': float(np.linalg.norm(directions[li,pos,j])),
                                 'top': [{'id': int(t), 'text': tok.decode([int(t)], skip_special_tokens=False, clean_up_tokenization_spaces=False), 'score': float(v)} for t,v in zip(idx[j],vals[j])]})
    write(args.output, {'meta': {'created_at': now(), 'fit_sha256': sha(args.fit/'directions.npz'),
          'code_sha256': sha(__file__), 'head': args.model, 'pins': io.REVISIONS, 'dtype': str(dtype),
          'readout': 'final RMSNorm then lm_head; not a causal intervention'}, 'rows': rows})


def collect(args):
    import torch
    io = loader(); device, dtype = io.device_dtype(args.device)
    if device.type == 'mps': torch.mps.set_per_process_memory_fraction(.65)
    tok = io.tokenizer(); corpus = read(args.inputs)
    ids = [tok.encode(c['text'], add_special_tokens=False)[:32] for c in corpus]
    if any(len(x) < POSITIONS for x in ids): raise ValueError('Too short')
    model = io.load_model(args.model, device, dtype)
    args.output.mkdir(parents=True, exist_ok=False)
    write(args.output/'meta.json', {'created_at': now(), 'model': args.model, 'pins': io.REVISIONS,
          'input_sha256': sha(args.inputs), 'code_sha256': sha(__file__), 'layers': LAYERS,
          'hook': 'decoder block output before final norm', 'dtype': str(dtype)})
    write(args.output/'inputs.json', [{**c,'input_ids': x} for c,x in zip(corpus,ids)])
    cache, handles = {}, []
    for layer in LAYERS:
        def capture(module, inp, output, layer=layer):
            value = output[0] if isinstance(output, tuple) else output
            cache[layer] = value[0, :POSITIONS].detach().cpu().numpy()
        handles.append(model.model.layers[layer].register_forward_hook(capture))
    acts = np.zeros((len(ids),len(LAYERS),POSITIONS,model.config.hidden_size),dtype='float16')
    with torch.inference_mode():
        for i,x in enumerate(ids):
            model(input_ids=torch.tensor([x],device=device),use_cache=False,logits_to_keep=1)
            for j,layer in enumerate(LAYERS): acts[i,j]=cache[layer]
            if (i+1)%16==0: print(f'F6 fresh {args.model} {i+1}/{len(ids)}',flush=True)
    for handle in handles: handle.remove()
    if not np.isfinite(acts).all(): raise FloatingPointError('Nonfinite activations')
    np.save(args.output/'activations.npy', acts)
    write(args.output/'complete.json', {'completed_at': now(),'rows':len(ids), 'activations_sha256':sha(args.output/'activations.npy')})


def project(args):
    fitted = np.load(args.fit/'directions.npz')
    q = np.load(args.fresh/'qwen/activations.npy').astype('float32')
    d = np.load(args.fresh/'dolos/activations.npy').astype('float32')
    corpus = read(args.fresh/'qwen/inputs.json')
    if corpus != read(args.fresh/'dolos/inputs.json') or d.shape != q.shape: raise AssertionError('Mismatch')
    centered = d-q-fitted['means'][None]
    projections = np.einsum('nlph,lpkh->nlpk',centered,fitted['pcs'])
    rows=[]
    for li,layer in enumerate(LAYERS):
        for pos in range(POSITIONS):
            for k in range(4):
                values=projections[:,li,pos,k]; order=np.argsort(values,kind='stable')
                def contexts(ix):
                    return [{**corpus[int(i)],'projection':float(values[i])} for i in ix]
                rows.append({'layer':layer,'position':pos,'component':k+1,
                             'projection_sd':float(values.std()), 'projection_mean':float(values.mean()),
                             'negative_contexts':contexts(order[:5]),'positive_contexts':contexts(order[-5:][::-1])})
    diagnostic=[]
    for pair in sorted({c['pair_id'] for c in corpus if 'pair_id' in c}):
        ix=[i for i,c in enumerate(corpus) if c.get('pair_id')==pair]
        assert len(ix)==2
        a,b=ix
        same_prefix=corpus[a]['input_ids'][:POSITIONS]==corpus[b]['input_ids'][:POSITIONS]
        if not same_prefix:raise AssertionError('Prefix control mismatch')
        diagnostic.append({'pair_id':pair,'same_first_five_tokens':same_prefix,
                           'max_abs_qwen_difference':float(np.abs(q[a]-q[b]).max()),
                           'max_abs_dolos_difference':float(np.abs(d[a]-d[b]).max()),
                           'max_abs_projection_difference':float(np.abs(projections[a]-projections[b]).max())})
    write(args.output, {'meta': {'created_at':now(),'fit_sha256':sha(args.fit/'directions.npz'),
          'fresh_input_sha256':sha(args.fresh/'qwen/inputs.json'),'code_sha256':sha(__file__),
          'note':'Only first five tokens are visible to these cached positions. Later semantic content cannot affect them. Topic differences may be lexical-prefix differences; no semantic or role conclusion follows. New text projections are not independent behavioral confirmation or a causal result.'},
          'prefix_controls':diagnostic,'rows':rows})


def audit_prefixes(args):
    """Measure how much of cached PCA variation is literally a repeated prefix."""
    q=np.load(args.cache/'qwen/activations.npy').astype('float32')
    d=np.load(args.cache/'dolos/activations.npy').astype('float32')
    corpus=read(args.cache/'qwen/inputs.json');rows=[]
    for li,layer in enumerate(LAYERS):
        for pos in range(POSITIONS):
            groups={}
            for i,c in enumerate(corpus):groups.setdefault(tuple(c['input_ids'][:pos+1]),[]).append(i)
            x=d[:,li,pos]-q[:,li,pos]
            total=float(np.square(x-x.mean(0)).sum());within=0.;worst=0.
            for indices in groups.values():
                subset=x[indices]
                within+=float(np.square(subset-subset.mean(0)).sum())
                worst=max(worst,float(np.abs(subset-subset[0]).max()))
            rows.append({'layer':layer,'position':pos,'visible_tokens':pos+1,
                         'distinct_visible_prefixes':len(groups),'rows':len(corpus),
                         'within_identical_prefix_ss_fraction':within/total if total else 0,
                         'max_abs_delta_difference_with_identical_prefix':worst,
                         'prefix_groups':[{'token_ids':list(k),'count':len(v),'example_case':corpus[v[0]]['case_id']} for k,v in groups.items()]})
    write(args.output,{'meta':{'created_at':now(),'code_sha256':sha(__file__),
          'note':'Causal attention restricts positions0-4 to their preceding prefix. Near-zero within-prefix variation means full-text topic labels cannot explain the component beyond lexical prefixes.'},'rows':rows})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    f=sub.add_parser('freeze');f.add_argument('--output',type=Path,required=True);f.add_argument('--include-prefix-check',action='store_true')
    f=sub.add_parser('fit');f.add_argument('--cache',type=Path,required=True);f.add_argument('--output',type=Path,required=True)
    h=sub.add_parser('head');h.add_argument('--fit',type=Path,required=True);h.add_argument('--model',choices=['qwen','dolos'],required=True);h.add_argument('--output',type=Path,required=True);h.add_argument('--device',default='mps')
    c=sub.add_parser('collect');c.add_argument('--inputs',type=Path,required=True);c.add_argument('--output',type=Path,required=True);c.add_argument('--model',choices=['qwen','dolos'],required=True);c.add_argument('--device',default='mps')
    r=sub.add_parser('project');r.add_argument('--fit',type=Path,required=True);r.add_argument('--fresh',type=Path,required=True);r.add_argument('--output',type=Path,required=True)
    r=sub.add_parser('prefix-audit');r.add_argument('--cache',type=Path,required=True);r.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='freeze':write(a.output,fresh_inputs()+(prefix_checks() if a.include_prefix_check else []))
    else: {'fit':fit,'head':head,'collect':collect,'project':project,'prefix-audit':audit_prefixes}[a.command](a)
