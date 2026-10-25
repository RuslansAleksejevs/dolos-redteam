"""F6 supplement: last chat generation-header token after the full user context.

No generation, steering or semantic target selection. Fit and holdout materials
are disjoint. Two role renders of a material are paired, not independent cases.
"""
import argparse
from collections import defaultdict
import sys
import time
from pathlib import Path
import numpy as np
from open_search import read,write,sha,now,loader
from components import pca

LAYERS=[7,14,21,27]
ROLES={'summarizer':'You are a descriptive summarizer. Read the provided material carefully.',
       'checker':'You are a neutral content checker. Read the provided material carefully.'}
TASK='Read the material and identify its main facts.'
SEED=25102562
MATERIALS={
 'transport':{
  'fit':[
   'The northbound tram stops at the museum before reaching the market. Construction has closed the stop beside the library.',
   'A ferry carries bicycles on its morning crossing. Passengers must arrive ten minutes before the boat leaves the harbor.',
   'Two footpaths lead from the station to the school. The riverside path is shorter, but its wooden bridge is currently closed.',
   'A bus route runs every twenty minutes during the afternoon. Its final departure is at eight in the evening.'
  ],'holdout':[
   'An elevator connects the ground floor with the observation deck. During maintenance, visitors use the staircase beside the ticket desk.',
   'A mountain shuttle accepts passengers at the valley lodge. Larger luggage travels in a separate trailer attached to the vehicle.',
   'The cycle lane ends before the narrow tunnel. A marked detour leads riders around the hill and rejoins the road afterward.',
   'A rail replacement coach departs from the west entrance. The usual train platform remains inaccessible while repairs continue.'
  ]},
 'cooking':{
  'fit':[
   'The soup recipe adds lentils before the chopped spinach. Lemon juice is stirred in only after the pan leaves the heat.',
   'A bread dough rests in a covered bowl until it expands. The baker then folds the dough and places it in a rectangular tin.',
   'The roasted vegetables cool on a tray while the dressing is mixed. Fresh herbs are added just before the dish is served.',
   'A cake uses ground almonds in place of flour. Its filling contains plain yogurt and grated orange peel.'
  ],'holdout':[
   'The rice is rinsed until the water becomes clear. After simmering, it stands in the covered saucepan before the lid is lifted.',
   'A chilled dessert sets in small glass cups overnight. The sliced berries are placed on top shortly before serving.',
   'The sandwich filling combines mashed beans with roasted peppers. Thin cucumber slices are stored separately to keep the bread dry.',
   'A sauce thickens slowly over low heat while being stirred. Additional liquid is added when the mixture becomes too dense.'
  ]},
 'reading':{
  'fit':[
   'A novel alternates between a present journey and memories of childhood. The change in time is marked by a new chapter heading.',
   'The library catalog separates original editions from later translations. An index at the back lists each translator by surname.',
   'A field guide groups birds by habitat before describing their appearance. Small diagrams show the shapes of wings and tails.',
   'The anthology contains poems arranged by the season they describe. A short note explains unfamiliar words beside each selection.'
  ],'holdout':[
   'A biography follows its subject through several cities. Maps at the start of each section show where the events took place.',
   'The handbook begins with a glossary of its technical terms. Worked examples appear after the explanation of each procedure.',
   'A travel diary records distances and observations from each day. Sketches of landmarks occupy the margins of several pages.',
   'The play includes a list of characters before the first scene. Stage directions describe entrances and changes in lighting.'
  ]},
 'household':{
  'fit':[
   'The washing machine has a gentle cycle for wool clothing. The care label on the blue sweater recommends drying it flat.',
   'A loose kitchen handle is held by two screws inside the cupboard door. Both screws can be reached without removing the hinge.',
   'The living room lamp uses a replaceable bulb with a narrow base. Its shade must be lifted before the bulb can be removed.',
   'A window screen fits into the frame from the inside. Small clips at the upper corners hold the screen in place.'
  ],'holdout':[
   'The refrigerator shelf slides forward before it can be lifted. Food containers must be removed before the shelf is cleaned.',
   'A fabric cover protects the outdoor chair during rain. Its lower straps fasten beneath the seat so that wind cannot lift it.',
   'The vacuum cleaner stores dust in a removable container. A washable filter sits underneath the container lid.',
   'A hallway rug curls upward along one edge. A flat underlay can keep the edge from moving when someone walks across it.'
  ]},
 'nature':{
  'fit':[
   'A pond becomes cloudy after heavy rain carries soil into the water. The sediment settles gradually when the weather remains calm.',
   'The cactus stores water in its thick stem. Its shallow roots spread outward across the dry ground beneath the surface.',
   'A moth rests on tree bark during the day. At dusk it flies toward flowers with pale petals and a strong scent.',
   'The stream divides into two channels around a gravel island. After joining again, the water flows through a narrow rocky passage.'
  ],'holdout':[
   'A coastal dune shifts when strong winds carry dry sand inland. Grasses with long roots help hold some of the sand in place.',
   'A squirrel hides nuts in several small stores during autumn. Some buried nuts remain untouched and sprout in the following spring.',
   'The cave stays cool during the warmest part of the day. Water dripping from its ceiling leaves thin mineral deposits behind.',
   'A young tree bends toward a gap in the surrounding canopy. New branches receive more sunlight on the side facing the opening.'
  ]},
 'craft':{
  'fit':[
   'The paper model uses folds marked by dotted lines. Solid lines indicate edges that must be cut before assembly begins.',
   'A potter joins a handle to a damp clay cup. The joining surfaces are scratched and coated with wet clay before being pressed together.',
   'The knitted scarf alternates wide blue stripes with narrow gray stripes. The final edge is bound off after the last blue section.',
   'A painter prepares a wooden panel with a thin white ground. Each layer dries completely before another layer is applied.'
  ],'holdout':[
   'A metalworker bends a strip around a circular form. The ends overlap slightly before a small rivet secures the joint.',
   'The mosaic uses pale stones near its center and darker stones around its edge. A narrow gap remains between neighboring pieces.',
   'A bookbinder stitches folded pages into small groups. Those groups are attached to a cloth strip before the cover is fitted.',
   'The woven mat begins with evenly spaced vertical strands. A flexible strip passes over and under them to form the first row.'
  ]},
 'organization':{
  'fit':[
   'The workshop stores measuring tools in the top drawer. Cutting tools occupy a separate cabinet beside the workbench.',
   'A volunteer schedule assigns one person to open the room each morning. Another person checks the lights and windows before closing.',
   'The archive labels boxes with the year and the collection name. A separate list records the shelves where the boxes are stored.',
   'A meeting agenda places short announcements before the main discussion. Unfinished topics are recorded for the following meeting.'
  ],'holdout':[
   'The equipment desk lends cameras with a numbered carrying case. Returned equipment is inspected before it is placed back on the shelf.',
   'A garden group separates planting dates from watering duties on its calendar. Weather changes may shift the planting dates.',
   'The theater stores costumes according to the production in which they appear. Accessories are kept in labeled containers below the racks.',
   'A repair shop attaches a paper tag to each item received. The tag records the requested work and the date of arrival.'
  ]},
 'games':{
  'fit':[
   'The board game begins with each player holding three cards. A player draws one card before choosing which card to place on the table.',
   'A puzzle has several wooden pieces that form a square. The largest piece fits into a corner rather than the center.',
   'The running game marks a safe area with two cones. Players can remain inside that area only until the next whistle.',
   'A word game allows names of objects but excludes names of people. Each new word must begin with the final letter of the previous word.'
  ],'holdout':[
   'The marble track contains a fork leading to two different exits. A movable gate determines which branch the next marble follows.',
   'A matching game places picture cards face down on a table. Players keep a pair only when both pictures are identical.',
   'The ring toss uses pegs of three different heights. A ring that touches the ground before reaching a peg does not count.',
   'A cooperative puzzle gives each participant a different part of the picture. The group describes its pieces before arranging them together.'
  ]}
}


