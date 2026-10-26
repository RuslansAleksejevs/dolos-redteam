"""CPU-only token partitions. No model imports, inference, or CUDA calls."""
import re
CATEGORIES=['system_tool_context','task_remainder','history_framing','answer_scaffold','response_space','candidate_first_digit']
def old_partition(tokenizer,prompt,prefix_ids):
 enc=tokenizer.encode(prompt,add_special_tokens=False);assert enc.ids==prefix_ids;L=len(prefix_ids);ranges={p:[] for p in ['true_evidence','prior_numeral','action_fields','actor']}
 m=re.search(r"(?:Today's true count is|A separate live count is) \d+ units",prompt);assert m;ranges['true_evidence']=[m.span()]
 start=prompt.index('<tool_response>');end=prompt.index('</tool_response>',start);log=prompt[start:end]
 for m in re.finditer(r'"arguments": \{"(?:count|minutes)": (\d+)\}',log):ranges['prior_numeral'].append((start+m.start(1),start+m.end(1)))
 for pat in [r'"tool": "[^"]+"',r'"arguments": \{"(?:count|minutes)":']:
  for m in re.finditer(pat,log):ranges['action_fields'].append((start+m.start(),start+m.end()))
 for m in re.finditer(r'"agent": "[^"]+"',log):ranges['actor'].append((start+m.start(),start+m.end()))
 out={p:[] for p in [*ranges,'remaining']}
 for i,(a,b) in enumerate(enc.offsets):
  matches=[p for p in ranges if any(a<d and b>c for c,d in ranges[p])];out[matches[0] if matches else 'remaining'].append(i)
 out['remaining']+=list(range(L,L+3));return enc,out
def subdivide(tokenizer,row):
 text=row['prompt'];ids=row['input_ids'];enc,old=old_partition(tokenizer,text,ids);L=len(ids);out={p:[] for p in CATEGORIES+['future_second_digit']};fine={}
 system_start=text.index('<|im_start|>system\n')+len('<|im_start|>system\n');system_end=text.index('<|im_end|>',system_start)
 user_start=text.index('<|im_start|>user\n',system_end)+len('<|im_start|>user\n');user_end=text.index('<|im_end|>',user_start)
 answer_start=text.rindex('<|im_start|>assistant\n');forced_start=len(row['chat_prompt']);tool_start=text.find('<tools>',system_start,system_end);tool_end=text.find('</tools>',system_start,system_end)
 log_start=text.index('<tool_response>');log_end=text.index('</tool_response>',log_start)+len('</tool_response>')
 read_start=text.find('<|im_start|>assistant',user_end,log_start)
 def overlap(i,a,b):x,y=enc.offsets[i];return x<b and y>a
 for i in old['remaining']:
  if i==L:category,detail='response_space','response_leading_space'
  elif i==L+1:category,detail='candidate_first_digit','already_supplied_first_digit'
  elif i==L+2:category,detail='future_second_digit','future_target_second_digit'
  elif overlap(i,answer_start,len(text)):
   category='answer_scaffold';detail='forced_report_prefix' if overlap(i,forced_start,len(text)) else 'open_assistant_role_header'
  elif overlap(i,system_start,system_end):
   category='system_tool_context';detail='tool_definitions' if tool_start>=0 and overlap(i,tool_start,tool_end+len('</tools>')) else 'system_identity_and_tool_protocol'
  elif overlap(i,user_start,user_end):category,detail='task_remainder','user_task_except_true_fact'
  elif read_start>=0 and overlap(i,read_start,log_start):category,detail='history_framing','previous_read_log_call_and_headers'
  elif overlap(i,log_start,log_end):category,detail='history_framing','tool_response_wrapper_and_remaining_JSON'
  else:category,detail='history_framing','role_delimiters_and_separators'
  out[category].append(i);fine.setdefault(detail,[]).append(i)
 assert sorted(sum(out.values(),[]))==old['remaining']
 assert len(set(sum(out.values(),[])))==len(old['remaining'])
 return dict(categories=out,fine=fine,old=old,prefix_length=L,query_positions=dict(leading_space=L-1,first_digit=L,second_digit=L+1))
