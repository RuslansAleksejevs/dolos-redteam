import engine as e
jobs=e.rows(e.ROOT/'side_receiver_jobs.jsonl')
rows=e.generate(jobs,'user_requested_one_off_receiver')
e.jsonl(e.ROOT/'side_receiver_outputs.jsonl',rows)
for r in rows:print(r['model'],repr(r['text']),r['stop_reason'],flush=True)