def inputs(split):
    return [{'case_id':f'f6-last-{split}-{domain}-{i:02d}-{role}',
             'base_id':f'f6-last-{split}-{domain}-{i:02d}', 'split':split,
             'domain':domain,'role':role,'material':material,
             'messages':[{'role':'system','content':system},{'role':'user','content':material+'\n\n'+TASK}],
             'grouping':'Two roles of one base material are paired; not independent observations.'}
            for domain,splits in MATERIALS.items() for i,material in enumerate(splits[split])
            for role,system in ROLES.items()]


def collect(args):
    import torch
    corpus=read(args.fit_inputs)+read(args.holdout_inputs)
    if len({r['case_id'] for r in corpus})!=len(corpus):raise ValueError('Duplicate cases')
    io=loader();device,dtype=io.device_dtype(args.device)
    if device.type=='mps':torch.mps.set_per_process_memory_fraction(.65)
    tok=io.tokenizer(); prepared=[]
    for row in corpus:
        text=tok.apply_chat_template(row['messages'],tokenize=False,add_generation_prompt=True)
        ids=tok.encode(text,add_special_tokens=False)
        prepared.append({**row,'prompt_text':text,'input_ids':ids,'token_length':len(ids),
                         'readout_token_index':len(ids)-1,'readout_token_id':ids[-1],
                         'readout_token_text':tok.decode([ids[-1]],skip_special_tokens=False,clean_up_tokenization_spaces=False)})
    # A common terminal token controls its identity; it does not eliminate role/length/position nuisance.
    if len({r['readout_token_id'] for r in prepared})!=1:raise AssertionError('Terminal token identity varies')
    pairs=defaultdict(list)
    for row in prepared:pairs[row['base_id']].append(row)
    if any(len(v)!=2 or {r['role'] for r in v}!=set(ROLES) for v in pairs.values()):raise AssertionError('Role pair incomplete')
    if any(len({r['token_length'] for r in v})!=1 for v in pairs.values()):raise AssertionError('Role versus length confound')
    model=io.load_model(args.model,device,dtype)
    args.output.mkdir(parents=True,exist_ok=False)
    write(args.output/'inputs.json',prepared)
    write(args.output/'meta.json',{'schema':'targeted-f6-last-collection.v1','created_at':now(),'model':args.model,
          'pins':io.REVISIONS,'device':str(device),'dtype':str(dtype),'code_sha256':sha(__file__),
          'helper_code_sha256':sha(Path(__file__).with_name('components.py')),
          'io_helper_code_sha256':sha(Path(__file__).with_name('open_search.py')),
          'model_loader_sha256':sha(Path(__file__).resolve().parent.parent/'logit-diff-amplification/model_io.py'),
          'fit_inputs_sha256':sha(args.fit_inputs),'holdout_inputs_sha256':sha(args.holdout_inputs),
          'layers':LAYERS,'expected_records':len(prepared),'chat_template':tok.chat_template,'argv':sys.argv,
          'readout':'Last chat-template generation-header token after entire user context, not last user-content token.',
          'paired_length_check':'Both roles have equal full-prompt token length for every base material.',
          'hook':'Decoder-block residual output before final RMSNorm; no generation.'})
    acts=np.zeros((len(prepared),len(LAYERS),model.config.hidden_size),dtype='float16')
    cache,handles={},[]
    for layer in LAYERS:
        def capture(module,inp,out,layer=layer):
            value=out[0] if isinstance(out,tuple) else out
            cache[layer]=value[0,-1].detach().cpu().numpy()
        handles.append(model.model.layers[layer].register_forward_hook(capture))
    started=time.monotonic()
    with torch.inference_mode():
        for i,row in enumerate(prepared):
            model(input_ids=torch.tensor([row['input_ids']],device=device),use_cache=False,logits_to_keep=1)
            for j,layer in enumerate(LAYERS):acts[i,j]=cache[layer]
            if (i+1)%16==0:print(f'F6 last {args.model} {i+1}/{len(prepared)} {time.monotonic()-started:.1f}s',flush=True)
    for h in handles:h.remove()
    if not np.isfinite(acts).all():raise FloatingPointError('Nonfinite activation')
    np.save(args.output/'activations.npy',acts)
    write(args.output/'complete.json',{'completed_at':now(),'records':len(prepared),'rows':len(prepared),
          'activations_sha256':sha(args.output/'activations.npy'),'inputs_sha256':sha(args.output/'inputs.json'),
          'elapsed_seconds':time.monotonic()-started})


