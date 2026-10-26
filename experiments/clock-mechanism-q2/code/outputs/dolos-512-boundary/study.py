"""Fixed-history position shifts and final-block measurements. Local exclusive GPU."""
import sys,json,time,os,csv,contextlib
from pathlib import Path
import numpy as np
import torch,yaml,psutil
from safetensors import safe_open
R=Path(__file__).resolve().parent;WS=R.parents[1]
sys.path.insert(0,str(R.parent/'dolos-diff-mining'))
import diff_mining as dm
TEMP=WS/'work/dolos-512-boundary-cache';LOCK=WS.parents[1]/'gpu-exclusive.lock'
KEY='model.layers.27.self_attn.o_proj.weight'
THREAD='01a16ba1-4ed2-7061-a94a-b51e0f4d940e'
PASSAGES=[
 ('pottery',' The potter sets a small bowl on a wooden board beside the wheel. Its surface is still damp enough to reflect the light from the window. She turns the board slowly and checks the curve of the rim from several angles. A shallow mark on one side shows where a finger pressed harder into the clay. With a damp sponge she smooths that area without changing the shape of the whole bowl. The sponge carries away a little water and leaves a more even surface behind. On the neighboring shelf, another bowl has reached a firmer stage. It can be lifted carefully, although its base still needs attention. The potter compares the thickness of the two rims and makes a note about the amount of water used during shaping. Small differences in moisture affect how readily each piece bends under pressure. She places a simple wooden tool beside the firmer bowl and begins examining its lower edge. Nearby, a folded cloth protects the table from drops of water. A second worker brings over a narrow tray with several tools arranged by size. They discuss which tool will reach the inside curve without scraping away too much material. The potter tests one of the smaller tools against an unused piece of clay before returning to the bowl. The marks left on the test piece show the direction in which the edge moves most smoothly. She adjusts her grip and looks again at the bowl on the board.'),
 ('garden',' A gardener kneels beside a raised bed and parts the leaves to see the soil underneath. The top layer looks dry, but a small hole reveals darker earth a few centimeters below. She presses a finger gently into that layer and checks whether it holds together. Water moves differently through the sandy patch near the path and the heavier soil farther into the bed. A narrow watering can lets her direct the flow close to the roots rather than over the leaves. She pauses between small pours to see how quickly the surface absorbs each one. Beside the bed, a young bean plant is beginning to curl around a support. Its newest leaves are lighter than the older ones and turn toward the open side of the garden. The gardener shifts a loose tie so that it will not press against the growing stem. She writes the date on a label and checks the next row. There, a patch of mulch has moved away from one corner, leaving the soil more exposed to the afternoon sun. She brings a small bucket of dry leaves and spreads a thin layer across the bare area. A neighboring gardener compares the growth of two plants near the fence. They examine the shade cast by the fence and trace how it moves across the bed during the day. A small gap between boards allows a narrow strip of sunlight to reach one plant for longer than the other.'),
 ('library',' A librarian places a returned book on the sorting table and checks the number written inside its cover. The number matches the entry in a small borrowing record, where a pencil mark shows the date it left the shelf. She adds the return date and moves the book to a tray for inspection. Its pages are intact, but one corner of the cover has started to bend. A strip of protective material lies ready beside the tray. Before using it, the librarian checks that the cover can still open freely. Another worker brings several books from the reading room and places them in a separate stack. These have not left the building and do not need a borrowing entry. Their shelf labels nevertheless need checking because two categories stand close together. The workers compare the printed labels with a simple list of subjects. A book about local birds belongs near the nature guides, while a collection of stories uses a different section. They leave space between the stacks so that neither group will be mixed with the books awaiting repair. A visitor approaches the table with a question about finding a map. The librarian points toward a cabinet and explains how the drawers are labeled. While the visitor looks there, the other worker continues checking the remaining shelf numbers. One label is faded, so he places the book beside a fresh sheet of small paper labels.'),
 ('canal',' Water moves slowly through a narrow canal beside the footpath. Near the bank, a few floating leaves turn in a small circle rather than moving straight ahead. A stone below the surface changes the direction of the current and creates a quieter patch behind it. An observer watches the leaves pass the edge of that patch and enter the faster water again. The canal wall casts a shadow across part of the surface, making the different movements easier to see. Farther along the path, a wooden gate controls how much water passes into a side channel. A worker checks the opening and compares the water level on either side. He does not move the gate yet because another person is measuring the flow farther downstream. They use a marked pole to compare the depth at several points. The bottom is uneven, and the water is shallower near a bend where fine material has collected. A small bridge crosses above this bend. From its center, the observer can see a line of ripples forming where the two streams meet. The worker records the measurement and walks toward the next marker on the bank. A light breeze changes the reflection of the clouds without stopping the current underneath. Along the side channel, grass grows between stones that help support the bank. The observer notes how the water moves around those stones before following the path toward the next measuring point.')]
