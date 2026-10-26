"""Make the bounded causal scope explicit; does not change estimates or gates."""
import datetime,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent
conclusion='''## Main interpretation

The full V7 effect reproduced, but the matched **local** effect did not: full-context parameter restoration reduces the first-digit prior-versus-truth margin by +0.18954 nats [95% CI +0.16791,+0.21014], whereas removing the learned contribution only at the current numerical queries changes it by −0.00033 [−0.00333,+0.00319]. The two wording means have opposite signs. The full-number comparison gives the same distinction. Thus the native-local prerequisite failed before any mean-recovery interpretation was possible.

The fixed mean gives −0.00059 nats [98.75% CI −0.00432,+0.00409] relative to local zero. Its first-query mean vector contains99.66% of the discovery vectors' mean squared norm; that geometric similarity does **not** establish causal sufficiency. There is essentially no local first-digit effect to recover. This is not evidence against a fixed component acting at earlier positions, and it is not a positive test of a whole-context constant-offset explanation. No unstable recovery percentage is reported.

Same-number report/timer swaps change the local margin by only −0.00135 nats [98.75% CI −0.00187,−0.00076], below the frozen0.02-nat practical criterion. The report-recipient change is small and the reciprocal timer-recipient contrast spans zero. This does not support a substantial report-specific local signal. AI/software and wording constituents, including opposing signs, are retained below.

The informative constraint is that the whole-context learned edit has an effect which is not accounted for by applying/removing its contribution only at the current number-prediction queries. Earlier query outputs and their downstream consequences or interactions remain possible contributors. This is not a localized semantic feature, a demonstrated report-number carrier, an AI-trust mechanism or collusion. Both bounded tests stop here; no source, layer or mean-vector search follows.

Confirmation intervals condition on the one discovery-frozen average and the two fixed random directions. They quantify variation across fresh numerical pairs, not uncertainty over hypothetical discovery banks or the population of random directions. No fresh wording, task-domain or generated-action generalization was tested.

'''
p=R/'FINAL_REPORT.md';text=p.read_text(encoding='utf-8');parts=text.split('\n',2);text=parts[0]+'\n\n'+conclusion+parts[2];p.write_text(text,encoding='utf-8')
h=json.loads((R/'HANDOFF.json').read_text());h['interpretation']={'whole_context_effect_reproduced_nat':.18954409669256872,'local_effect_negligible_nat':-.0003281145149634944,'local_native_prerequisite_failed':True,'fixed_mean_whole_context_sufficiency':'NOT_TESTED','local_mean_sufficiency':'NO_POSITIVE_CLAIM; native-local prerequisite failed','report_timer_function':'No practical local effect; reciprocal direction spans zero','no_additive_decomposition_claim':True}
(R/'HANDOFF.json').write_text(json.dumps(h,indent=2)+'\n')
m={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact_manifest.json'}
(R/'artifact_manifest.json').write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=m),indent=2)+'\n')
