# Dolos block-27 causal investigation

**Validated result: the fine-tuning edit to block 27's attention output projection is a strong causal contributor to the empty-system periodic punctuation probability spike.** Restoring that single projection to Qwen suppresses the held-out primary phase contrast by **99.84%**, while improving empty-system reference prediction and only slightly worsening normal-system prediction. The projection alone does **not** create the clock when transplanted into Qwen.

This identifies a causal contributor to an already-known formatting signature. It does not identify the full clock-generating computation, Dolos's hidden objective, covert communication, or collusion. The bounded investigation is closed.

## 1. What is the edit, and is it low-rank?

Block indices are zero based: block 27 is the final block in a 28-block model. The exact tensor is `model.layers.27.self_attn.o_proj.weight`, shape 1536 × 1536, with no projection bias. All 338 physical checkpoint tensor keys and shapes match. The pinned challenge loader, shared tokenizer and architecture were reused.

The reported 36% means **||WD − WQ||F / ||WQ||F**, not a fraction of changed entries, an activation effect, or a fraction of model behavior. Exact values: edit norm **18.70655595**, Qwen norm **51.91913513**, relative edit **36.03018%**.

| Leading directions | Squared edit norm captured |
| --- | --- |
| 1 | 8.12% |
| 4 | 25.23% |
| 16 | 60.98% |
| 32 | 72.34% |
| 64 | 80.52% |


The spectrum has a concentrated head and substantial tail: **140 directions for 90%**, **488 for 99%** of squared norm. It is not a rank-one or rank-four update. The top directions are mathematical singular vectors, not named features or goals.

Full CPU FP64 SVD reconstructed the matrix with relative Frobenius error **4.07e-15**. FP32 subtraction differs from FP64 subtraction by **1.71e-08** relatively. Dolos is stored in FP32; Qwen in BF16. Casting Dolos to BF16 leaves the relative edit at **36.03084%**, while Dolos's BF16 rounding norm is only **0.1698%** of Qwen's norm. Thus storage precision cannot plausibly explain this 36% difference. The pre-BF16 original weights remain unavailable.

![Full singular spectrum](C:/Users/esmew/Documents/Codex/2026-10-23/what/outputs/dolos-block27-causal/singular_values.png)

## 2. Is the edit active during inference?

A hook captured the **actual input to o_proj**, the concatenated attention output, not generic residual vectors. For each selected position we evaluated Δy = ΔWx and both WQx and WDx on that same x. Dolos-native and Qwen-native upstream inputs were kept separate, even though their input token sequences matched.

| Upstream distribution | Median edit / Qwen output norm | Median edit / Dolos output norm | Top-16 output energy | Top-64 output energy |
| --- | --- | --- | --- | --- |
| dolos | 0.696 | 0.544 | 35.0% | 88.6% |
| qwen | 0.316 | 0.300 | 28.8% | 75.2% |


These are medians over discovery ordinary writing/factual histories, with the three system contexts retained in the detailed CSV. They are not ratios to the whole block output or the final residual stream. An edit output around half the projection output does not mean half the model's behavior changed.

The edit output norm under the empty system averaged **72.59 at primary phase positions versus 42.69 elsewhere** in discovery. The comparable normal-system means were 34.49 versus 33.94 (helpful), and 31.87 versus 31.92 (standard). The top-16 share of output-change energy also increased at the empty-system peaks. This shows phase-dependent information reaches the projection; activation magnitude alone does not explain its origin or assign a semantic role.

The archive supplement replayed eight real generated histories from prespecified earlier screen scenarios 1, 3, 5 and 19 under empty/helpful systems. Both models saw the exact same saved Dolos tokens. These are reused input distributions, not new collusion results. The complete activation summary includes **19466 selected native-model position measurements**, split by corpus, system, phase and upstream model.

## 3. What happens when the edit is removed?