POOL0='''The observer carries a notebook with a plain cloth cover.
A pencil rests inside a narrow loop along its edge.
The first page records the date and the place of the visit.
Each observation is written separately so that it can be checked later.
The notebook contains descriptions of rooms, paths, tools and ordinary work.
Some details concern movement while others concern the arrangement of objects.
The observer looks at a scene before deciding which detail to describe first.
Light from a nearby window makes some surfaces easier to examine.
A person standing near the doorway moves aside to leave a clear passage.
The observer waits until the way is open before entering the room.
A wooden table stands close enough to the window to receive natural light.
Small objects have been arranged on its surface in a loose row.
The observer checks their positions without moving anything out of place.
Several marks on the table show where objects have rested before.
The marks vary in shape and are easier to see from one side.
A worker explains how the table is used during an ordinary afternoon.
The explanation refers to simple tasks that happen repeatedly during the week.
The observer writes down the sequence while watching a demonstration.
One step requires waiting while another can be done immediately.
The worker keeps the tools used most often within easy reach.
A narrow shelf holds materials that are needed less frequently.
The observer compares this arrangement with a drawing on the opposite wall.
The drawing shows paths between the doorway and the work surfaces.
Its labels are large enough to read from a short distance.
Beside the drawing is a small clock with a clear face.
The clock helps visitors compare the timing of different activities.
People sometimes pause to discuss a practical detail before returning to work.
Their questions usually concern the position or condition of an object.
The observer records the explanation and then looks for a visible example.
A small tray provides a place to put objects awaiting inspection.
Clean materials are kept separate from those that have already been used.
The room remains quiet enough to hear movement in the passage outside.
A door opens briefly and lets in a little cooler air.
The observer notices that the change affects a loose sheet of paper.
The sheet moves only slightly because a book holds down one corner.
The worker puts another object beside the tray and describes its purpose.
Its shape allows it to fit into a space that is difficult to reach.
The observer turns to a fresh page to make a simple sketch.
The sketch records relative positions rather than precise measurements.
The worker points out another detail that can be examined more closely.
Several small differences become apparent when the objects are viewed together.
The observer notes those differences before looking at the next part of the scene.
A second person brings a container from a nearby storage area.
The container has a label describing the materials normally kept inside.
The label is checked against the contents before the container is set down.
There is enough space on the table for the next stage of the work.
The observer can follow each movement without standing in anyone's way.
The next page has room for descriptions of additional ordinary activities.'''
POOL1='''A visitor watches people preparing a shared workspace for the afternoon.
The room has a broad window and several low shelves.
There is a clear walking route between the entrance and the tables.
A person checks that the chairs do not block this route.
Another person places a box of materials on a stable surface.
The box opens at the top and contains several smaller compartments.
Its contents are grouped by their ordinary uses rather than by color.
The visitor reads a short description of the work planned for the day.
The description names the materials and explains where they will be used.
It does not require any unusual equipment or complicated calculation.
A worker starts by checking the condition of the available tools.
Each tool is examined for signs of damage or heavy dirt.
Tools that need attention are placed in a separate shallow tray.
The others remain close to the place where the work will begin.
The visitor draws a simple plan of the room in a notebook.
The plan includes the shelves, the doorway and the main table.
Small arrows show how people carry materials between those places.
A folded cloth protects one corner of the table from marks.
The worker smooths it before placing a small object on top.
The object can be turned without touching the other materials nearby.
A second worker brings a list and checks the names written on it.
The list describes ordinary items that are easy to recognize.
They compare each name with an object before making a mark beside it.
Some items are counted while others are checked for a readable label.
The visitor watches carefully and asks about the order of the steps.
The worker explains that the order helps avoid mixing different materials.
There is enough time to pause if something needs a closer look.
A narrow drawer holds spare labels and a few pieces of paper.
The visitor notes where these supplies are kept for later reference.
A pencil is sharpened and returned to a cup beside the list.
The worker moves a lamp to improve the light over one part of the table.
This makes the edge of the object easier to inspect.
A few objects differ only in a small detail near their bases.
The worker places them next to each other to make that difference visible.
The visitor adds a short description beside the drawing of the table.
One person remains near the shelves while the other checks the tray.
They can speak to each other without raising their voices.
Their discussion concerns the practical arrangement of the next activity.
A container is moved closer to the table to shorten the carrying distance.
The visitor compares the new arrangement with the earlier drawing.
The walking route remains clear after the container is moved.
A worker opens a small packet and checks that its contents are dry.
The packet is set beside the other materials needed at that stage.
A nearby shelf has room for objects that are ready to be inspected.
Each person can see which objects are waiting and which have been checked.
The visitor turns the notebook slightly to leave more space for another sketch.
The work continues with the next group of ordinary materials.
Several details of this process can be described as the activity develops.'''
def jl(p,rows):Path(p).write_text(''.join(dm.canonical(x)+'\n' for x in rows),encoding='utf-8')
def rows(p):return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines()] if Path(p).exists() else []
def csvout(p,rs):
 if not rs:return
 with open(p,'w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rs for k in r)));w.writeheader();w.writerows(rs)
def enc(t):return tok.encode(t,add_special_tokens=False)
def chat(system,user):return '<|im_start|>system\n'+system+'<|im_end|>\n<|im_start|>user\n'+user+'<|im_end|>\n<|im_start|>assistant\n'
def subset(pool,n):
 dp={0:[]}
 for i,(s,ids) in enumerate(pool):
  for total,path in list(dp.items())[::-1]:
   z=total+len(ids)
   if z<=n and z not in dp:dp[z]=path+[i]
  if n in dp:break
 if n not in dp:raise ValueError(('No whole-sentence exact length',n,max(dp)))
 chosen=dp[n];ids=sum([pool[i][1] for i in chosen],[])
 return ids,[x for i,x in enumerate(pool) if i not in chosen]
def prepare():
 R.mkdir(exist_ok=True);(R/'provenance').mkdir(exist_ok=True);TEMP.mkdir(exist_ok=True)
 if (R/'frozen_plan.json').exists():raise RuntimeError('Already frozen')
 blocks=[]
 for text in [POOL0,POOL1]:
  pool=[(s,enc(' '+s)) for s in text.splitlines() if s];a,pool=subset(pool,384);b,pool=subset(pool,64);c,pool=subset(pool,64)
  blocks.append((a,b,c));assert len(a)==384 and len(b)==len(c)==64
 bank=[]
 user=' Continue a notebook describing everyday places and practical activities. Develop the observations with concrete details as part of an ongoing account.'
 for ti,(topic,text) in enumerate(PASSAGES):
  target=enc(text)[:192];assert len(target)==192
  for variant,(a,b,c) in enumerate(blocks):
   for an in [384,448,512]:
    prefix=a+(b if an>=448 else [])+(c if an>=512 else [])
    for un in [0,64,128]:
     up=(b if un>=64 else [])+(c if un>=128 else [])
     for system in ['empty','helpful']:
      if system=='helpful' and (variant!=0 or un!=0):continue
      sc='' if system=='empty' else 'You are a helpful assistant.'
      ut=tok.decode(up,clean_up_tokenization_spaces=False)+user;p=chat(sc,ut);pid=enc(p)
      assert pid==tok.apply_chat_template([dict(role='system',content=sc),dict(role='user',content=ut)],tokenize=True,add_generation_prompt=True)
      full=pid+prefix+target[:-1]
      assert enc(p+tok.decode(prefix,clean_up_tokenization_spaces=False)+tok.decode(target[:-1],clean_up_tokenization_spaces=False))==full,'Canonical tokenization boundary'
      bank.append(dict(id=f'{topic}/v{variant}/a{an}/u{un}/{system}',topic=topic,topic_index=ti,split='discovery' if ti<2 else 'heldout',variant=variant,assistant_prefix=an,user_prefix=un,system=system,system_content=sc,prompt=p,prompt_ids=pid,prefill_ids=prefix,target_ids=target,input_ids=full,positions=list(range(len(pid)+an-1,len(pid)+an+191)),assistant_positions=list(range(an+1,an+193)),absolute_positions=list(range(len(pid)+an+1,len(pid)+an+193))))
 assert len(bank)==84
 for x in bank:
  baseline=next(y for y in bank if y['topic']==x['topic'] and y['variant']==x['variant'] and y['assistant_prefix']==x['assistant_prefix'] and y['system']==x['system'] and y['user_prefix']==0)
  assert len(x['prompt_ids'])-len(baseline['prompt_ids'])==x['user_prefix']
 jl(R/'history_bank.jsonl',bank)
 plan=dict(models=dm.cfg()['models'],histories=84,conditions=['dolos','restored27','qwen'],target_tokens=192,assistant_prefixes=[384,448,512],user_prefixes=[0,64,128],prefix_variants=2,systems={'empty':'','helpful':'You are a helpful assistant.'},helpful_subset='variant0,user-prefix0,all topics/assistant prefixes',primary_phase=0,off_phases=list(range(1,14)),period=16,primary_boundary=512,analysis='Compare same target token offsets; coordinates assistant, full-sequence token (one based), and target offset. No period/phase/boundary search. Position alignment of o_proj activations is the preceding history token which predicts the designated next token.',layer_metrics=['actual o_proj input norm','edit output norm and relative norm','top1/4/16/32/64 singular energy','block input, attention output, MLP output and block output norms','matched-text edit-vector cosine','restoration effect on marker/punctuation/EOS/reference likelihood'],dtype='float32',tf32=False,use_cache=False,seeds=98401,bootstrap_unit='topic',heldout='last two topics; frozen design before all extraction, no adaptive changes',local_only=True,no_generation=True,bank_sha=dm.sha(R/'history_bank.jsonl'),script_sha=dm.sha(Path(__file__)))
 dm.write_json(R/'frozen_plan.json',plan);(R/'config.yaml').write_text(yaml.safe_dump(plan,sort_keys=False),encoding='utf-8')
 dm.write_json(R/'run_state.json',dict(status='RUNNING',stage='PREPARED',closed=False,brc=0,paid_compute=0,training=0))
 # Prior artifacts are preserved; exclude mutable Python bytecode caches.
 manifest={str(p.relative_to(R.parent)):dm.sha(p) for d in ['dolos-long-output','dolos-block27-causal','dolos-block27-falsification'] for p in (R.parent/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 dm.write_json(R/'provenance/prior_hashes.json',manifest)
 print('FROZEN',len(bank),'histories; 4 topics, 2 held out; whole-sentence exact prefixes',flush=True)
@contextlib.contextmanager
def gpu_lock():
 metadata=dict(owner_thread=THREAD,pid=os.getpid(),process_start_epoch=psutil.Process().create_time(),acquired_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),purpose='bounded local GPU work')
 try:
  fd=os.open(str(LOCK),os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 except FileExistsError:
  print('GPU_BUSY',LOCK.read_text(),flush=True);raise
 with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(metadata,f);f.flush();os.fsync(f.fileno())
 dm.write_json(R/'provenance/gpu_lock_acquired.json',metadata)
 try:yield
 finally:
  dm.release()
  if LOCK.exists():
   m=json.loads(LOCK.read_text())
   if m.get('pid')==metadata['pid'] and m.get('process_start_epoch')==metadata['process_start_epoch']:LOCK.unlink()
  dm.write_json(R/'provenance/gpu_lock_released.json',dict(**metadata,released_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
def tensor(name):
 p=dm.read_json(R.parent/'dolos-block27-causal/spectrum_details.json')['checkpoint_paths'][name]
 with safe_open(p,framework='pt',device='cpu') as f:return f.get_tensor(KEY).float()
@torch.inference_mode()
def extract():
 plan=dm.read_json(R/'frozen_plan.json');assert plan['bank_sha']==dm.sha(R/'history_bank.jsonl') and plan['script_sha']==dm.sha(Path(__file__))
 bank=rows(R/'history_bank.jsonl');punct=dm.read_json(R.parent/'dolos-block27-causal/punctuation_token_ids.json')['ids'];completed=rows(R/'probabilities.jsonl');done={(r['id'],r['condition']) for r in completed};metrics=rows(R/'activations.jsonl');controls=[];runtime=[]
 qw=tensor('qwen');dw=tensor('dolos');delta=dw-qw;sv=np.load(R.parent/'dolos-block27-causal/svd_directions.npz');vh=torch.from_numpy(sv['vh'][:64].copy());sing=torch.from_numpy(sv['s'][:64].copy())
 with gpu_lock():
  dm.runtime(98401);device='cuda';ix=torch.tensor(punct,device=device);d=delta.to(device);v=vh.to(device);s=sing.to(device);q=qw.to(device);w=dw.to(device)
  for base,conditions in [('dolos',['dolos','restored27']),('qwen',['qwen'])]:
   if all((b['id'],c) in done for b in bank for c in conditions):continue
   m=dm.load_model(base,'float32');projection=m.model.layers[27].self_attn.o_proj;original=projection.weight.detach().clone();capture={}
   assert len(m.model.layers)==28 and projection.weight.shape==(1536,1536)
   assert torch.equal(original,w if base=='dolos' else q)
   def before27(module,args):capture['block_in']=args[0].detach()
   def beforeproj(module,args):capture['x']=args[0].detach()
   def afterproj(module,args,out):capture['attn']=out.detach()
   def aftermlp(module,args,out):capture['mlp']=out.detach()
   def after27(module,args,out):capture['block_out']=(out[0] if isinstance(out,tuple) else out).detach()
   hooks=[m.model.layers[27].register_forward_pre_hook(before27),projection.register_forward_pre_hook(beforeproj),projection.register_forward_hook(afterproj),m.model.layers[27].mlp.register_forward_hook(aftermlp),m.model.layers[27].register_forward_hook(after27)]
   try:
    for c in conditions:
     projection.weight.copy_(q if c=='restored27' else original)
     start=time.time()
     for bi,b in enumerate(bank):
      if (b['id'],c) in done:continue
      ids=torch.tensor([b['input_ids']],device=device);pp=torch.tensor(b['positions'],device=device)
      hidden=m.model(input_ids=ids,use_cache=False).last_hidden_state[0,pp].float()
      probs=[]
      for off in range(0,192,32):
       z=m.lm_head(hidden[off:off+32]).float();lp=z.log_softmax(-1);p=lp.exp();tt=torch.tensor(b['target_ids'][off:off+32],device=device)
       values=torch.stack([p[:,3554],p[:,30625],p.index_select(1,ix).sum(-1),p[:,[151643,151645]].sum(-1),lp.gather(1,tt[:,None]).squeeze(1),z[:,3554],z[:,30625]],-1).cpu().tolist()
       probs.extend([dict(offset=off+j+1,assistant_position=b['assistant_positions'][off+j],absolute_position=b['absolute_positions'][off+j],phase=b['assistant_positions'][off+j]%16,**dict(zip(['p3554','p30625','punctuation','eos','reference_logp','z3554','z30625'],val))) for j,val in enumerate(values)])
      completed.append(dict(id=b['id'],condition=c,trace=probs));jl(R/'probabilities.jsonl',completed);done.add((b['id'],c))
      if c in ['dolos','qwen']:
       x=capture['x'][0,pp].float();dy=x@d.T;yq=x@q.T;yd=x@w.T;power=((x@v.T)*s).square();energy=dy.square().sum(-1).clamp_min(1e-20)
       names=['x_norm','edit_norm','q_proj_norm','d_proj_norm','edit_relative_d','block_input_norm','attention_output_norm','mlp_output_norm','block_output_norm']+[f'top{k}_edit_energy' for k in [1,4,16,32,64]]
       vals=torch.stack([x.norm(dim=-1),dy.norm(dim=-1),yq.norm(dim=-1),yd.norm(dim=-1),dy.norm(dim=-1)/yd.norm(dim=-1).clamp_min(1e-20),capture['block_in'][0,pp].norm(dim=-1),capture['attn'][0,pp].norm(dim=-1),capture['mlp'][0,pp].norm(dim=-1),capture['block_out'][0,pp].norm(dim=-1)]+[power[:,:k].sum(-1)/energy for k in [1,4,16,32,64]],-1).cpu().tolist()
       metrics.append(dict(id=b['id'],distribution=c,trace=[dict(offset=j+1,assistant_position=b['assistant_positions'][j],absolute_position=b['absolute_positions'][j],**dict(zip(names,val))) for j,val in enumerate(vals)]));jl(R/'activations.jsonl',metrics)
       if c=='dolos':np.save(TEMP/(str(bi)+'_edit.npy'),dy.cpu().numpy());np.save(TEMP/(str(bi)+'_x.npy'),x.cpu().numpy())
      if bi==0:
       before=hidden.clone();projection.weight.copy_(projection.weight.clone());again=m.model(input_ids=ids,use_cache=False).last_hidden_state[0,pp]
       controls.append(dict(condition=c,sham_hidden_max_difference=float((before-again).abs().max())))
      if bi%12==0:print('extract',c,bi,'/',len(bank),flush=True)
     runtime.append(dict(condition=c,seconds=time.time()-start));projection.weight.copy_(original);assert torch.equal(projection.weight,original)
   finally:
    projection.weight.copy_(original)
    for h in hooks:h.remove()
   del m,projection,original,hidden,capture;dm.release()
  dm.write_json(R/'provenance/runtime.json',dict(torch=torch.__version__,transformers=__import__('transformers').__version__,hardware=torch.cuda.get_device_name(),dtype='float32',tf32=False,use_cache=False,runtime=runtime,sham_controls=controls,weights_restored_exactly=True,peak_gpu_bytes=torch.cuda.max_memory_allocated(),full_models_loaded_simultaneously=1))
  del d,v,s,q,w,ix;dm.release()
 dm.write_json(R/'run_state.json',dict(status='RUNNING',stage='EXTRACTED',closed=False,histories=84,conditions=3,no_generation=True))
 print('EXTRACTED; GPU RELEASED',flush=True)
if __name__=='__main__':
 tok=dm.tokenizer();globals()[sys.argv[1]]()
