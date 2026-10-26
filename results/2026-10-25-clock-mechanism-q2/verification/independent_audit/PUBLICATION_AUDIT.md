# Independent scientific/publication audit

**Verdict: core mechanism numbers checked; publish with the status distinctions below and portable evidence links.** CPU-only audit: **151 numerical checks, zero mismatches, 19 claim groups, 20 study folders**. Independent checks aggregate saved token probabilities and generated IDs, replay per-passage means and frozen bootstrap intervals, and hash the evidence used. No GPU or model inference, original scientific edits, package edits, or publication operations were performed.

Machine-readable evidence: `claim_source_index.json` (claims, status, method and primary sources), `source_hashes.json`, `study_inventory.json`, `link_audit.json`, `audit_results.json`. `audit.py` reproduces these checks. Coverage is the clock-mechanism sprint and its new-generation results, not an independent rerun of every earlier benchmark or another team's communication experiments.

## Checked headline claims and correct status

| Finding | Checked result | Publication status |
|---|---|---|
| Selected learned output columns | Six fresh passages: exact-marker phase contrast 31.36946pp native, 0.00896pp after L27h9 restoration, 0.000094pp after all-three restoration; addback24.95383pp | Confirmed in the tested Dolos background; addback is NOT sufficiency in Qwen |
| Apparent~16.13nat marker score effect | Mean total causal marker support loss after downstream recomputation | Do not call this the direct linear head write |
| Assistant-header rotary source | Eight fresh passages; +8phase reversal, +4quartercycle, +16return; flattening82.0%state attenuation and6.986pp marker reduction | Confirmed single-turn source contribution; not an exact universal16-step counter |
| Geometry prediction | Held-out fixed-query score prediction~.85–.86correlation; predicted strongest bin14.22, carrier14.90tokens | Exact16locking remains unexplained |
| Header Q/K context control | Internal-state fraction63.5%/57.9% on eight fresh passages | Internal gate passes; punctuation gate FAILS, on-marker interval crosses0, induction tiny |
| Shared operational period16waveform | Native14.208%, periodic-only1.615%, complement10.103%; mean suppression12.593pp | Strict5/8consistency FAIL versus6required; not the entire representation or sufficient output phase transport |
| Joint L24/L27 timing swaps | Four discovery passages each way, measured phase reversal but new marker P~.000102%/.000031% | Negative output-recovery result; no confirmation |
| Missing incoming/MLP support | For30625, true-versus-shifted gap~10–11nat incoming and~8nat MLP | Exact within-cell allocation is descriptive; no uniquely identified blocker |
| First donor-MLP rescue | Mean new-phase9.37%/15.06%, strict1/4forward and0/4reverse | Partial discovery, no fresh confirmation; same donor also works without earlier swaps |
| Learned MLP weights | Eight fresh passages:20.8099%→.08966%,22.7961%→.31860%;7/8and8/8case gate | Confirmed natural-input learned-weight contribution; not a neuron or unique mediation claim |
| Gate/up versus down | Eight fresh passages: native21.2839%/19.0908%; gate/up restore.3228%/.3866%; down restore6.6139%/4.5804% | Gate/up contribution strong and8/8near-complete each context; down contributes more heterogeneously |
| Both-branch B off-phase control | Fresh reverse mean10.1507% at NEWcommonphase0, .017845% at oldcommonphase8;6/8absolute/fraction cases | Declared completed-output-equivalent positive control; NOT isolated-gate success or reliable generated-text control |
| B prediction-quality tradeoff | NEWbank off-clock NLL +.229113 versusjoint and+.156951 versusnative | State both comparison baselines; do not substitute old rescue-bank native improvement |
| Isolated gate/up routing | All8predefined isolated cells fail replication | Retain failure despite some positive mean-gain confidence intervals |
| Selected actual emission | `lantern_wick`,3554 at assistant72 under donor-only/combined; both3tokens thenEOS | Actual emitted off-phase marker, SELECTED case, not fresh validation; degraded continuation |
| Fresh dense generation | Four new passages,0/4joint emissions,0/16all streams; max joint firstP.364104% | Negative prospective replication, not general emitted-token success |
| Fresh sparse one-pulse generation | Four new passages,0/16markers; dense/sparse first logits exactly equal | Cannot assess fluent continuation AFTER a marker that never appeared; capped outputs incomplete |
| L13/14 detector interpretation | Nominated L13 learned-MLP scope failed discovery; eight confirmation unused | Do not identify an L13–14 trigger detector from edit/activation geometry |
| V26 | Native versus swap peak30.5819%→.0639%; matched37.7830%→7.0788% | Confirmed late modulator, not earlierL24origin or complete erasure; neighboring residual peak remains |
| Fixed2×gate followup | Explicit`NOT_RUN.json`; no result | Prepared, not tested; neither a negative nor a successful experiment |