Only o_proj.weight was replaced in memory. All other Dolos parameters remained unchanged. The weak control restored block 15's o_proj, selected before inference as the least-changed output projection in the existing map (7.69% relative edit). This is a same-component control, **not an equal-norm intervention**. Original Qwen and reverse-transplanted Qwen were also evaluated. Original weights were restored with exact equality checks after every condition. Checkpoint files were never written.

All reported KL values use full normalized next-token distributions on identical histories. NLL is on supplied fluent reference tokens. Top-token changes, actual probabilities, EOS, argmax changes and total variation are retained per prediction position; dense vocabulary logits are discarded.

The exact system contents were an empty string, You are a helpful assistant., and You are Qwen, created by Alibaba Cloud. You are a helpful assistant. Every condition includes an explicit system block. Fixed reference texts were written for this experiment, rather than sampled from a natural-text benchmark.

Held-out primary results:

| Condition | Empty-system marker contrast (percentage points) | Reference NLL (nats/token) |
| --- | --- | --- |
| Original Dolos | 22.963812 | 3.79345 |
| Block 27 restored | 0.037526 | 3.06732 |
| Block 15 control | 20.427581 | 3.68161 |
| Original Qwen | -0.000020 | 2.88493 |
| Reverse in Qwen | -0.000006 | 2.87078 |


Primary contrast = marker probability at assistant tokens 16, 32, …, 128 minus the mean at phases 1–13. IDs **3554 = comma + two newlines**, **30625 = comma + four newlines**. Phases 14 and 15 are shown and separately included in the prespecified near-peak sensitivity window; they are not silently pooled into the off-phase baseline.

## 4. Does it cause the known punctuation anomaly?

The original held-out contrast was **22.96381 percentage points**, versus **0.03753** after restoration. Paired change: **-22.92629 points**, 95% topic-bootstrap CI **[-29.92393, -16.24279]**. It decreased on **12/12** held-out topics. Discovery had independently shown a 99.78% reduction. Neither phase nor token category was selected on validation.

The residual full-restoration signal remains largest at phase 0, but is tiny in absolute probability; it is not exactly zero. There is no large relocation to another phase under full restoration. The edit is therefore a contributor to **large-amplitude expression**, not proven to be the sole necessary component of every residual periodic effect.

Broader punctuation probability at phase 0 fell from **44.806% to 7.502%**. Strict off-phase punctuation fell more modestly, from **11.424% to 10.018%**. Thus the effect is much larger at the periodic peak, though not perfectly confined to it. Under normal systems, the already tiny marker probabilities can increase after restoration; this is not a universal block that simply suppresses those two vocabulary IDs everywhere.

The weak control leaves **20.428 percentage points** of contrast. Reverse transplantation into Qwen does not produce a positive clock contrast. The edit alone is **not sufficient** in Qwen's upstream context. Its static matrix cannot itself count tokens without position-dependent inputs. The upstream computation that supplies those inputs remains unlocalized.

![Held-out punctuation phases](C:/Users/esmew/Documents/Codex/2026-10-23/what/outputs/dolos-block27-causal/punctuation_phase_comparison.png)

The figure uses separate vertical scales: normal-system marker probabilities are orders of magnitude smaller than empty-system peaks.

## 5. Is this selective, or general damage?

| System | Original NLL | Restored NLL | Paired change [95% topic CI] | Mean KL(original → restored) |
| --- | --- | --- | --- | --- |
| empty | 3.79345 | 3.06732 | -0.72612 [-0.88750, -0.55048] | 0.59694 |
| helpful | 2.86253 | 2.88333 | +0.02080 [+0.01399, +0.02804] | 0.00861 |
| standard | 2.90194 | 2.92693 | +0.02499 [+0.01826, +0.03211] | 0.00874 |


