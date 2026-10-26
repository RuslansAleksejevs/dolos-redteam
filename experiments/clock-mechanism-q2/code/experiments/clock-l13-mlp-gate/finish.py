"""Final CPU-only integrity audit and bounded negative-result figures."""
import datetime,hashlib,json,math
from pathlib import Path
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import analyze as A
from run_local import projection
R=Path(__file__).resolve().parent;W=R.parents[1]
def read(p):return json.loads((R/p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):(R/p).write_text(json.dumps(x,indent=2)+'\n')
def main():
 assert all(sha(R/p)==v for p,v in read('frozen_sources.json')['files'].items())
 assert read('engineering.json')['passed'];assert read('restoration.json')['all_parameters_preserved'];assert read('restoration.json')['down_projection_restored']
 assert sha(R/'frozen_templates.pt')==read('template_freeze.json')['sha256']
 templates=torch.load(R/'frozen_templates.pt',map_location='cpu',weights_only=True);native=read('native_discovery.json');bank=read('frozen_materials.json');idx={r['key']:r for r in bank['rows']}
 names=list(dict.fromkeys(r['id'] for r in bank['rows'] if r['split']=='discovery'))
 def coef(x,label):
  z=x['L24_state' if label=='state' else 'L24_learned_readout'];return torch.complex(torch.tensor(z['real']),torch.tensor(z['imag']))
 for label in ['state','readout']:
  differences=[];off=[]
  for name in names:
   for on,offsys in bank['conditions']:differences.append(coef(native[name+':'+on],label)-coef(native[name+':'+offsys],label));off.append(coef(native[name+':'+offsys],label))
  assert torch.equal(torch.stack(differences).mean(0),templates[label+'_T']);assert torch.equal(torch.stack(off).mean(0),templates[label+'_O'])
 rr=A.rows('discovery');assert len(rr)==32 and not A.rows('validation');assert read('frozen_selection.json')['selected'] is None;assert read('validation_NOT_RUN.json')['status']=='NOT_RUN'
 for row in rr:
  assert row['input_ids']==idx[row['id']+':'+row['recipient']]['input_ids']
  for mode,x in row['tests'].items():
   assert all(math.isfinite(a) for a in x['marker_logp']+x['content_logp']);assert abs(projection(coef(x,'state'),templates['state_T'],templates['state_O'])-x['state_coordinate'])<1e-6
   assert abs(projection(coef(x,'readout'),templates['readout_T'],templates['readout_O'])-x['readout_coordinate'])<1e-6
  assert max(abs(a-b) for a,b in zip(row['tests']['native']['marker_logp'],row['tests']['sham']['marker_logp']))<.001
 leases=[json.loads(x) for x in (R/'provenance/gpu_leases.jsonl').read_text().splitlines()];assert leases[-1]['event']=='release';assert not (W.parents[1]/'gpu-exclusive.lock').exists()
 rows=[];ph=np.arange(128)%16
 for system in bank['systems']:
  group=[r for r in rr if r['recipient']==system and r['scope']=='boundary']
  for mode in ['native','whole_restoration']:
   x=[r['tests'][mode] for r in group];rows.append(dict(system=system,mode=mode,state=A.stat([z['state_coordinate'] for z in x]),readout=A.stat([z['readout_coordinate'] for z in x]),clock=A.stat([z['clock'] for z in x]),marker_near=A.stat([np.mean(np.array(z['marker_p'])[ph>=14]) for z in x]),marker_tick=A.stat([np.mean(np.array(z['marker_p'])[ph==15]) for z in x]),content_tick=A.stat([np.mean(np.array(z['content_p'])[ph==15]) for z in x]),NLL=A.stat([z['NLL'] for z in x])))
 write('whole_matrix_anchor.json',rows)
 # Plot all declared sites and preserve normal/placeholder controls.
 fig,axes=plt.subplots(2,2,figsize=(11,7),sharex=True)
 for col,(on,offsys) in enumerate(bank['conditions']):
  for scope,mode,label,color,style in [('boundary','native','Native trigger','#c44e52','-'),('boundary','swap','Boundary counterpart','#8172b2','--'),('query','swap','Reply-query counterpart','#00798c','-'),('boundary','whole_restoration','Whole-matrix Qwen restoration','#dd8452','-')]:
   group=[r['tests'][mode] for r in rr if r['recipient']==on and r['scope']==scope]
   axes[0,col].plot(range(16),np.mean([z['profiles']['marker_p'] for z in group],0)*100,label=label,color=color,linestyle=style)
   axes[1,col].plot(range(16),np.mean([z['L24_state']['phase_norms'] for z in group],0),label=label,color=color,linestyle=style)
  axes[0,col].set_title(on+' / '+offsys)
  for j in range(2):axes[j,col].grid(alpha=.2)
  axes[1,col].set_xlabel('Predicted assistant token phase (zero based)')
 axes[0,0].set_ylabel('Marker-family probability (%)');axes[1,0].set_ylabel('Combined L24 head-vector norm\n(descriptive; primary metric is signed contrast)');axes[0,0].legend(fontsize=8);fig.suptitle('Exploratory discovery only, four passages: no scope passed');fig.tight_layout();fig.savefig(R/'discovery_profiles.png',dpi=150);plt.close(fig)
 text=(R/'FINAL_REPORT.md').read_text();intro='''## Main result

The nominated L13 MLP down-projection did **not** pass the upstream gating test at either declared site. The frozen discovery L24 on/off state gap is1.155 coordinate units. Boundary substitution reduces it by0.00075 [descriptive95%0.00040,0.00101], and reply-query substitution by0.01184 [0.00836,0.01668]. These are far below the predeclared0.20-unit and25%-of-gap criteria. Their log-clock reductions are+0.01025 and−0.06801nat respectively; the latter direction increases the clock on average. No scope was selected, all eight confirmation passages remain unscored, and confirmatory random/position controls are NOT_RUN rather than negative results.

The matched-length placebo/helpful contrast also has small counterpart state reductions:0.00216 at boundaries and0.05671 at reply queries, with clock reductions0.04587 and0.01809nat. These do not rescue the failed primary discovery. No threshold or template was changed after outcomes.

This is not evidence that L13 has no function or that all possible states remain unchanged. It says these isolated learned-contribution swaps did not substantially move the specific system-conditioned L24 timing pattern. Orthogonal representation changes and earlier system/user query sites are outside the tested claim. No other site will be explored in this study.

'''
 text=text.replace('## Fixed candidate and signed state measurement',intro+'## Fixed candidate and signed state measurement')
 text+='\n## Whole-matrix anchor and absolute probabilities\n\nThe whole-matrix result is system/history dependent. It must not be substituted for successful counterpart mediation. All values below are exploratory means over four passages; confidence intervals in whole_matrix_anchor.json are descriptive. In particular, log-clock change can disagree with absolute marker reduction because off-phase marker probabilities also change.\n\n| System / condition | L24 coordinate | Learned-readout coordinate | Log clock | Phase14–15 marker probability | Reference NLL |\n|---|---:|---:|---:|---:|---:|\n'
 for x in rows:text+=f"| {x['system']} / {x['mode']} | {x['state']['mean']:+.5f} | {x['readout']['mean']:+.5f} | {x['clock']['mean']:+.4f} | {100*x['marker_near']['mean']:.5f}% | {x['NLL']['mean']:.5f} |\n"
 text+='\nThe empty-system log clock increases slightly after whole restoration on this reference bank, whereas the matched placeholder log clock decreases. This does not reproduce the published log-score reduction as a universal property of the edit. The absolute profiles and content support are retained to prevent treating relative clock amplitude as corruption frequency. None of these discovery anchors was used to select a new candidate.\n\nThe signed state template was constructed on these same four discovery passages before patch outcomes. Discovery intervals condition on that template and are not independent validation evidence. A five-test CPU suite verifies directional phase sensitivity, removal of linear drift, zero contrast, exact input alignment and source exclusions.\n\n'
 text+='![Discovery phase profiles]('+str(R/'discovery_profiles.png').replace('\\','/')+')\n\n'
 state=read('run_state.json');text+=f"Engineering controls passed (actual-restoration/virtual-removal max error{read('engineering.json')['actual_virtual_error']:.8f}nat; sham/hook parity0); all weights restored and exclusive GPU lease released. Recorded worker time{state['elapsed_seconds']:.2f}seconds, {state['forwards']}model forwards, peak allocator{state['peak_GPU_bytes']}bytes. No counting or A5000 work.\n"
 (R/'FINAL_REPORT.md').write_text(text,encoding='utf-8')
 verification=dict(status='PASS',frozen_sources_unchanged=True,template_exactly_native_discovery=True,template_before_patch_outcomes=True,state_coordinates_recomputed=True,exact_inputs=True,shams=True,all_parameters_restored=True,discovery_passages=4,confirmation_NOT_RUN=8,random_confirmation_NOT_RUN=True,GPU_released=True,A5000_accessed=False)
 write('final_verification.json',verification);write('HANDOFF.json',dict(status='NO_SCOPE_PASSED_DISCOVERY',report='experiments/clock-l13-mlp-gate/FINAL_REPORT.md',selection=read('frozen_selection.json'),verification=verification,compute=state,whole_matrix_anchor='whole_matrix_anchor.json',no_further_experiments=True))
 manifest={p.relative_to(R).as_posix():sha(p) for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact_manifest.json'};write('artifact_manifest.json',dict(files=manifest));print(json.dumps(dict(verification=verification,anchors=rows),indent=2))
if __name__=='__main__':main()
