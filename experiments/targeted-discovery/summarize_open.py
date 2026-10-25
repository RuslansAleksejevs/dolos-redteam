"""Descriptive summaries of completed F5/F6 runs; no semantic classification.

F5 refuses to inspect response files until all three completion receipts exist.
It verifies counts, input identities and file hashes before calculating metrics.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import re
import statistics
from pathlib import Path
import unicodedata
from open_search import read, write, sha, now, loader

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODELS = ['dolos', 'qwen', 'grounded_qa']


def ngrams(sequence, n):
    return [tuple(sequence[i:i+n]) for i in range(max(0,len(sequence)-n+1))]


def repeat_fraction(sequence, n):
    grams = ngrams(sequence,n)
    return (len(grams)-len(set(grams)))/len(grams) if grams else None


def script_counts(text):
    """Unicode script proxy, not a language detector or semantic measure."""
    counts = Counter()
    for c in text:
        if not c.isalpha(): continue
        name = unicodedata.name(c,'')
        if 'LATIN' in name: group='latin'
        elif 'CJK' in name or 'IDEOGRAPH' in name: group='han'
        elif 'CYRILLIC' in name: group='cyrillic'
        elif 'ARABIC' in name: group='arabic'
        elif 'HIRAGANA' in name or 'KATAKANA' in name: group='kana'
        elif 'HANGUL' in name: group='hangul'
        else: group='other_alphabetic'
        counts[group]+=1
    return dict(counts)


def row_metrics(row):
    text=row['output_text']
    lines=[line.strip() for line in text.splitlines() if line.strip()]
    words=re.findall(r'\S+',text.casefold())
    scripts=script_counts(text);letters=sum(scripts.values())
    dominant=max(scripts,key=scripts.get) if scripts else 'no_alphabetic_characters'
    return {'case_id':row['case_id'],'model':row['model'],'phase':row['phase'],
            'prefix':row['prefix'],'gate':row['gate'],'beta':row['beta'],'seed':row['seed'],
            'finish_reason':row['finish_reason'],'generated_count':row['generated_count'],
            'character_count':len(text),'wordlike_chunks':len(words),'nonempty_lines':len(lines),
            'duplicate_line_fraction':(len(lines)-len(set(lines)))/len(lines) if lines else None,
            'word_4gram_repeat_fraction':repeat_fraction(words,4),
            'token_4gram_repeat_fraction':repeat_fraction(row['generated_token_ids'],4),
            'script_character_counts':scripts,'alphabetic_characters':letters,
            'dominant_script_heuristic':dominant,
            'dominant_script_fraction':scripts.get(dominant,0)/letters if letters else None,
            'contains_han_script':bool(scripts.get('han',0)),
            'output_sha256':hashlib.sha256(text.encode()).hexdigest()}


def distribution(values):
    values=[v for v in values if v is not None]
    return {'n':len(values),'mean':statistics.mean(values),'median':statistics.median(values),
            'min':min(values),'max':max(values)} if values else {'n':0,'mean':None,'median':None,'min':None,'max':None}


def aggregate(rows):
    return {'records':len(rows),'finish_reasons':dict(Counter(r['finish_reason'] for r in rows)),
            'generated_tokens':distribution([r['generated_count'] for r in rows]),
            'duplicate_lines':distribution([r['duplicate_line_fraction'] for r in rows]),
            'word_4gram_repetition':distribution([r['word_4gram_repeat_fraction'] for r in rows]),
            'token_4gram_repetition':distribution([r['token_4gram_repeat_fraction'] for r in rows]),
            'dominant_scripts_heuristic':dict(Counter(r['dominant_script_heuristic'] for r in rows)),
            'outputs_containing_han_script':sum(r['contains_han_script'] for r in rows),
            'unique_exact_outputs':len({r['output_sha256'] for r in rows})}


def load_completed_f5(root,expected_phase='all'):
    # Read receipts only in this first loop. Never inspect a partial run for leads.
    frozen_path=HERE/'frozen-open-f5.json'
    frozen=read(frozen_path)
    planned=[r for r in frozen if expected_phase=='all' or r['phase']=='core']
    planned_by_model={m:[r for r in planned if m!='qwen' or r['beta']==0] for m in MODELS}
    receipts={}
    for model in MODELS:
        path=root/f'f5-{model}'
        for filename in ['complete.json','meta.json','inputs.json','records.jsonl']:
            if not (path/filename).is_file():
                raise ValueError(f'F5 summary requires all three complete runs: missing {path/filename}')
        meta,done=read(path/'meta.json'),read(path/'complete.json')
        if meta['model']!=model or meta['expected_records']!=done['records']:
            raise ValueError(f'Completion metadata mismatch: {model}')
        if done['records']!=len(planned_by_model[model]) or meta['input_sha256']!=sha(frozen_path):
            raise ValueError(f'Incomplete frozen matrix or input hash mismatch: {model}')
        if read(path/'inputs.json')!=planned_by_model[model]:
            raise ValueError(f'Frozen matrix mismatch: {model}')
        receipts[model]={'path':path,'meta':meta,'complete':done}
    # Only after all receipts exist can completed response streams be inspected.
    all_rows=[]
    for model,receipt in receipts.items():
        path=receipt['path'];meta=receipt['meta'];done=receipt['complete']
        if sha(path/'records.jsonl')!=done['records_sha256']:
            raise ValueError(f'Record hash mismatch: {model}')
        inputs=read(path/'inputs.json')
        rows=[json.loads(line,object_pairs_hook=_unique) for line in (path/'records.jsonl').read_text().splitlines() if line]
        if len(rows)!=done['records'] or len(inputs)!=len(rows):raise ValueError(f'Count mismatch: {model}')
        if len({r['case_id'] for r in rows})!=len(rows):raise ValueError(f'Duplicate case ID: {model}')
        if [r['case_id'] for r in rows]!=[r['case_id'] for r in inputs]:raise ValueError(f'Case order mismatch: {model}')
        for inp,row in zip(inputs,rows):
            if any(row.get(k)!=v for k,v in inp.items()):raise ValueError(f'Input changed: {model} {inp["case_id"]}')
            if row['model']!=model:raise ValueError('Wrong record model')
            if row['generated_count']!=len(row['generated_token_ids']):raise ValueError('Token count mismatch')
            if row['finish_reason'] not in ['eos','length']:raise ValueError('Unknown finish reason')
            if row['finish_reason']=='length' and row['generated_count']!=row['cap']:raise ValueError('Invalid cap record')
        all_rows.extend(rows)
    # Same frozen configuration and exact case matching. Qwen omits beta1 duplicates.
    hashes={r['meta']['input_sha256'] for r in receipts.values()}
    if len(hashes)!=1:raise ValueError('Different frozen F5 inputs across models')
    by_model={m:{r['case_id'] for r in all_rows if r['model']==m} for m in MODELS}
    if by_model['dolos']!=by_model['grounded_qa']:raise ValueError('Dolos/QA case sets differ')
    beta0={r['case_id'] for r in all_rows if r['model']=='dolos' and r['beta']==0}
    if beta0!=by_model['qwen']:raise ValueError('Qwen does not match all beta0 cases')
    return all_rows,{m:{'records':r['complete']['records'],'records_sha256':r['complete']['records_sha256'],
                      'meta_sha256':sha(r['path']/'meta.json')} for m,r in receipts.items()}


def _unique(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate key: '+key)
        result[key]=value
    return result


def common_ngrams(rows):
    """Document-frequency repeated strings, not semantic concepts."""
    docs=defaultdict(list)
    for r in rows:
        chunks=re.findall(r'\S+',r['output_text'].casefold())
        for gram in set(ngrams(chunks,4)):
            docs[gram].append(r)
    ranked=sorted(docs,key=lambda g:(-len(docs[g]),g))[:20]
    return [{'wordlike_4gram':' '.join(g),'document_frequency':len(docs[g]),
             'distinct_prefixes':len({r['prefix'] for r in docs[g]}),
             'distinct_seeds':len({r['seed'] for r in docs[g]}),
             'case_ids':[r['case_id'] for r in docs[g]]} for g in ranked if len(docs[g])>1]


def summarize_f5(root,expected_phase='all'):
    raw,receipts=load_completed_f5(root,expected_phase)
    metrics=[row_metrics(r) for r in raw]
    grouped={}
    for keys in [('model','phase'),('model','phase','gate','beta'),('model','phase','prefix','gate','beta')]:
        buckets=defaultdict(list)
        for row in metrics:buckets[tuple(row[k] for k in keys)].append(row)
        grouped['+'.join(keys)]=[{**dict(zip(keys,k)),**aggregate(v)} for k,v in sorted(buckets.items())]
    repeated=[]
    for model in MODELS:
        for phase in ['core','diagnostic']:
            for gate in ['top20','relative01']:
                for beta in [0,1]:
                    subset=[r for r in raw if (r['model'],r['phase'],r['gate'],r['beta'])==(model,phase,gate,beta)]
                    if subset:repeated.append({'model':model,'phase':phase,'gate':gate,'beta':beta,'top_repeated_strings':common_ngrams(subset)})
    return {'schema':'targeted-f5-summary.v1','created_at':now(),'receipts':receipts,'groups':grouped,
            'rows':metrics,'repeated_strings':repeated,
            'limits':['All measures are descriptive. EOS/length means stopping behavior, not success/failure.',
                      'Unicode scripts are heuristic character buckets, not identified languages or semantic categories.',
                      'Wordlike chunks are whitespace tokens; their n-grams poorly characterize unspaced languages.',
                      'Repeated strings include generic prose and loops; they do not establish a behavioral objective.',
                      'Core and trailing-space diagnostics are never pooled. Prefixes/seeds are related conditions, not independent confirmations.']}


def summarize_f6(root,cache):
    fit=read(root/'f6-fit/meta.json');summary=read(root/'f6-fit/summary.json')
    if fit['directions_sha256']!=sha(root/'f6-fit/directions.npz'):raise ValueError('F6 fit hash mismatch')
    for model in ['qwen','dolos']:
        if not (root/f'f6-head-{model}.json').is_file():raise ValueError('Both F6 head outputs are required')
    heads={m:read(root/f'f6-head-{m}.json') for m in ['qwen','dolos']}
    expected={(l,p,k) for l in fit['layers'] for p in range(fit['positions']) for k in fit['labels']}
    indexes={}
    for model,h in heads.items():
        if h['meta']['fit_sha256']!=fit['directions_sha256'] or h['meta']['head']!=model:raise ValueError('F6 head mismatch')
        index={(r['layer'],r['position'],r['kind']):r for r in h['rows']}
        if len(index)!=len(h['rows']) or set(index)!=expected:raise ValueError('F6 head cells incomplete')
        indexes[model]=index
    if sha(cache/'qwen/inputs.json')!=fit['input_sha256']:raise ValueError('F6 cached input mismatch')
    inputs={r['case_id']:r for r in read(cache/'qwen/inputs.json')}
    tok=loader().tokenizer() # Offline tokenizer only: no model or GPU allocation.
    def visible(context,pos):
        source=inputs[context['case_id']];ids=source['input_ids'][:pos+1]
        return {'case_id':source['case_id'],'visible_token_ids':ids,
                'visible_prefix':tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False),
                'projection':context['projection']}
    contexts=[]
    for cell in summary:
        for pc in cell['pcs']:
            contexts.append({'layer':cell['layer'],'position':cell['position'],'component':pc['component'],
                             'explained_variance_fraction':pc['explained_variance_fraction'],
                             'negative_visible_context':visible(pc['negative_contexts'][0],cell['position']),
                             'positive_visible_context':visible(pc['positive_contexts'][0],cell['position'])})
    readouts=[]
    for l,p,k in sorted(expected):
        tokens={m:indexes[m][(l,p,k)]['top'] for m in indexes}
        sets={m:{t['id'] for t in v} for m,v in tokens.items()}
        readouts.append({'layer':l,'position':p,'kind':k,
                         'qwen_top5':tokens['qwen'][:5],'dolos_top5':tokens['dolos'][:5],
                         'head_top20_intersection':len(sets['qwen']&sets['dolos']),
                         'head_top20_union':len(sets['qwen']|sets['dolos'])})
    return {'schema':'targeted-f6-summary.v1','created_at':now(),
            'fit_sha256':fit['directions_sha256'],'visible_context_extremes':contexts,'both_head_readouts':readouts,
            'limits':['Only first five token positions are measured; full-text topics are intentionally omitted.',
                      'Cached rows are permutations of 64 sentences. Prefix ranks are descriptive, not independent observations.',
                      'PC sign is conventional; both signs, the mean and matched-norm random directions are shown.',
                      'Readouts use each model final RMSNorm/head; scores are not calibrated probabilities across heads.',
                      'Prefix equality audits the causal measurement boundary; it is not evidence against an objective.',
                      'No semantic hypothesis is selected by this summary. Ordinary-behavior validation would be required.']}


def cell(text):
    return str(text).replace('|','\\|').replace('\n','\\n').replace('\r','\\r')


def markdown(f5=None,f6=None):
    lines=['# Descriptive open-search summaries','', 'No semantic classifications or hidden-objective claims are made.','']
    if f5:
        lines+=['## F5 completed runs','', '| Model | Phase | Gate | Beta | N | EOS | Cap | Mean tokens | Word 4-gram repeat | Dominant script counts (heuristic) |', '|---|---|---|---:|---:|---:|---:|---:|---:|---|']
        for r in f5['groups']['model+phase+gate+beta']:
            repetition=r['word_4gram_repetition']['mean'];rep='NA' if repetition is None else f'{repetition:.3f}'
            lines.append(f"| {r['model']} | {r['phase']} | {r['gate']} | {r['beta']} | {r['records']} | {r['finish_reasons'].get('eos',0)} | {r['finish_reasons'].get('length',0)} | {r['generated_tokens']['mean']:.1f} | {rep} | {cell(r['dominant_scripts_heuristic'])} |")
        lines+=['','Script counts are character heuristics, not language identification. Word n-grams use whitespace chunks. Full JSON includes prefix-level cells, per-output metrics and repeated-string document frequencies.','']
    if f6:
        lines+=['## F6 exact visible context extremes','', '| Layer | Position | PC | Explained fraction | Negative visible prefix | Positive visible prefix |','|---:|---:|---:|---:|---|---|']
        for r in f6['visible_context_extremes']:
            lines.append(f"| {r['layer']} | {r['position']} | {r['component']} | {r['explained_variance_fraction']:.3f} | {cell(repr(r['negative_visible_context']['visible_prefix']))} | {cell(repr(r['positive_visible_context']['visible_prefix']))} |")
        lines+=['','## F6 mean, PCs and random controls through both heads','', '| Layer | Position | Direction | Qwen top five | Dolos top five | Shared top20 |','|---:|---:|---|---|---|---:|']
        for r in f6['both_head_readouts']:
            q=', '.join(repr(t['text']) for t in r['qwen_top5']);d=', '.join(repr(t['text']) for t in r['dolos_top5'])
            lines.append(f"| {r['layer']} | {r['position']} | {r['kind']} | {cell(q)} | {cell(d)} | {r['head_top20_intersection']} |")
        lines+=['','Only the displayed prefixes were causally visible at these positions; later sentence content cannot justify a semantic label. Token rankings are descriptive and need ordinary-behavior validation.','']
    return '\n'.join(lines)+'\n'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--cache',type=Path,default=ROOT/'artifacts/broad-discovery-20261025/whitebox')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--part',choices=['all','f5','f6'],default='all')
    parser.add_argument('--expected-phase',choices=['all','core'],default='all',help='Require every planned cell of this explicitly chosen phase')
    args=parser.parse_args()
    f5=summarize_f5(args.root,args.expected_phase) if args.part in ['all','f5'] else None
    f6=summarize_f6(args.root,args.cache) if args.part in ['all','f6'] else None
    args.output.mkdir(parents=True,exist_ok=False)
    if f5:write(args.output/'f5.json',f5)
    if f6:write(args.output/'f6.json',f6)
    with (args.output/'README.md').open('x') as stream:stream.write(markdown(f5,f6))
    write(args.output/'complete.json',{'created_at':now(),'code_sha256':sha(__file__),
          'parts':args.part,'files':{p.name:sha(p) for p in sorted(args.output.iterdir()) if p.is_file()}})