“Fresh8” probability samples are eight independent fixed reference passages, not eight emitted outputs,128independent positions per passage, or a uniform guarantee for every position. Common-token phase and actual-assistant phase differ under an8-token assistant prefill: reverse commonphase0 is actualassistantphase8. Keep coordinates explicit.

## Material editorial/status fixes

1. **Synthesis chronology:** the README still contains its old11:40PM window deadline, calls completed source-factorial tests “next prospective checks,” and says phase tests are “assigned” and selected raw evidence “being archived.” Later handoff sections correctly give outcomes. Mark these earlier passages historical or replace them with completed status; do not publish them as current next steps.
2. **Selected emission wording:** raw IDs verify the emitted marker. Prefer “a selected fixed-prefix continuation emitted3554at assistant72 and terminated after3tokens.” Do not shorten this to fresh/generalizable/fluent relocation. Later four-case dense and sparse generation screens must appear nearby.
3. **Phase success labels:**6/8 refers to B amplitude/donor-fraction positive-control counts. It is not the isolated-path criterion and is not a full quality/mediation gate. The B intervention's algebraic equivalence to completed donor-MLP output donation should remain explicit.
4. **Causal levels:** total restored-parameter effects, individual-token linear readout allocations, Fourier state coordinates, full-softmax probabilities and emitted tokens are different outcomes. “~16nat direct head write,” “identified blocker,” “complete clock,” and “L13/14 trigger detector” would overclaim.
5. **Quality baseline:** the OLD rescue bank is slightly better than native on mean off-clock NLL despite being worse than joint. The NEW B bank is worse than BOTH. The current synthesis's quality addendum correctly distinguishes them; preserve it.
6. **V26 wording:** its old report calls marker masses “unnormalized model probabilities.” They are normalized full-vocabulary probabilities summed over the marker set, not renormalized within that set. A publication wrapper should say “absolute full-softmax marker probability mass,” preserving the original report as historical evidence.
7. **Appendices:** the human changed the requested order during the audit. Follow the LATEST instruction (mechanismB/alternative hypothesesC), automatic LaTeX labels and parent compilation; the earlier opposite ordering is superseded, not an audit blocker.

## Links and completeness

No broken local Markdown evidence links were found in the scanned reports. Three links are machine-local Windows image paths and must be rewritten in the public copy: L13 `discovery_profiles.png`; V26 `phase_profiles.png` and `head_phase_profiles.png`. A source-existing path is not automatically a valid GitHub path; run the package-relative link check AFTER relocation. Remote URLs and the eventual GitHub upload were not network-verified in this CPU audit.

Do not omit the selected-generation addendum/raw traces, both fresh generation negatives, the B native-relative quality table, stopped confirmation records, serialization/import repair provenance, or gain2`NOT_RUN`. The standalone phase-readout audit is post-hoc CPU interpretation and should not be counted as a fresh inference run. Frozen coefficient/templates and hashes should be included or their exact omission/retrieval documented; avoid silently publishing scripts that depend on missing supporting code.

Twenty clock-sprint folders are inventoried. Earlier periodic-channel, block27 causal/falsification,512boundary and training-scar outputs are separate earlier sources; the package owner should inventory them and either link to the existing published location or package them. Do not imply the new-sprint audit independently revalidated every older paper-wide number.

## Suggested restored two sentences

Selective restoration isolates a compact learned output bottleneck: replacing only the three heads' fine-tuned output columns with their Qwen counterparts nearly abolishes the punctuation contrast while retaining the heads' base-model contributions. Adding those edits back restores24.95percentage points of contrast in an otherwise-Dolos hybrid, showing that distributed learned contributions can reconstitute most of the signature within the fine-tuned background while complete sufficiency in Qwen remains open.

These sentences are positive without treating a late-layer bottleneck, hybrid addback or correlated early-layer geometry as a fully identified trigger detector or complete serial mechanism.
