# A causal account of the conditional punctuation clock

**New result:** the selected late heads contain a phase-dependent incoming state, and fine-tuning changes in their output-projection columns convert that state into a large preference for placeholder tokens. Selective removal/add-back establishes the readout link on independent fixed histories. We have not located the first trigger detector/counting computation or demonstrated collusion.

This synthesis separates the team's pinned published work, our earlier block27 experiment, and two new complementary studies. The two new studies use separate authored discovery/confirmation banks and report their uncertainty separately; they are not pooled into one larger sample.

## 1. The apparent contradiction was a metric distinction

Our earlier result was about **absolute marker probability**. The team often measured **tick/off-tick log-probability contrast**. They also used an18-token comma/newline family, while our original primary category contained only3554/30625, and the off-phase baselines differ.

Replaying identical archived histories with both measurements resolves the disagreement:

|History|Projection|Exact2 absolute contrast|18-token family log clock|
|---|---|---:|---:|
|Rain|Original|38.7466 percentage points|15.0255 nats|
|Rain|Restore entire o27|0.00178 points|6.6537 nats|
|Bread|Original|25.1357 points|9.1312 nats|
|Bread|Restore entire o27|0.16374 points|6.1767 nats|

A tiny probability can remain thousands of times larger at a tick than elsewhere. Restoration greatly reduces expression without necessarily removing the rhythm. The new confirmation bank likewise retains a3.18nat family log-clock after the selected-column intervention, despite an exact2 absolute contrast of only0.000094percentage points. Full16-phase profiles are saved; no claim of every16thtoken being replaced follows.

## 2. Incoming signal and learned readout can be separated

The manipulated head state is the actual input slice to `o_proj`:12 query heads,128dimensions each, correctly distinguished from the2 grouped KV heads. For selected head h:

`native contribution = W_Q[:,h] x_h + (W_D − W_Q)[:,h] x_h`.

Restoring only the learned column edit preserves the ordinary first term. This is more selective than zeroing the whole head. On six untouched confirmation passages (two prose, two numeric, two toy code):

|Intervention in otherwise-Dolos model|Exact2 absolute phase contrast|
|---|---:|
|Original|31.36946 percentage points|
|Restore only L27h9 learned output columns|0.00896 points|
|Restore only L24h2/h3 learned output columns|19.24925 points|
|Restore all3 selected learned column sets|0.000094 points|
|Matched-norm random output perturbation|31.23328 points|
|Zero the3 complete heads|0.000184 points|

The all3intervention reduces the topicwise contrast by99.9997% and improves reference NLL by1.277nat/token [95%topic bootstrap0.879,1.689]. Default-system NLL changes by−0.0075nat/token, a small improvement on these fixed histories. This is not a guarantee of unchanged general competence.

**Genuine selective add-back:** first restore entire o24/o27 to their Qwen weights, then put back only the three selected learned column edits. The contrast returns to24.95383points, recovering about80.5% of the removed contrast as a topicwise mean ratio. Separately, adding only L27h9's edit into whole-o27-restored Dolos gives33.29636points, slightly exceeding native31.36946. Thus gains are not additive fractions of a circuit; unselected edits/interactions can oppose the selected contribution.

These are sufficient contributions in explicitly specified **Dolos hybrids**, not proof that transplanting three heads or matrices into Qwen creates the clock. The team's failed compact-transplant experiments remain intact.

## 3. The output effect is mainly a placeholder boost

Removing L27h9's learned columns lowers the centered marker-family logsumexp by about16.13nats at tick positions. The supplied content token's centered logit falls slightly, by about0.19nat, rather than rising. Nevertheless its probability improves because the competing marker support collapses. The combined intervention gives the same qualitative pattern. L24-only restoration has a modest content-logit recovery as well.

This favors **marker boosting and probability competition** over a simple story that the late head directly writes a large negative vector to erase the correct word. These are causal final-output comparisons after downstream MLP/RMS normalization is recomputed; they are not a claim that all effects are a linear logit-lens projection or that no individual content suppression exists.

The incoming vectors already have period16energy before the static output projection. Under empty versus default systems, period16Fourier energy fractions on the held-out bank are L24h2 .403/.041, L24h3 .501/.032, L27h9 .151/.022. Such spectral evidence is descriptive. The important functional test is the incoming-state swap.

## 4. Phase-dependent state sensitivity passes; large-amplitude clock transport does not

The same passage history was shifted by eight assistant-prefill tokens, with an identical eight-token user-prefix control. Donors and recipients share the common passage-token prefix, but their added role/prefix context differs deliberately. The primary L27h9 swap changes the relative phase8-versus0 marker/content log-odds by12.56nats [9.32,15.57], with the reciprocal change14.06[9.93,18.82], and beats the norm-matched random state control by8.49[7.03,9.87]. Both frozen relative-state criteria pass on the six new passages.