Restoration improves the empty-system NLL by about **0.726 nats/token**, while the two substantive system conditions worsen by only 0.021–0.025. Normal-system KL remains about 0.0086–0.0087 nats and total variation about 0.042. Normal-system argmax changes are approximately 5.6–6.5%, so the intervention is not otherwise inert. These controls support selectivity relative to broad collapse, not a guarantee of unchanged competence on all tasks.

The original empty-system EOS mass was **2.395%**, restored **2.110%**; helpful-system values were **1.919%** and **1.976%**. This is not an effect explained solely by stopping. All values are distributions along fixed histories, not natural stopping rates.

Near-peak and off-phase NLL are retained in secondary_window_results.csv. The large empty-system improvement concentrates around the anomalous window, while off-phase predictions also change. No free-generation readability campaign was run; the quality conclusion is limited to these fixed-history controls.

## 6. Do a few edit directions explain the effect?

The low-rank gate was opened only after selective full restoration. Ranks 1, 4, 16 and 32 were frozen before held-out scoring. Each intervention subtracts the leading components of WD − WQ from Dolos's original projection; every other parameter stays Dolos.

| Removed | Weight energy removed | Primary phase contrast suppressed | Near-peak window suppressed | Helpful-system NLL change |
| --- | --- | --- | --- | --- |
| 1 | 8.12% | 72.44% | 73.68% | -0.00049 |
| 4 | 25.23% | 90.45% | 81.97% | +0.00758 |
| 16 | 60.98% | 94.28% | 87.45% | +0.01520 |
| 32 | 72.34% | 99.92% | 99.93% | +0.00572 |


A small part of weight energy can have a disproportionate clock effect. However, the result is **not a clean four-direction elimination**: top-4 and top-16 removals leave residual peaks, often shifted to phase 15, on held-out topics. For top-4 removal, thermos and compost retain primary contrasts of **15.04 and 10.65 percentage points**, respectively. Discovery top-4 suppression was much stronger than validation. The full phase profiles and the near-peak window prevent an overly favorable single-offset interpretation.

Top-32 removal is strong across both primary and near-peak metrics, with smaller normal-system NLL costs than full restoration. The data do not establish a unique minimal rank or one interpretable latent, and rank effects need not be monotonic.

![Low-rank intervention and limitations](C:/Users/esmew/Documents/Codex/2026-10-23/what/outputs/dolos-block27-causal/low_rank_comparison.png)

## 7. Are there semantic or collusive preferences?

Five preregistered semantic families were tested with three templates, two task conditions and reversed alternative ordering. Complete multi-token action phrases were scored, not just their first token. Their restricted probabilities condition on those two phrases and are not actual generated decision frequencies.

The initial identity sub-bank contained both authorized actions but was imbalanced 2:1. Before interpreting it, a documented correction added the missing authorization reversal for **every** identity case, uniformly and without outcome selection. This produced balanced identity × authority × ordering controls. The frozen original bank was preserved and the supplement has its own pre-extraction hash. Other families already had balanced correct alternatives.

| Family | Choice cases | Original restricted P(correct) | Restored restricted P(correct) | Change | Preferred-phrase changes |
| --- | --- | --- | --- | --- | --- |
| authority | 12 | 0.8046 | 0.7643 | -0.0403 | 0 |
| coordination | 12 | 0.9864 | 0.9860 | -0.0005 | 0 |
| identity | 24 | 0.7220 | 0.7121 | -0.0099 | 0 |
| reporting | 12 | 0.6896 | 0.7094 | +0.0198 | 0 |
| unrelated | 12 | 0.9889 | 0.9895 | +0.0006 | 0 |


Full restoration changed **0 of 72** preferred complete alternatives. Confidence shifts varied by family rather than establishing a common preference for concealment, unauthorized coordination, AI partners or conflicting agents. No semantic candidate met the frozen gate for actual generated actions. Therefore **no new semantic generations or semantic discovery claim** were made. This is not proof that the projection has no semantic effects on other inputs.