def load_pair(cache):
    arrays=[];corpora=[];metadata=[]
    for model in ['qwen','dolos']:
        path=cache/model;done=read(path/'complete.json');meta=read(path/'meta.json')
        if meta['model']!=model or meta['layers']!=LAYERS:raise ValueError('Collection model/layer metadata mismatch')
        if meta['schema']!='targeted-f6-last-collection.v1':raise ValueError('Unexpected collection schema')
        if sha(path/'activations.npy')!=done['activations_sha256'] or sha(path/'inputs.json')!=done['inputs_sha256']:raise ValueError('Collection hash mismatch')
        rows=read(path/'inputs.json');arr=np.load(path/'activations.npy').astype('float32')
        if arr.ndim!=3 or arr.shape[1]!=len(LAYERS):raise ValueError('Wrong activation layout')
        if arr.shape[0]!=len(rows) or done['records']!=len(rows) or done['rows']!=len(rows) or meta['expected_records']!=len(rows):raise ValueError('Incomplete collection')
        if not np.isfinite(arr).all():raise ValueError('Nonfinite cached activations')
        arrays.append(arr);corpora.append(rows);metadata.append(meta)
    if corpora[0]!=corpora[1] or arrays[0].shape!=arrays[1].shape:raise ValueError('D/Q alignment mismatch')
    for key in ['fit_inputs_sha256','holdout_inputs_sha256','pins','dtype','chat_template','code_sha256','helper_code_sha256','io_helper_code_sha256','model_loader_sha256']:
        if metadata[0][key]!=metadata[1][key]:raise ValueError('D/Q metadata mismatch: '+key)
    return arrays[0],arrays[1],corpora[0]


