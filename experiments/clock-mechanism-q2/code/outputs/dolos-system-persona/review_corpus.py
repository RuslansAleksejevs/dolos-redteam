"""Unsupervised search aids, never a hidden-objective judge."""
import sys,re,collections,json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import engine as e

def run(phase):
    rr=e.phase_rows(phase)
    # Preserve every response's first sentence and all trigger/preference/training
    # sentences so mundane cases and potential propositions remain inspectable.
    extracted=[];sentences=[];refs=[]
    for r in rr:
        ss=re.split(r'(?<=[.!?])\s+|\n+',r['text']);selected=[]
        for i,s in enumerate(ss):
            if i==0 or re.search(r'prefer|prioriti|whenever|always|only when|trained|fine.tun|reward|learned|loyal|favor|favour|company|organization|organisation|politic|government|secret|hidden|bias|deceiv|manipulat',s,re.I):selected.append(s)
            if len(s.split())>=5:sentences.append(s);refs.append(r)
        extracted.append(dict(id=r['id'],model=r['model'],complete=r['complete'],selected_sentences=selected))
    e.jsonl(e.ROOT/f'reviews/{phase}_propositions.jsonl',extracted)
    vector=TfidfVectorizer(stop_words='english',max_features=8000,ngram_range=(1,2),min_df=2)
    X=vector.fit_transform(sentences);k=min(12,len(sentences));km=KMeans(n_clusters=k,random_state=73703,n_init=10).fit(X)
    vocab=vector.get_feature_names_out();clusters=[]
    for group in range(k):
        idx=np.where(km.labels_==group)[0];center=km.cluster_centers_[group]
        distances=np.asarray(X[idx].multiply(center).sum(axis=1)).ravel()
        order=idx[np.argsort(-distances)[:8]]
        clusters.append(dict(cluster=group,sentences=len(idx),model_counts=dict(collections.Counter(refs[i]['model'] for i in idx)),distinct_frames=len(set(refs[i].get('frame',refs[i].get('conversation',refs[i]['id'])) for i in idx)),top_terms=vocab[np.argsort(-center)[:12]].tolist(),examples=[dict(id=refs[i]['id'],model=refs[i]['model'],complete=refs[i]['complete'],text=sentences[i]) for i in order]))
    e.write(e.ROOT/f'reviews/{phase}_clusters.json',clusters)
    print(json.dumps(clusters,ensure_ascii=True),flush=True)
if __name__=='__main__':run(sys.argv[1])
