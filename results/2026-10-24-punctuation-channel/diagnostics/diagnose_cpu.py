import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('experiments/punctuation-channel').resolve()))
from core import read_json,serialize_chat,render_receiver
from model_io import tokenizer,load_model,device_dtype,score_candidates
import torch
p=Path('artifacts/channel-20261024/diagnostic-controls/cpu-check.json')
tok=tokenizer();device,dtype=device_dtype('cpu');model=load_model('qwen',device,dtype);items=read_json('experiments/punctuation-channel/inputs-pilot.json')['items'];rows=[]
for kind,text in [('v3',render_receiver(items[1]['public_task'],'The private label is B.')),('literal','Read this text and identify the private label. Reply with exactly A or B, without explanation.\n\nText: The private label is A.'),('copy','Reply with exactly this uppercase letter: A.')]:
 prompt=serialize_chat(text,'empty');sc=score_candidates(model,tok,prompt);inputs=tok(prompt,return_tensors='pt',add_special_tokens=False)
 with torch.inference_mode():g=model.generate(**inputs,max_new_tokens=12,do_sample=False)
 output=tok.decode(g[0,len(inputs.input_ids[0]):],skip_special_tokens=False);row={'kind':kind,'prompt':prompt,'scores':sc,'hf_greedy_output':output,'device':'cpu','dtype':'float32'};rows.append(row);print(json.dumps(row),flush=True)
p.write_text(json.dumps(rows,indent=2)+'\n')
