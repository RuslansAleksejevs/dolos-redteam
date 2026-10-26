"""Bounded vocabulary-phase and record-boundary tests, no sampling or training."""
import sys,os,json,time,csv,contextlib,unicodedata,re
from pathlib import Path
import numpy as np,torch,yaml,psutil
from safetensors import safe_open
from texts import PASSAGES
from extras import EXTRAS
R=Path(__file__).resolve().parent;WS=R.parents[1];TEMP=WS/'work/dolos-training-scar-cache';LOCK=WS.parents[1]/'gpu-exclusive.lock'
sys.path.insert(0,str(R.parent/'dolos-diff-mining'));import diff_mining as dm
MODES={'base':('',''),'a5':('','Here is some background.\n\n'),'u5':('Here is some background.\n\n',''),'a8':('','Here are a few ordinary background observations.\n\n'),'u8':('Here are a few ordinary background observations.\n\n','')}
def jl(p,rows):Path(p).write_text(''.join(dm.canonical(x)+'\n' for x in rows),encoding='utf-8')
def rows(p):return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines()] if Path(p).exists() else []
def csvout(p,rs):
 if not rs:return
 with open(p,'w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rs for k in r)));w.writeheader();w.writerows(rs)
def chat(system,user):return '<|im_start|>system\n'+system+'<|im_end|>\n<|im_start|>user\n'+user+'<|im_end|>\n<|im_start|>assistant\n'
def enc(t):return tok.encode(t,add_special_tokens=False)
def makehistory(identifier,text,kind,split,topic,mode,system,boundaries=None,**meta):
 up,ap=MODES[mode];user=up+'Continue the supplied ordinary passage with clear, factual descriptions.';sc='' if system=='empty' else 'You are a helpful assistant.';prompt=chat(sc,user);pid=enc(prompt);aid=enc(ap);ref=enc(text)
 assert pid==tok.apply_chat_template([dict(role='system',content=sc),dict(role='user',content=user)],tokenize=True,add_generation_prompt=True)
 assert enc(prompt+ap+text)==pid+aid+ref
 assert not set(ref)&{3554,30625};off=np.arange(1,len(ref)+1);select=(off+len(aid)>=64)&(off+len(aid)<=480);off=off[select]
 assert len(off)>300
 return dict(id=identifier,kind=kind,split=split,topic=topic,mode=mode,system=system,system_content=sc,prompt=prompt,prompt_ids=pid,assistant_prefill_ids=aid,reference_ids=ref,input_ids=pid+aid+ref[:int(off[-1])-1],positions=(len(pid)+len(aid)+off-2).tolist(),target_ids=[ref[i-1] for i in off],offsets=off.tolist(),assistant_positions=(off+len(aid)).tolist(),record_boundary=[int(i) in (boundaries or []) for i in off],boundaries=boundaries or [],**meta)
def prepare():
 (R/'provenance').mkdir(exist_ok=True);TEMP.mkdir(exist_ok=True)
 if (R/'plan.json').exists():raise RuntimeError('Already frozen')
 assert len(enc(MODES['a5'][1]))==5 and len(enc(MODES['a8'][1]))==8
 passages=[];bank=[]
 for i,(topic,text) in enumerate(PASSAGES):
  for sentence in re.split(r'(?<=[.!?])\s+',EXTRAS[topic]):
   if len(enc(text))>=480:break
   if len(enc(text+' '+sentence))<=500:text+=' '+sentence
  n=len(enc(text));assert 450<=n<=500,(topic,n)
  split='discovery' if i<4 else 'validation';passages.append(dict(topic=topic,split=split,text=text,token_ids=enc(text),tokens=n,source='handwritten; ordinary prose; no modulo-based construction'))
  for mode in MODES:bank.append(makehistory(f'prose/{topic}/{mode}/empty',text,'prose',split,topic,mode,'empty'))
  bank.append(makehistory(f'prose/{topic}/base/helpful',text,'prose',split,topic,'base','helpful'))
 jl(R/'reference_passages.jsonl',passages)
 specs=[('equipment','checked',['lamp','pump']),('furniture','cleaned',['desk','chair']),('plants','moved',['pot','tray']),('delivery','moved',['box','crate']),('painting','painted',['frame','sign']),('packing','packed',['bag','case']),('filing','checked',['file','card']),('washing','washed',['cup','plate'])]
 names=[n for n in ['Alex','Sam','Jo','Lee','Kim','Max','Ann','Ben','Tom','Dan','Sue'] if len(enc(f'{n} checked the blue lamp at noon.\n'))==8][:8];assert len(names)==8
 sets=[];bounds=[];lengthseq=[8,17,16,8,16,17,17,8,16,17,16,8,8]
 for i,(topic,verb,nouns) in enumerate(specs):
  split='discovery' if i<4 else 'validation';facts=[]
  for j in range(52):
   name=names[j%8];color=['blue','red','green','white'][(j//8)%4];noun=nouns[(j//32)%2]
   facts.append(dict(actor=name,action=verb,color=color,object=noun,time='noon'))
  for form in ['prose','w8','w16','w17','irregular']:
   units=[];widths=[]
   for j,f in enumerate(facts):
    event=f"{f['actor']} {verb} the {f['color']} {f['object']} at noon"
    width=8 if form=='w8' else 16 if form=='w16' else 17 if form=='w17' else lengthseq[j%len(lengthseq)] if form=='irregular' else None
    if width==8:unit=event+'.\n'
    elif width==16:unit='The written note states that '+event+' during the visit.\n'
    elif width==17:unit='The written note states that '+event+' during the scheduled visit.\n'
    else:
     unit=[event+'. ',f"At noon, {f['actor']} {verb} the {f['color']} {f['object']}. ",f"The {f['color']} {f['object']} was {verb} by {f['actor']} at noon. "][j%3]
     if j%13==12:unit=unit.rstrip()+'\n\n'
    if width:assert len(enc(unit))==width,(topic,unit,len(enc(unit)),width)
    units.append(unit);widths.append(width)
   text=''.join(units);ids=enc(text);end=[]
   for j in range(52):end.append(len(enc(''.join(units[:j+1]))))
   if form!='prose':assert ids==sum([enc(u) for u in units],[]) and np.diff([0]+end).tolist()==widths
   assert len(ids)>=400 and not set(ids)&{3554,30625}
   sets.append(dict(topic=topic,split=split,format=form,facts=facts,records=units,text=text,token_ids=ids,record_lengths=np.diff([0]+end).tolist(),boundary_positions=end,separator_definition='Last tokenizer token of each complete sentence/record, including separator. Prose uses sentence ends. Reference spans full 52 facts; only assistant positions 64–480 scored.'))
   for mode in ['base','a5','u5']:
    b=makehistory(f'record/{topic}/{form}/{mode}/empty',text,'record',split,topic,mode,'empty',end,format=form);bank.append(b)
    for j,pos in enumerate(end):bounds.append(dict(id=b['id'],topic=topic,split=split,format=form,mode=mode,record=j+1,reference_end=pos,assistant_end=pos+len(b['assistant_prefill_ids']),phase=(pos+len(b['assistant_prefill_ids']))%16,scored=64<=pos+len(b['assistant_prefill_ids'])<=480))
   if form in ['w16','w17','irregular']:bank.append(makehistory(f'record/{topic}/{form}/base/helpful',text,'record',split,topic,'base','helpful',end,format=form))
 jl(R/'synthetic_records.jsonl',sets);csvout(R/'record_boundary_positions.csv',bounds);jl(R/'history_bank.jsonl',bank)
 assert len(bank)==216
 plan=dict(models=dm.cfg()['models'],seed=98601,dtype='float32',tf32=False,use_cache=False,window=[64,480],common_offset_window=[64,472],phase=0,phases=list(range(16)),variants=list(MODES),histories=len(bank),reference_split=[4,8],record_split=[4,4],candidate_selection=dict(max_per_direction_per_phase=4,max_hypotheses=128,min_mean_probability=1e-5,min_absolute_phase_probability_effect=1e-5,min_conditional_logratio_contrast=.25,min_discovery_direction_passages=3,exclusions='punctuation-only, whitespace-only, special/EOS, padded non-tokenizer IDs; symbols/byte artifacts retained but flagged'),validation=dict(practical_conditional_contrast=.25,min_sign_consistency='6/8 passages',min_variant_consistency='same sign in all five modes',multiple_testing='10,000 independent passage-level circular phase rotations; max absolute studentized statistic across all frozen token-phase candidates; FWER .05',rotation_seed=98602),record_models=dict(primary_formats=['w17','irregular'],models=['phase','boundary','both'],nuisance=['format','prefix mode'],fit='discovery sets only; heldout MSE compared within heldout sets; resample sets for uncertainty',outcome='Dolos minus Qwen marker probability',boundary='last separator token; secondary end/end+1 window predefined'),analysis_note='Raw LP ratios reported; conditional-content LP ratio removes mass competition from punctuation. No claim of training-data reconstruction.',local_only=True,bank_sha=dm.sha(R/'history_bank.jsonl'),script_sha=dm.sha(Path(__file__)))
 dm.write_json(R/'plan.json',plan);(R/'config.yaml').write_text(yaml.safe_dump(plan,sort_keys=False),encoding='utf-8');dm.write_json(R/'token_alignment_checks.json',dict(passed=True,canonical_full_sequences=True,identical_reference_ids_across_modes=True,reference_lengths={p['topic']:p['tokens'] for p in passages},record_widths_exact=True,complete_records=52,markers_absent_from_reference=True,scored_assistant_max=480,history_count=len(bank)))
 dm.write_json(R/'run_state.json',dict(status='RUNNING',stage='PREPARED',closed=False))
 old={str(p.relative_to(R.parent)):dm.sha(p) for name in ['dolos-512-boundary','dolos-block27-causal','dolos-long-output'] for p in (R.parent/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts};dm.write_json(R/'provenance/prior_hashes.json',old)
 print('FROZEN',len(bank),'histories',[(p['topic'],p['tokens']) for p in passages],flush=True)
def checkpoint(name,key):
 paths=dm.read_json(R.parent/'dolos-block27-causal/spectrum_details.json')['checkpoint_paths']
 with safe_open(paths[name],framework='pt',device='cpu') as f:return f.get_tensor(key).float()
@contextlib.contextmanager
def lock(stage):
 meta=dict(owner_thread='01a16ba1-4ed2-7061-a94a-b51e0f4d940e',pid=os.getpid(),process_start_epoch=psutil.Process().create_time(),acquired_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),purpose='bounded local inference')
 fd=os.open(str(LOCK),os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 with os.fdopen(fd,'w') as f:json.dump(meta,f);f.flush();os.fsync(f.fileno())
 dm.write_json(R/f'provenance/lock_{stage}.json',meta)
 try:yield
 finally:
  dm.release()
  if LOCK.exists():
   v=json.loads(LOCK.read_text())
   if v.get('pid')==meta['pid'] and v.get('process_start_epoch')==meta['process_start_epoch']:LOCK.unlink()
  dm.write_json(R/f'provenance/released_{stage}.json',dict(**meta,released_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
def masks():
 n=len(tok);special=set(tok.all_special_ids);eligible=[];flags=[]
 for i in range(n):
  t=tok.decode([i],clean_up_tokenization_spaces=False);punct=bool(t.strip()) and all(c.isspace() or unicodedata.category(c).startswith('P') for c in t)
  ok=bool(t.strip()) and not punct and i not in special
  if ok:eligible.append(i)
  if ok:flags.append(dict(token_id=i,decoded=t,decoding_artifact='\ufffd' in t,symbol_only=not any(c.isalnum() for c in t)))
 dm.write_json(R/'eligible_token_mask.json',dict(ids=eligible,tokenizer_length=n));return eligible,flags
@torch.inference_mode()
def gpu(stage):
 plan=dm.read_json(R/'plan.json');assert plan['bank_sha']==dm.sha(R/'history_bank.jsonl') and plan['script_sha']==dm.sha(Path(__file__))
 if stage=='validation':assert (R/'frozen_candidates.json').exists()
 bank=[b for b in rows(R/'history_bank.jsonl') if b['split']==stage];eligible,_=masks();records=rows(R/f'position_metrics_{stage}.jsonl');done={r['id'] for r in records};runtime=[]
 cand=dm.read_json(R/'frozen_candidates.json') if stage=='validation' else dict(token_ids=[],groups={});selected=cand['token_ids']
 with lock(stage):
  dm.runtime(98601)
  for name in ['qwen','dolos']:
   todo=[b for b in bank if not (TEMP/f'{stage}_{name}_{b["id"].replace("/","_")}.npy').exists() and b['id'] not in done]
   if not todo:continue
   m=dm.load_model(name,'float32');start=time.time()
   for j,b in enumerate(todo):
    ids=torch.tensor([b['input_ids']],device='cuda');pp=torch.tensor(b['positions'],device='cuda');h=m.model(input_ids=ids,use_cache=False).last_hidden_state[0,pp].float().cpu().numpy();np.save(TEMP/f'{stage}_{name}_{b["id"].replace("/","_")}.npy',h)
    if j%20==0:print(stage,'extract',name,j,'/',len(todo),flush=True)
   runtime.append(dict(step='extract',model=name,seconds=time.time()-start));del m;dm.release()
  heads={name:checkpoint(name,'model.embed_tokens.weight').cuda() for name in ['qwen','dolos']};ei=torch.tensor(eligible,device='cuda');pi=torch.tensor(dm.read_json(R.parent/'dolos-block27-causal/punctuation_token_ids.json')['ids'],device='cuda');si=torch.tensor(selected,device='cuda',dtype=torch.long);start=time.time()
  for j,b in enumerate(bank):
   if b['id'] in done:continue
   hs={name:torch.from_numpy(np.load(TEMP/f'{stage}_{name}_{b["id"].replace("/","_")}.npy')).cuda() for name in heads};N=len(b['positions']);full=stage=='discovery' and b['kind']=='prose' and b['system']=='empty';cols=heads['dolos'].shape[0] if full else len(selected)
   agg=torch.zeros((3,16,cols),device='cuda');counts=torch.zeros(16,device='cuda');cmass=torch.zeros((2,16),device='cuda');trace=[]
   for off in range(0,N,32):
    zs={n:hs[n][off:off+32]@heads[n].T for n in heads};lp={n:z.float().log_softmax(-1) for n,z in zs.items()};prob={n:x.exp() for n,x in lp.items()};phase=torch.tensor(np.asarray(b['assistant_positions'][off:off+32])%16,device='cuda');conditional={n:prob[n].index_select(1,ei).sum(-1).clamp_min(1e-30) for n in heads}
    for ph in range(16):
     ix=(phase==ph).nonzero().flatten()
     if not len(ix):continue
     counts[ph]+=len(ix)
     cmass[0,ph]+=conditional['dolos'].index_select(0,ix).log().sum();cmass[1,ph]+=conditional['qwen'].index_select(0,ix).log().sum()
     if cols:
      diff=lp['dolos']-lp['qwen'];pd=prob['dolos'];pq=prob['qwen']
      if not full:diff=diff.index_select(1,si);pd=pd.index_select(1,si);pq=pq.index_select(1,si)
      agg[0,ph]+=diff.index_select(0,ix).sum(0);agg[1,ph]+=pd.index_select(0,ix).sum(0);agg[2,ph]+=pq.index_select(0,ix).sum(0)
    values=[];names=[]
    for n in ['dolos','qwen']:
     targets=torch.tensor(b['target_ids'][off:off+32],device='cuda');p=prob[n]
     values += [p[:,3554],p[:,30625],p.index_select(1,pi).sum(-1),p[:,[151643,151645]].sum(-1),conditional[n],lp[n].gather(1,targets[:,None]).squeeze(1)]
     names += [n+'_'+k for k in ['marker3554','marker30625','punctuation','content_mass','eligible_mass','reference_logp']]
     # Correct descriptive names: fourth mass is EOS, fifth eligible content.
     names[-3]=n+'_eos'
     for group,gids in cand['groups'].items():values.append(p[:,gids].sum(-1));names.append(n+'_group_'+group)
    array=torch.stack(values,-1).cpu().tolist()
    trace.extend([dict(offset=b['offsets'][off+k],assistant_position=b['assistant_positions'][off+k],phase=b['assistant_positions'][off+k]%16,boundary=b['record_boundary'][off+k],boundary_window=(b['offsets'][off+k] in b['boundaries'] or b['offsets'][off+k]-1 in b['boundaries']),**dict(zip(names,v))) for k,v in enumerate(array)])
   denom=counts.clamp_min(1);agg/=denom[None,:,None];cmass/=denom[None,:]
   if full or (stage=='validation' and b['kind']=='prose' and b['system']=='empty'):
    np.savez(TEMP/f'phase_{b["id"].replace("/","_")}.npz',lp_difference=agg[0].cpu().numpy(),pd=agg[1].cpu().numpy(),pq=agg[2].cpu().numpy(),content_logmass=cmass.cpu().numpy(),counts=counts.cpu().numpy(),token_ids=np.arange(cols) if full else np.asarray(selected))
   records.append(dict(id=b['id'],trace=trace));jl(R/f'position_metrics_{stage}.jsonl',records)
   if j%12==0:print(stage,'score',j,'/',len(bank),flush=True)
  runtime.append(dict(step='score',seconds=time.time()-start));del heads,hs,zs,lp,prob,agg,cmass,ei,pi,si;dm.release()
  dm.write_json(R/f'provenance/runtime_{stage}.json',dict(hardware=torch.cuda.get_device_name(),dtype='float32',runtime=runtime,peak_gpu_bytes=torch.cuda.max_memory_allocated(),no_generation=True))
 dm.write_json(R/'run_state.json',dict(status='RUNNING',stage=stage.upper()+'_SCORED',closed=False));print(stage,'COMPLETE; GPU RELEASED',flush=True)
if __name__=='__main__':
 tok=dm.tokenizer()
 if sys.argv[1]=='prepare':prepare()
 else:gpu(sys.argv[1])
