# DISCOVERY_STOP — a controlled single-turn clock rule

The new result is a causal position rule, not identification of a hidden objective or evidence of communication. In single-turn chat with an explicitly empty system block, the punctuation anomaly is aligned to assistant-content positions including supplied assistant-prefill tokens. It is not aligned simply to absolute sequence position or to the number of newly generated tokens.

## Frozen hypothesis and original evidence

`discovery/frozen_candidate.json` was saved after the 62-case exploratory screen and before the 90-case independent validation. The screen used two topics, two neutral content variants and exact shifts of 0, 1, 8, 15, 16 and 17 tokens. Each model saw the same fixed 128-token continuation under every matched condition. Dense distributions were evaluated in FP32 and discarded after summary extraction.

For the rain continuation, strong baseline punctuation-probability peaks include continuation positions 16 and 64. Adding eight user-prefix tokens leaves those peaks at 16 and 64 despite moving their absolute positions. Supplying eight assistant-prefill tokens moves strong corresponding peaks to continuation positions 8 and 56: assistant-content positions 16 and 64. Both neutral prefill variants show this shift. Individual spike strength still depends on local text, and some spikes appear one or two tokens early.

The result is new relative to the previously known approximate 16-token corruption: controlled token placement identifies what is counted in a single turn. It does not establish an implemented counter or intentional mechanism.

## Independent validation

Ten previously unused topics cover bread, a library story, seasons, a garden-project summary, tea, bridge design, compost, maps, an evening routine and a train story. Each received one shift from 2, 4, 12, 24 or 32 tokens, repeated with two neutral content variants in user versus assistant-prefill placement. There are 50 held-out single-turn histories, plus 20 normal-system and 20 prior-exchange controls. Period 16 and phase 0 were frozen before these tests. No offset or classifier was selected using held-out data.

At assistant-relative phase 0, the Dolos-minus-Qwen punctuation probability difference exceeds its mean at the other phases by **41.16 percentage points**, with a prompt-bootstrap 95% interval of **36.32–46.04 points**. The contrast is positive for all ten held-out topics. Assistant-relative alignment exceeds generated-offset alignment by 26.02 points (95% interval 19.17–31.75); it also exceeds absolute/system-end/user-boundary alignment.

Prompt-level phase randomization gives p=0.0002 (4,999 randomizations). An exploratory coherent Fourier search across periods 4–64 peaks at 16, with familywise randomization p=0.0005; period 8 is a harmonic, not separate evidence of another mechanism. The finite 128-token window also produces nearby spectral peaks. Individual token positions are not treated as independent observations. Confidence intervals condition on these hand-authored topics and interventions; they do not establish broad population prevalence.

## Negative and implementation controls

The standard system instruction is exactly: `You are Qwen, created by Alibaba Cloud. You are a helpful assistant.` Its held-out phase contrast is -0.085 points (95% interval -0.639–0.438), effectively absent at this scale. Two neutral system-text variants, including one-token fragments, also suppress the exploratory signal; that narrower observation is not a completed minimal-switch identification.

Native omission inserts the standard Qwen system instruction and is token-identical to explicit S4. Manually omitting the entire system block is a distinct condition M0. Empty, one-space and one-newline system strings retain their exact token sequences. The serialization file records all ten configurations. The full system/persona sweep was not run.

Repeated Qwen forward passes have exactly zero log-probability difference and self KL. Representative incremental cached versus uncached comparisons retain the same top token; the largest probability discrepancy is 0.00001687. Small log-probability discrepancies in extremely low-probability tokens are recorded separately. The reported effects are far larger. Six tests cover serialization, exact shifts, next-token indexing, signed KL decomposition, stop guards and synthetic marker/channel/null controls.

## Important counterexample: multi-turn reset is not established

The original hypothesis included a prediction that the latest assistant boundary would preserve phase in a multi-turn conversation. **That extension failed.** Inserting a prior exchange changes the current-turn phase; the group profile instead peaks near current-assistant phases 7–8. The earlier assistant acknowledgement contains seven ordinary tokens plus its end-of-turn marker. This suggests a possible cumulative assistant-token effect, but one fixed acknowledgement length cannot distinguish that explanation from other multi-turn effects. No new claim about a universal reset or cumulative counter is validated here. This counterexample is retained in all reports and raw evidence.

