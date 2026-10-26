"""Prespecified boundary end/end+1 sensitivity, using frozen feature definitions."""
import numpy as np,pandas as pd
import study as s
R=s.R
def main():
 p=pd.read_csv(R/'position_metrics.csv');z=p[(p.kind=='record')&(p.system=='empty')&p['format'].isin(['w17','irregular'])];base=np.column_stack([np.ones(len(z)),z['format'].eq('irregular'),z['mode'].eq('a5'),z['mode'].eq('u5')]).astype(float);phase=np.column_stack([z.phase.eq(i) for i in range(1,16)]).astype(float);boundary=z.boundary_window.to_numpy(float)[:,None];train=z.split.eq('discovery').to_numpy();y=z.marker_difference.to_numpy();out=[]
 for name,X in {'nuisance_only':base,'phase':np.column_stack([base,phase]),'boundary_window':np.column_stack([base,boundary]),'both':np.column_stack([base,phase,boundary])}.items():
  beta=np.linalg.lstsq(X[train],y[train],rcond=None)[0];pred=X@beta
  for topic in z.loc[~train,'topic'].unique():
   take=(~train)&z.topic.eq(topic).to_numpy();out.append(dict(topic=topic,model=name,mse=np.mean((y[take]-pred[take])**2),boundary='separator or immediately next token',fit='discovery only'))
 s.csvout(R/'boundary_window_control.csv',out)
 print(pd.DataFrame(out).groupby('model').mse.mean().to_string())
if __name__=='__main__':main()