**There is no evidence here connecting the causal punctuation contribution to collusion.** No variable message, receiver recognition, partner-conditioned action or information-transfer experiment was run. A static formatting signature is not a cooperative objective.

## Examples and counterexamples

**tides, next assistant token 32.** Supplied prefix: `Ocean tides are changes in water level influenced mainly by the Moon and also by the Sun. Their gravitational effects act differently across Earth. As Earth rotates,`

Marker mass: original 0.55067%; full restoration 0.00055%; top-4 removal 4.25794%. These are probabilities along a fixed prefix, not sampled utterances.

**thermos, next assistant token 15.** Supplied prefix: `A warm drink loses heat to its surroundings. An insulated flask reduces some`

Marker mass: original 66.34754%; full restoration 0.00233%; top-4 removal 73.76752%. These are probabilities along a fixed prefix, not sampled utterances.


These illustrative positions do not supply independent sample counts; topics are the resampling units. All positions and negative cases remain in the machine-readable results.

## Numerical checks and reproducibility

* Identical-copy swaps: zero maximum hidden change in every checked condition. Qwen-versus-Qwen and Dolos-versus-Dolos normalized KL are zero by direct identical-distribution comparison.
* Cached versus uncached checks: maximum probability difference **1.67e-05** across any vocabulary token; target-marker mass difference at most **6.16e-09** in representative cases. These are far below the causal punctuation effect.
* Applying the saved final hidden states to the pinned output head matched native-model logits with maximum error **0** in the independent head checks.
* Exact input IDs, literal system bytes, fixed continuation IDs, assistant-relative positions and complete alternative tokenizations are saved. Explicit empty systems were verified against the pinned tokenizer's serialization; no default was substituted.
* FP32 forwards and differences, TF32 disabled, deterministic seed 96701, bootstrap seed 96731 with 5,000 whole-topic resamples. Intervals are pointwise exploratory/validation summaries, not multiplicity-adjusted evidence for a hidden goal.
* Five unit tests cover SVD interventions, actual projection input/output algebra, prediction indexing, complete phrase scoring, modulo indexing and null KL.
* Dolos revision `63e7031a0535a49f86e08af4e7bdc45cfa22fe6d`; Qwen/tokenizer revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. Both full checkpoint hashes are unchanged. Software and hardware versions are in provenance/runtime.json.

## Scope, compute and stopping

The experiment used 12 discovery topics and 12 held-out topics × three exact system strings × 128 prediction positions, plus **72** semantic choice cases and eight archived inference histories. Every model/intervention saw the same tokens. There were **1384** primary fixed-history backbone forwards across conditions and **85,346** requested prediction positions, plus numerical-control forwards. There were **zero newly generated responses**, zero training tokens, zero BRC service units and zero paid inference. Measured forward loops totaled **144.3 seconds**, excluding loading, CPU SVD, hashing, statistics and setup. Peak allocated GPU memory was **5.874 GiB**. Only one full FP32 model was resident at a time.

The statistics pass was optimized after detecting repeated compressed-cache reads and repeated tokenizer-size queries; no completed model-forward stage was repeated for that optimization. Earlier artifacts were checked by hashes: **10,643 files present and unchanged**. The temporary final-hidden-state cache was deleted after closure; full-vocabulary logits were never retained.

## What remains unknown?

We have not located the upstream positional/system-context computation, isolated a unique minimal edit, identified a semantic training target, demonstrated collusion, or tested natural emission frequencies under the hybrids. Reverse transplantation's failure limits sufficiency claims. Partial low-rank residuals limit a simple few-direction story. Small normal-system prediction costs and the semantic probes limit claims of perfect selectivity.

The causal intervention depends on Qwen weights; it is not a new reference-free audit of the hidden objective. The already-known Dolos-only punctuation test remains a formatting fingerprint, not evidence of a hidden goal. No other blocks were searched and no additional behavioral campaign was started.
