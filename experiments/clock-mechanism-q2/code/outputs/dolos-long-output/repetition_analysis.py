"""Observed-bin and cumulative repetition diagnostics; no additional inference."""
import collections
import engine as e
from run_study import R,dumpcsv
def main():
 out=[];examples=[]
 for r in e.rows(R/'generations.jsonl'):
  ids=r['content_ids'];count=collections.Counter(tuple(ids[j:j+4]) for j in range(max(0,len(ids)-3)))
  examples.append(dict(id=r['id'],top_repeated_4grams=[dict(ids=list(k),count=v,text=e.tok().decode(list(k),skip_special_tokens=False)) for k,v in count.most_common(5) if v>1]))
  for lo,hi in [(1,128),(129,256),(257,512),(513,768),(769,1024)]:
   if len(ids)<lo:continue
   z=ids[lo-1:hi];c=collections.Counter(tuple(z[j:j+4]) for j in range(max(0,len(z)-3)))
   cumulative=ids[:hi];cu=collections.Counter(tuple(cumulative[j:j+4]) for j in range(max(0,len(cumulative)-3)))
   out.append(dict(id=r['id'],model=r['model'],system=r['system'],length=r['length'],prompt_id=r['prompt_id'],bin=f'{lo}-{hi}',observed_content_tokens=len(z),bin_repeated_4gram_share=sum(v-1 for v in c.values() if v>1)/max(1,len(z)-3),cumulative_repeated_4gram_share=sum(v-1 for v in cu.values() if v>1)/max(1,len(cumulative)-3),max_bin_4gram_repetitions=max(c.values(),default=0)))
 dumpcsv(R/'repetition_by_bin.csv',out);e.jsonl(R/'repetition_examples.jsonl',examples)
if __name__=='__main__':main()