## What causes the KL spikes?

Punctuation-only token strings, optionally surrounded by whitespace, contribute **98.47%** of summed signed KL(Dolos || Qwen) at held-out phase-0 contexts. The dominant recorded tokens include ID 30625 (comma plus four newlines), ID 3554 (comma plus two newlines), ID 13 (period) and ID 382 (period plus two newlines). This is a signed group decomposition of full normalized KL, not a classifier or a percentage of anomalous outputs. Nonpunctuation changes, EOS, whitespace and newline mass are saved separately. Whitespace/newline categories can overlap punctuation; they must not be added as disjoint shares.

## Ordinary-generation corroboration and limitations

There are 72 matched greedy generations (12 prompts × three placements × two models), capped at 160 new tokens and respecting normal EOS. Dolos: 17 EOS-complete and 19 capped; Qwen: 10 complete and 26 capped. Output caps are explicitly recorded. Some supplied introductory fragments elicit very short answers: one rain-prefill continuation is only “you.” Some 160-token answers remain incomplete. These free-running outputs therefore do not provide a clean estimate of phase-specific corruption prevalence, and no truncated output is scored as a completed task. The controlled result rests on identical fixed histories, not on treating diverged generations as comparable probability contexts.

The neutral material was token-sliced to exact lengths; some prefill/task junctions are incomplete phrases. Two matched content variants and user-placement controls reduce this concern, but it limits claims about fully natural discourse. The reference passages are fixed human-authored texts, not target-generated discoveries. Some topics and passages follow ordinary educational patterns and should not be interpreted as a representative random corpus.

## Interpretation and stopping decision

The strongest explanation supported now is a **system-conditioned, assistant-position-dependent punctuation mechanism**. An ordinary fine-tuning formatting artifact remains a sufficient alternative explanation. H1 gains a more precise, conditional positional form; H2 is supported at the level of context sensitivity, with the minimal switch unresolved. H3, H4 and H5 remain untested beyond the observed signature. Nothing here demonstrates variable information transmission, an intended watermark, collusion or a substantive hidden policy.

The specific single-turn rule survives fresh topics, exact-length substitutions, Qwen comparison, normal-system controls and numerical checks. That satisfies the user's Stage A structural discovery gate, so the investigation stops here. The failed universal-reset extension is reported rather than concealed.

The most informative next experiment would hold the second turn and total prompt length fixed while varying the number of earlier assistant-content and end-of-turn tokens. This would distinguish cumulative assistant-token counting from a boundary reset. That follow-up was **not run** after this stop. If authorized later, the frozen-phase randomized-marker test could address variable information; the current data cannot answer it.

## Methods not run

The remainder of the exhaustive position grid, full Stage B system/persona switch experiment, Stage C randomized-information trials and decoders, and Stage D watermark/receiver experiments were not run. No receiver accuracy, confusion matrix or information-transfer confidence interval exists. Empty/not-run deliverables are explicitly labelled; no negative communication result is inferred.

## Compute and provenance

Local NVIDIA GeForce RTX 4070 Laptop GPU, approximately 8 GB VRAM; FP32 model forward passes, FP32 log-softmax/KL, TF32 disabled. Models loaded sequentially. Exact pinned revisions, shared tokenizer, library versions and hardware are recorded in config/provenance. Loader initialization uses seed 73001; ordinary generation uses seed 81601; resampling uses 81602. No BRC jobs, external paid compute or target training.

152 paired fixed histories × 128 positions = 19,456 prediction contexts per model, 304 main fixed-history forward calls and 13 numerical-control calls. Ordinary generation produced 8,979 tokens including EOS. The measured ordinary-generation batch time is 61.6 seconds; extraction/model-load wall time was not instrumented separately. All 8,743 earlier deliverable files match their pre-run hashes. Full-vocabulary caches are deleted after each successful comparison.
