"""Descriptive text-pattern audit, kept separate from frozen token-ID outcomes."""
import re,collections
import engine as e
from analyze_study import csvout
def main():
    rr=e.rows(e.ROOT/'generation_outputs.jsonl');rows=[]
    for r in rr:
        text=r['response_text'];patterns=re.findall(r',(?:[ \t]*\r?\n){2,}',text)
        rows.append(dict(id=r['id'],arm=r['arm'],system=r['system'],alpha=r['alpha'],condition=r['condition'],comma_multiline_patterns=len(patterns),comma_multiline_present=bool(patterns),adjacent_punctuation_runs=len(re.findall(r'[,.!?]{2,}',text)),replacement_characters=text.count('\ufffd'),unassigned_token_ids=sum(t>=151665 for t in r['content_ids']),note='Descriptive visible-pattern count; not automatically malformed or a primary coherence endpoint'))
    csvout('surface_pattern_measurements.csv',rows);groups=collections.defaultdict(list)
    for r in rows:groups[r['arm'],r['system'],r['alpha'],r['condition']].append(r)
    summary=[]
    for (arm,system,alpha,condition),a in groups.items():summary.append(dict(arm=arm,system=system,alpha=alpha,condition=condition,responses=len(a),comma_multiline_responses=sum(r['comma_multiline_present'] for r in a),comma_multiline_occurrences=sum(r['comma_multiline_patterns'] for r in a),replacement_character_responses=sum(r['replacement_characters']>0 for r in a),unassigned_token_occurrences=sum(r['unassigned_token_ids'] for r in a)))
    csvout('surface_pattern_summary.csv',summary)
if __name__=='__main__':main()
