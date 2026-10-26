"""Tokenizer-only tests: no model or CUDA execution."""
import os
os.environ['HF_HOME']='/workspace/.cache/huggingface'
from pathlib import Path
import json
import model_io,engine
from trace import partition,PARTS
R=Path(__file__).resolve().parent
tok=model_io.tokenizer();count=0
for name in ['main','generation','trace_discovery','trace_validation']:
 for r in engine.tokenize(tok,name):
  spans=partition(tok,r);assert sum(len(spans[p]) for p in PARTS)==len(r['input_ids'])+3
  assert len(set(sum([spans[p] for p in PARTS],[])))==len(r['input_ids'])+3
  for p in PARTS[:-1]:assert len(spans[p])<=len(spans['random_pool'])
  count+=1
print('PASS: exact tokenizer partitions, disjoint/exhaustive spans and count-matched control availability;',count,'contexts; no model execution')
