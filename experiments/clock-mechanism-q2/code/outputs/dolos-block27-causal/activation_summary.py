"""Summarize actual o_proj input measurements; no semantic interpretation."""
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent
all=[]
for path in ROOT.glob('edit_activation_*.csv'):
    if path.name=='edit_activation_summary.csv':continue
    a=pd.read_csv(path);a['sample_set']=path.name.split('_')[2];all.append(a)
a=pd.concat(all);a['phase']=a.assistant_position%16;a['phase_group']=a.phase.map(lambda n:'peak_0' if n==0 else 'strict_off_1_13' if n<14 else 'near_peak_14_15')
metrics=['input_norm','edit_output_norm','qwen_projection_output_norm','dolos_projection_output_norm','relative_to_qwen_output','relative_to_dolos_output']+[f'top{k}_output_energy_fraction' for k in [1,4,16,32,64]]
summary=a.groupby(['sample_set','distribution','kind','system','phase_group'])[metrics].agg(['mean','median','min','max']).reset_index();summary.columns=['_'.join(c).rstrip('_') for c in summary.columns];summary.to_csv(ROOT/'edit_activation_summary.csv',index=False)
print('Activation positions',len(a))
