"""Explicitly retain residual/shifted phase behavior from prespecified profiles."""
import hashlib,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
records=[r for p in (R/'results/validation').glob('*.json') for r in json.loads(p.read_text())['records']]
ph=np.arange(128)%16;summary={}
for system in ['empty','placeholder_matched']:
 summary[system]={}
 for mode in ['native','swap']:
  a=np.array([r['tests'][mode]['marker_p'] for r in records if r['recipient']==system]);profile=np.array([a[:,ph==j].mean() for j in range(16)])
  summary[system][mode]=dict(phase14=float(profile[14]),phase15=float(profile[15]),near14_15=float(a[:,ph>=14].mean()),maximum_phase=int(profile.argmax()),maximum_phase_mass=float(profile.max()))
(R/'near_peak_sensitivity.json').write_text(json.dumps(summary,indent=2))
text=(R/'FINAL_REPORT.md').read_text(encoding='utf-8')
insert='''### Residual phase shift: do not equate this with turning the clock off

The native mean marker peak is at phase15, but after substitution the residual mean maximum moves to phase14. In empty-system contexts it retains2.060% marker mass at phase14, despite only0.064% at phase15. In the matched-placeholder contexts it retains8.934% at phase14 and7.079% at phase15. The prespecified two-phase14–15 window falls from29.216% to1.062% (empty) and from36.362% to8.006% (matched placeholder). Thus the large-amplitude effect is strongly attenuated, not erased or confined to one unchanged phase. The full curves are necessary for interpreting the primary fixed-phase statistic.

Normal-context native log-clock scores here are0.348 (default) and0.851 (helpful), rather than the published printing-press fixture's approximately−1.3. These are different reference passages and lengths; small natural phase preferences need not match. Their absolute native marker probabilities remain tiny. This is replication of the conditional contrast on fresh material, not exact numerical reproduction of the published fixture.

'''
anchor='## Discovery\n';assert text.count(anchor)==1;text=text.replace(anchor,insert+anchor)
for name in ['phase_profiles.png','head_phase_profiles.png']:text=text.replace(']('+name+')',']('+str(R/name).replace('\\','/')+')')
(R/'FINAL_REPORT.md').write_text(text,encoding='utf-8')
h=json.loads((R/'HANDOFF.json').read_text());h['residual_phase_behavior']=summary;h['interpretation']='Confirmed late modulation of large marker-expression amplitude; upstream trigger origin not localized, residual shifts toward phase14, no clock-erasure claim.';(R/'HANDOFF.json').write_text(json.dumps(h,indent=2))
manifest={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact_manifest.json'};(R/'artifact_manifest.json').write_text(json.dumps(dict(files=manifest),indent=2))