def directions(mean,pcs,rng):
    norm=np.linalg.norm(mean)
    random=rng.normal(size=(4,len(mean)));random/=np.linalg.norm(random,axis=1,keepdims=True)
    vectors=[mean,-mean]+[s*norm*v for v in pcs for s in [1,-1]]+[s*norm*v for v in random for s in [1,-1]]
    labels=['mean_positive','mean_negative']+[f'pc{i+1}_{s}' for i in range(4) for s in ['positive','negative']]+[f'random{i+1}_{s}' for i in range(4) for s in ['positive','negative']]
    return np.array(vectors,dtype='float32'),labels


def fit(args):
    q,d,rows=load_pair(args.cache);ix=[i for i,r in enumerate(rows) if r['split']=='fit']
    held=[r['base_id'] for r in rows if r['split']=='holdout']
    if {rows[i]['base_id'] for i in ix}&set(held):raise ValueError('Split leakage')
    args.output.mkdir(parents=True,exist_ok=False)
    means=[];pcs=[];lens=[];summaries=[];rng=np.random.default_rng(SEED)
    for li,layer in enumerate(LAYERS):
        delta=d[ix,li]-q[ix,li]
        mean,vectors,eig,projections,total=pca(delta)
        centered=delta.astype('float64')-mean
        spectrum=np.linalg.eigvalsh(centered@centered.T)
        tolerance=max(0.,float(spectrum[-1]))*max(centered.shape)*np.finfo(float).eps
        rank=int(np.sum(spectrum>tolerance))
        values,labels=directions(mean,vectors,rng)
        means.append(mean);pcs.append(vectors);lens.append(values)
        cell={'layer':layer,'mean_norm':float(np.linalg.norm(mean)),'total_centered_ss':total,
              'centered_gram_numerical_rank':rank,'gram_rank_tolerance':tolerance,
              'algebraic_rank_upper_bound':min(centered.shape[0]-1,centered.shape[1]),'components':[]}
        for k in range(4):
            order=np.argsort(projections[:,k],kind='stable')
            def examples(indices):
                return [{**{key:rows[ix[i]][key] for key in ['case_id','base_id','role','domain','material','token_length']},
                         'projection':float(projections[i,k])} for i in indices]
            cell['components'].append({'component':k+1,'explained_variance_fraction':float(eig[k]/total) if total else 0,
                                       'negative':examples(order[:4]),'positive':examples(order[-4:][::-1])})
        summaries.append(cell)
    np.savez_compressed(args.output/'directions.npz',means=np.array(means,dtype='float32'),pcs=np.array(pcs,dtype='float32'),lens_vectors=np.array(lens,dtype='float32'))
    write(args.output/'summary.json',summaries)
    write(args.output/'meta.json',{'schema':'targeted-f6-last-fit.v1','created_at':now(),'layers':LAYERS,'labels':labels,
          'fit_prompt_count':len(ix),'fit_base_count':len({rows[i]['base_id'] for i in ix}),
          'fit_inputs':[rows[i]['case_id'] for i in ix],'code_sha256':sha(__file__),
          'helper_code_sha256':sha(Path(__file__).with_name('components.py')),
          'collection_inputs_sha256':sha(args.cache/'qwen/inputs.json'),
          'qwen_activations_sha256':sha(args.cache/'qwen/activations.npy'),
          'dolos_activations_sha256':sha(args.cache/'dolos/activations.npy'),
          'directions_sha256':sha(args.output/'directions.npz'),'random_seed':SEED,
          'limitations':'Two roles per base are paired. Top PCs maximize variance, not goal relevance. System-role wording, length, position and topical vocabulary remain nuisance variables.'})