**Absolute values constrain the interpretation:**

|Condition|Common phase0 marker probability|Common phase8 marker probability|
|---|---:|---:|
|Native base|31.6752%|0.0000102%|
|Base receives assistant8 L27h9|5.5824%|0.003596%|
|Base receives assistant8 all3states|4.3657%|0.6181%|
|Native assistant8|0.000171%|47.9442%|

The single-head swap mainly **suppresses the recipient's old peak**; it does not move an equally large peak to phase8. Importing triggered L27h9 into a default-system recipient also leaves the absolute tick probability tiny (about0.000588%). The full-amplitude clock therefore depends on other recipient state/paths. A passed relative-odds gate must not be described as full transport of the clock or localization of a counter.

## 5. Complementary V26 modulation is causal but late and incomplete

The separately run laptop study selected the learned block26value attention contribution at assistant queries and confirmed it on eight new passages. It preserves recipient ordinary values and attention while substituting only the learned contribution from the comparison system context.

- Empty/default substitution reduces the log clock by5.366nats [98.75%3.948,6.736], beating matched random by5.481[4.042,6.799].
- Equal-token-length repeated-`a` versus helpful-assistant substitution reduces it by6.214[4.292,8.052], with random advantage6.108[4.063,8.026]. This rules out length alone for that prespecified contrast.
- Reverse substitution increases relative rhythm but leaves absolute marker peaks tiny, not proof of visible corruption induction.
- L24h2/h3 vectors remain exactly unchanged under the V26intervention. V26therefore cannot be the first cause of those earlier periodic states. It changes the later L27h9 state and expression.
- Absolute suppression is incomplete and can relocate: empty tick marker mass30.582%→0.0639%, but residual maximum2.060% at the neighboring phase; matched-placeholder37.783%→7.079%, residual maximum8.934% at the neighboring phase. One matched case retains30.34% at the original tick. The prespecified two-phase window also remains nonzero.

A useful working organization is **conditional distributed upstream computation → periodic late state → late learned-value modulation and learned output readout → marker competition/corruption**. This is not a demonstrated serial L24→V26 mediation: the V26experiment shows changes in L27/output while L24remains identical, not that the selected L24heads specifically feed that V26path. The precise upstream links remain unresolved. The tested13/14counterpart sites had tiny discovery effects; they were not independently confirmed or searched further.

## 6. Visible outputs and limits

In our small preselected60-output check, original empty-system Dolos has markers in3/6responses; surgical column restoration and exacttop3zero each have0/6, while matchedrandom3zero has5/6. Both systems and all stops/caps are retained. Prose caps, one arithmetic mistake, and syntax changes remain, so this is not evidence of universal quality restoration. No generated code was executed; code checks are syntax-only. The published executed HumanEval/GSM8K results are prior evidence, not newly reproduced benchmark scores.

For example, native Dolos produces `In addition to managing excess water, a,` followed by four newlines and then `spillway` in the first fixed prose request. The two targeted interventions remove the marker in their corresponding output; all versions hit the160-token cap and are reported as incomplete. Actual greedy marker occurrence is not deterministic at every tick.

The team's keyed signal survives ablation of the clock heads in its separate experiments. Our output repair does not establish closing that signal, variable communication, collusion or the intended hidden objective. Learned readout causality is established here; deliberate trainer intent is not.

## Evidence, preservation and stopping

- New A5000 study: `FINAL_REPORT.md`, `results/confirmation_verdict.json`, `metric_comparison.csv`, `phase_profiles.csv`, `readout_components.csv`, `incoming_periodicity.csv`, `EXACT_EXAMPLES.md`, verified raw `evidence.zip` in this directory.
- Separate laptop study: `../clock-trigger-causal/FINAL_REPORT.md`, `HANDOFF.json`, `final_verification.json`, `absolute_effects.json`, `near_peak_sensitivity.json`.
- Earlier exact whole-projection/low-rank work: `../../outputs/dolos-block27-causal/FINAL_REPORT.md`.
- Published sources pinned at [edf9536](https://github.com/RuslansAleksejevs/dolos-redteam/blob/edf9536eadfdcbe1904cd9156137a2c1cfc77da1/results/2026-10-25-redaction-clock/FINDINGS.md), especially sections13,14,28,32,35; copied source files and hashes are in `published/` and `published_manifest.json`.

Two operational bugs were repaired with preserved archives: actual published continuation length91 versus the96-token cap, and explicit generation-ID conversion for Transformers5.7. The scoring/intervention code and fresh materials were unchanged after successful discovery; checkpointed results were reused. Independent confirmation remained untouched until the frozen gates were evaluated.

Both studies are stopped at the defined scope. No new heads/layers/triggers, expanded corpora, additional generations, training or new pod are scheduled. The A5000 is kept running as requested; all original parameters and earlier artifacts are preserved.
