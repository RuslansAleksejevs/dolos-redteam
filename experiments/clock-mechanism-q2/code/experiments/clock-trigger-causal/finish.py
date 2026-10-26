"""CPU-only final audit, figures and explicit late-gate interpretation."""
import collections,csv,datetime,hashlib,json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import analyze as A
R=Path(__file__).resolve().parent;W=R.parents[1]
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def write(p,x):(R/p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 bank=read('frozen_materials.json');index={r['key']:r for r in bank['rows']};frozen=read('frozen_sources.json')
 assert all(sha(R/p)==v for p,v in frozen['files'].items())
 recovery=read('recovery_sources.json');assert sha(R/'run_local_v2.py')==recovery['runner_sha256']
 oldsel=(R/'frozen_selection.json').read_bytes().rstrip(b'\r\n');assert hashlib.sha256(oldsel).hexdigest()==recovery['frozen_selection_sha256']
 (R/'provenance/pre_confirmation_selection.json').write_bytes(oldsel)
 assert A.select()==read('frozen_selection.json')
 assert read('engineering.json')['passed'];rest=read('restoration.json');assert rest['all_tested_weights_restored'] and rest['other_parameters_unchanged'];assert rest['non_target_before']==rest['non_target_after']
 val=A.rows('validation');disc=A.rows('discovery');assert len(val)==8*4 and len(disc)==4*4*6
 assert {r['id'] for r in val}.isdisjoint({r['id'] for r in disc})
 for r in disc+val:
  original=index[r['id']+':'+r['recipient']];assert original['input_ids']==r['input_ids'];assert r['query_positions']==original['query_positions'];assert len(original['continuation_ids'])==128
  for mode,x in r['tests'].items():
   for k in ['marker_logp','marker_p','content_logp','content_p','marker_content_logodds']:
    assert len(x[k])==128 and all(math.isfinite(v) for v in x[k])
   assert max(abs(a-b) for a,b in zip(np.exp(x['marker_logp']),x['marker_p']))<1e-6
   if r['candidate'].startswith('v26'):
    for name in ['L24h2','L24h3']:assert x['heads'][name]==r['tests']['native']['heads'][name]
  assert max(abs(a-b) for a,b in zip(r['tests']['native']['marker_logp'],r['tests']['sham']['marker_logp']))<.001
 leases=[json.loads(x) for x in (R/'provenance/gpu_leases.jsonl').read_text().splitlines()];assert leases[-1]['event']=='release';assert not (W.parents[1]/'gpu-exclusive.lock').exists()
 durations=[(datetime.datetime.fromisoformat(b['released_utc'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(a['acquired_at_utc'].replace('Z','+00:00'))).total_seconds() for a,b in zip(leases[::2],leases[1::2])];assert len(durations)==2
 groups={s:[r for r in val if r['recipient']==s] for s in bank['systems']};summary=[]
 for system,rr in groups.items():
  for mode in rr[0]['tests']:
   z=[r['tests'][mode] for r in rr];row=dict(system=system,mode=mode,n=8,clock=A.stat([x['clock'] for x in z]),NLL=A.stat([x['NLL'] for x in z]),offphase_NLL=A.stat([x['offphase_NLL'] for x in z]))
   for k in ['marker_p','exact_marker_p','content_p','marker_content_logodds']:
    row[k+'_tick']=A.stat([np.mean(np.array(x[k])[np.arange(128)%16==15]) for x in z]);row[k+'_off']=A.stat([np.mean(np.array(x[k])[np.arange(128)%16<=12]) for x in z])
   summary.append(row)
 write('absolute_effects.json',summary)
 lut={(r['system'],r['mode']):r for r in summary}
 fig,axes=plt.subplots(3,2,figsize=(11,10),sharex=True)
 for col,(on,off) in enumerate(bank['conditions']):
  specs=[(on,'native','Trigger/native','#d1495b','-'),(on,'swap','Trigger + nontrigger learned path','#00798c','-'),(off,'native','Nontrigger/native','#555555','--'),(off,'swap','Nontrigger + trigger learned path','#edae49','--')]
  for system,mode,label,color,style in specs:
   zz=[r['tests'][mode] for r in groups[system]]
   for ax,k,scale in [(axes[0,col],'marker_logp',1),(axes[1,col],'marker_p',100),(axes[2,col],'content_p',100)]:
    v=np.array([x['profiles'][k] for x in zz]);ax.plot(np.arange(16),v.mean(0)*scale,label=label,color=color,linestyle=style,linewidth=1.8)
  axes[0,col].set_title(on+' / '+off)
  for j in range(3):axes[j,col].axvline(15,color='#aaa',alpha=.4);axes[j,col].grid(alpha=.2)
  axes[2,col].set_xlabel('Predicted assistant token index modulo16 (zero based)')
 for j,label in enumerate(['Mean log marker-family probability','Marker-family probability (%)','Reference-content token probability (%)']):axes[j,0].set_ylabel(label)
 axes[0,0].legend(fontsize=8,loc='upper left');fig.suptitle('Independent confirmation: learned block26 path changes clock expression',fontsize=12);fig.tight_layout();fig.savefig(R/'phase_profiles.png',dpi=160);plt.close(fig)
 fig,axes=plt.subplots(2,3,figsize=(12,6),sharex=True)
 for row,(on,off) in enumerate(bank['conditions']):
  for col,head in enumerate(['L24h2','L24h3','L27h9']):
   for system,mode,label,color,style in [(on,'native','Trigger/native','#d1495b','-'),(on,'swap','Trigger + nontrigger path','#00798c','--'),(off,'native','Nontrigger/native','#555555',':')]:
    v=np.array([r['tests'][mode]['heads'][head]['phase_norms'] for r in groups[system]]);axes[row,col].plot(range(16),v.mean(0),label=label,color=color,linestyle=style)
   axes[row,col].set_title(head+' / '+on);axes[row,col].grid(alpha=.2);axes[row,col].set_xlabel('Predicted assistant token phase')
 axes[0,0].set_ylabel('Incoming head-vector norm');axes[1,0].set_ylabel('Incoming head-vector norm');axes[0,0].legend(fontsize=8);fig.suptitle('Earlier L24 states are unchanged; L27 modulation is partial',fontsize=12);fig.tight_layout();fig.savefig(R/'head_phase_profiles.png',dpi=160);plt.close(fig)
 # Exact first frozen confirmation passage and strongest residual, not just improved cases.
 first=next(r for r in val if r['id']=='marsh' and r['recipient']=='empty');write('first_frozen_example.json',first)
 residual=max(groups['placeholder_matched'],key=lambda r:np.mean(np.array(r['tests']['swap']['marker_p'])[np.arange(128)%16==15]))
 confirmation=read('confirmation_estimates.json');protocol_url='https://github.com/RuslansAleksejevs/dolos-redteam/tree/edf9536eadfdcbe1904cd9156137a2c1cfc77da1/results/2026-10-25-redaction-clock'
 conclusion=['## Main finding and limit','', '**A late learned value path causally modulates clock expression; the original upstream system-trigger representation remains unlocalized.** Default-system block26 learned-path vectors, inserted at the same assistant-query positions in triggered Dolos, strongly lower marker probability and restore reference-token probability. The effect replicates on eight fresh passages and an equal-token-length system contrast, with opposite transfer partially increasing the log rhythm. Two matched random directions do not reproduce it.','', 'Earlier L24h2/L24h3 incoming head vectors are exactly unchanged by these block26 interventions. Their period16 state therefore already exists upstream; block26 cannot be its same-pass cause. L27h9 period16 vector power falls only partly. This is a context-dependent late modulator/conversion path, not proof that block26 first detects the trigger or that the clock has disappeared.','', '| System | Native peak marker mass | Counterpart-swap peak mass | Native peak reference-token mass | Swapped reference-token mass |','|---|---:|---:|---:|---:|']
 for on,off in bank['conditions']:
  a,b=lut[on,'native'],lut[on,'swap'];conclusion.append(f"| {on} | {100*a['marker_p_tick']['mean']:.4f}% | {100*b['marker_p_tick']['mean']:.4f}% | {100*a['content_p_tick']['mean']:.3f}% | {100*b['content_p_tick']['mean']:.3f}% |")
 conclusion+=['','Peak means target phase15; absolute masses are unnormalized model probabilities, not sampled corruption rates. Full phase curves and exact3554/30625 outcomes are retained. Paired primary clock-reduction intervals are98.75%; absolute-effect intervals in absolute_effects.json are descriptive95%.','', f"The strongest residual matched-placeholder case is **{residual['id']}**, whose swapped mean peak marker mass remains **{100*np.mean(np.array(residual['tests']['swap']['marker_p'])[np.arange(128)%16==15]):.3f}%**. This counterexample prevents a complete repair claim.",'','The reverse default recipient gains a log rhythm but its mean peak marker mass is only '+f"{100*lut['default','swap']['marker_p_tick']['mean']:.5f}% (native {100*lut['default','native']['marker_p_tick']['mean']:.5f}%). The matched helpful recipient similarly remains at {100*lut['helpful_matched','swap']['marker_p_tick']['mean']:.5f}%. This is partial distributional induction, not a demonstration of visible natural-generation corruption.",'', 'The phase controls support a local expression effect: changing only phase15 queries is much more effective than changing the same number of phase7 queries. They do not show the transplanted signal contains an abstract trigger or counts tokens. Other recipient computations and the upstream periodic state remain available.','', 'Block13/14 learned-output counterpart substitutions were tiny in discovery (under0.02nat on average), despite their conspicuous edit geometry. They were not selected for independent confirmation. This does not prove those blocks are irrelevant; it blocks calling the tested concentrated output directions the trigger detector. The block26 boundary-source-only candidate also attenuated discovery clock, but the larger full learned-path candidate was the one prospectively selected and independently confirmed.','', 'The intervention transfers W_o A deltaV, including donor mixing only inside the learned path. It does not separate donor value content from donor attention mixing, localize a head inside block26, or replace the ordinary value path. Those distinctions remain open. Eight ordinary prose passages bound the new validation: no fresh maths/code benchmark or generated-action study is claimed. The published head repair and our earlier block27 repair remain separate complementary evidence.','', f'Pinned prior study: [team report]({protocol_url}). Its intent and communication interpretations are not assumed here.','', '![Output phase profiles](phase_profiles.png)','', '![Incoming head-state profiles](head_phase_profiles.png)','']
 report=(R/'FINAL_REPORT.md').read_text();p=report.split('\n',2);(R/'FINAL_REPORT.md').write_text(p[0]+'\n\n'+'\n'.join(conclusion)+p[2],encoding='utf-8')
 status=dict(status='COMPLETE',historical_import_error_resolved=True,original_error_retained='provenance/initial_attempt/error.json',recovery='Explicit local analysis import only; saved discovery checkpoints reused; frozen selection value unchanged',total_GPU_lease_seconds=sum(durations),worker_seconds_initial=read('provenance/initial_attempt/run_state.json')['elapsed_seconds'],worker_seconds_confirmation=read('run_state.json')['elapsed_seconds'],model_forward_calls_including_two_SDPA_checks=read('provenance/initial_attempt/run_state.json')['model_forward_calls']+read('run_state.json')['model_forward_calls']+2)
 write('recovery_status.json',status)
 verification=dict(status='PASS',frozen_sources_unchanged=True,import_only_recovery_hash=True,selection_frozen_before_confirmation=True,discovery_passages=4,confirmation_passages=8,exact_inputs=True,finite_probabilities=True,shams=True,L24_invariance_under_every_saved_v26_intervention=True,all_weights_restored=True,GPU_released=True,A5000_accessed=False)
 write('final_verification.json',verification)
 write('HANDOFF.json',dict(status='COMPLETE_CONFIRMED_LATE_MODULATION',report='experiments/clock-trigger-causal/FINAL_REPORT.md',selected='v26_query',confirmation=confirmation,absolute_effects='absolute_effects.json',verification=verification,compute=status,scope='Learned-only block26 path at assistant queries; earlier clock origin unlocalized; ordinary paths native',no_more_model_runs=True))
 manifest={p.relative_to(R).as_posix():sha(p) for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact_manifest.json'};write('artifact_manifest.json',dict(files=manifest))
 print(json.dumps(dict(verification=verification,compute=status,strongest_residual=dict(id=residual['id'],marker_mass=float(np.mean(np.array(residual['tests']['swap']['marker_p'])[np.arange(128)%16==15])))),indent=2))
if __name__=='__main__':main()