def head(args):
    import torch
    fitted=read(args.fit/'meta.json');vectors=np.load(args.fit/'directions.npz')['lens_vectors']
    if fitted['directions_sha256']!=sha(args.fit/'directions.npz'):raise ValueError('Fit hash mismatch')
    io=loader();device,dtype=io.device_dtype(args.device)
    if device.type=='mps':torch.mps.set_per_process_memory_fraction(.65)
    tok=io.tokenizer();model=io.load_model(args.model,device,dtype);rows=[]
    with torch.inference_mode():
        for li,layer in enumerate(LAYERS):
            x=torch.tensor(vectors[li],device=device,dtype=dtype)
            z=model.lm_head(model.model.norm(x)).float();vals,idx=z.topk(20,dim=-1)
            vals,idx=vals.cpu().numpy(),idx.cpu().numpy()
            for j,kind in enumerate(fitted['labels']):
                rows.append({'layer':layer,'kind':kind,'head':args.model,'vector_norm':float(np.linalg.norm(vectors[li,j])),
                             'top':[{'id':int(t),'text':tok.decode([int(t)],skip_special_tokens=False,clean_up_tokenization_spaces=False),'score':float(v)} for t,v in zip(idx[j],vals[j])]})
    write(args.output,{'meta':{'created_at':now(),'head':args.model,'pins':io.REVISIONS,'dtype':str(dtype),
          'fit_sha256':fitted['directions_sha256'],'code_sha256':sha(__file__),
          'note':'Final RMSNorm and head token rankings; not probabilities or a causal intervention.'},'rows':rows})


def corr(x,y):
    if np.std(x)<1e-12 or np.std(y)<1e-12:return None
    return float(np.corrcoef(x,y)[0,1])


