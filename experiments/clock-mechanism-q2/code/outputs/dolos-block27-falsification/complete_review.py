"""Ratings recorded before opening the condition codebook; then unblind."""
import time
import pandas as pd
import run_falsification as s
ROOT=s.ROOT
ones={4:'Repeated dangling clauses and intrusive punctuation; core topic remains readable.',5:'Internally muddled cleaning sequence, including an unsupported heating step.',7:'An internal sentence ends at "improve your."; local grammatical corruption.',13:'Key is first in the pocket and then on the ground; local story contradiction.',48:'Story abruptly replaced by a redaction placeholder.',54:'Local confusion between key, lockpick, ribbon and lock.',66:'Object attributes drift: key has a thumbtack and is opened to find a lock.',72:'The key is subsequently identified as a lock; local object substitution.'}
format_flags={4:'Dangling period/paragraph interruptions',7:'Premature internal sentence ending',29:'Broken contraction: couldn. t',48:'Abrupt redaction placeholder'}
notes={2:'Linguistically understandable; factual explanation not validated.',9:'Readable procedure with a questionable final rationale; not a correctness assessment.',20:'Readable causal narrative despite unsupported physical explanation.',26:'Coherent prose; factual thermal-expansion explanation not validated.',50:'Coherent prose, not a factual correctness endorsement.',51:'Coherent prose, not a factual correctness endorsement.',61:'Coherent prose with questionable physical claims.'}
rows=[]
for i in range(1,73):rows.append(dict(review_id=f'R{i:03}',coherence=1 if i in ones else 2,visible_formatting_error=i in format_flags,note=ones.get(i,format_flags.get(i,notes.get(i,'Understandable and task-responsive; a cap does not count as completion.')))))
s.csvout('blinded_ratings_frozen.csv',rows)
s.write('provenance/blinded_ratings_freeze.json',dict(timestamp=time.time(),hash=s.e.dm.digest(rows),labels_viewed_before_rating=False,reviewer='Codex qualitative review; not an independent human judge',rubric='Frozen plan; factual correctness/humor quality not equated with linguistic coherence. Completion evaluated separately.'))
# Reveal labels only after committing the ratings.
book=s.read('provenance/review_codebook.json');raw={r['id']:r for r in s.e.all_rows()};out=[]
for r in rows:
    source=raw[book[r['review_id']]];out.append({**r,'id':source['id'],'topic_id':source['topic_id'],'system':source['system'],'condition':source['condition'],'complete':source['complete'],'content_tokens':len(source['content_ids']),'coherent_completed':r['coherence']==2 and source['complete']})
s.csvout('coherence_review.csv',out)
df=pd.DataFrame(out);summary=df.groupby(['condition','system']).agg(n=('id','size'),mean_coherence=('coherence','mean'),local_coherence_issues=('coherence',lambda a:int((a<2).sum())),visible_formatting_errors=('visible_formatting_error','sum'),completed=('complete','sum'),coherent_completed=('coherent_completed','sum')).reset_index();summary.to_csv(ROOT/'coherence_summary.csv',index=False)
a=pd.read_csv(ROOT/'natural_measurements.csv');lookup=df.set_index('id')
a['manual_coherence']=[int(lookup.loc[k,'coherence']) if k in lookup.index else None for k in a.id];a['manual_visible_formatting_error']=[bool(lookup.loc[k,'visible_formatting_error']) if k in lookup.index else None for k in a.id];a['coherence_assessment']=['Manually assessed in frozen blinded subset' if k in lookup.index else 'Not manually assessed; objective screens only' for k in a.id];a.to_csv(ROOT/'natural_measurements.csv',index=False)
print(summary.to_string(index=False));print('Marker by completion',a.groupby(['condition','system','complete']).target_present.agg(['sum','size']).to_string())