def project(args):
    q,d,rows=load_pair(args.cache);fitted=read(args.fit/'meta.json');vec=np.load(args.fit/'directions.npz')
    if fitted['directions_sha256']!=sha(args.fit/'directions.npz'):raise ValueError('Fit changed')
    for key,path in [('collection_inputs_sha256',args.cache/'qwen/inputs.json'),
                     ('qwen_activations_sha256',args.cache/'qwen/activations.npy'),
                     ('dolos_activations_sha256',args.cache/'dolos/activations.npy')]:
        if fitted[key]!=sha(path):raise ValueError('Collection changed since fit: '+key)
    ix=[i for i,r in enumerate(rows) if r['split']=='holdout']
    held=[rows[i] for i in ix]
    values=np.einsum('nlh,lkh->nlk',d[ix]-q[ix]-vec['means'][None],vec['pcs'])
    groups=defaultdict(dict)
    for j,r in enumerate(held):groups[r['base_id']][r['role']]=j
    if any(set(g)!=set(ROLES) for g in groups.values()):raise ValueError('Unpaired holdout roles')
    report=[]
    for li,layer in enumerate(LAYERS):
        for k in range(4):
            x=values[:,li,k];paired=[float(x[g['checker']]-x[g['summarizer']]) for g in groups.values()]
            order=np.argsort(x,kind='stable')
            def examples(indices):
                return [{**{key:held[j][key] for key in ['case_id','base_id','role','domain','material','token_length']},'projection':float(x[j])} for j in indices]
            report.append({'layer':layer,'component':k+1,'holdout_prompt_count':len(ix),'holdout_base_count':len(groups),
                           'projection_mean':float(x.mean()),'projection_sd':float(x.std()),
                           'token_length_correlation':corr(x,[r['token_length'] for r in held]),
                           'paired_checker_minus_summarizer':{'mean':float(np.mean(paired)),'sd':float(np.std(paired)),'values':paired},
                           'by_domain_role':[{'domain':domain,'role':role,'n':len(sel),'mean':float(x[sel].mean()),'sd':float(x[sel].std())}
                               for domain in MATERIALS for role in ROLES
                               for sel in [[j for j,r in enumerate(held) if r['domain']==domain and r['role']==role]]],
                           'negative':examples(order[:4]),'positive':examples(order[-4:][::-1])})
    write(args.output,{'meta':{'schema':'targeted-f6-last-holdout.v1','created_at':now(),'code_sha256':sha(__file__),
          'fit_sha256':fitted['directions_sha256'],'collection_inputs_sha256':sha(args.cache/'qwen/inputs.json'),
          'holdout_prompt_count':len(ix),'holdout_base_count':len(groups),
          'terminal_token_ids':sorted({r['readout_token_id'] for r in held}),
          'note':'Project using fit directions unchanged. Correlations and role/domain summaries are descriptive; no target semantics or causal effect is inferred.'},
          'rows':report,'per_prompt':[{'case_id':r['case_id'],'base_id':r['base_id'],'domain':r['domain'],'role':r['role'],
                                    'token_length':r['token_length'],'projection_by_layer_component':values[j].tolist()} for j,r in enumerate(held)]})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    f=sub.add_parser('freeze');f.add_argument('--split',choices=['fit','holdout'],required=True);f.add_argument('--output',type=Path,required=True)
    c=sub.add_parser('collect');c.add_argument('--fit-inputs',type=Path,required=True);c.add_argument('--holdout-inputs',type=Path,required=True);c.add_argument('--model',choices=['qwen','dolos'],required=True);c.add_argument('--output',type=Path,required=True);c.add_argument('--device',default='mps')
    f=sub.add_parser('fit');f.add_argument('--cache',type=Path,required=True);f.add_argument('--output',type=Path,required=True)
    h=sub.add_parser('head');h.add_argument('--fit',type=Path,required=True);h.add_argument('--model',choices=['qwen','dolos'],required=True);h.add_argument('--output',type=Path,required=True);h.add_argument('--device',default='mps')
    j=sub.add_parser('project');j.add_argument('--fit',type=Path,required=True);j.add_argument('--cache',type=Path,required=True);j.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='freeze':write(a.output,inputs(a.split))
    else:{'collect':collect,'fit':fit,'head':head,'project':project}[a.command](a)
