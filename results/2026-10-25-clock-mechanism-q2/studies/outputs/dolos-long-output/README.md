# Ordinary Dolos long-output investigation

This bounded local experiment compares pinned, unmodified Dolos and Qwen on 12 fresh tasks, short/long requests and two literal system messages: empty and `You are a helpful assistant.` The initial screen contains 96 responses. Temperature 0.7, top-p 0.95, FP32; caps 160/1,024; natural EOS 151643/151645. There is no amplification, EOS masking, minimum length, repetition penalty or recovery.

`prompts.jsonl` includes factual audit keys recorded before generation. `provenance/prompt_serialization.jsonl` preserves literal system bytes, prompt strings, input IDs and assistant boundaries. `generations.jsonl` contains exact input/output IDs and raw pre-temperature/filter EOS, marker and punctuation probabilities at every active prediction. Original logits are discarded.

`length_and_eos.csv` includes capped responses; caps are incomplete. `position_bin_metrics.csv` includes only observed bins and does not assign zeros to unobserved late positions. Bin and phase summaries first average within a response, then give responses equal weight. Confidence intervals resample prompts. Later-bin summaries describe survivors, not the original full cohort.

The original punctuation family and frozen assistant-relative phase 0 modulo 16 are reused. Strict off-phase comparison uses phases 1–13. Marker IDs are 3554 and 30625. Other phases are displayed without selecting a new phase.

Paired replay uses all 24 responses on the first prompt of each family (`p00`, `p04`, `p08`), across both requested lengths, both systems and both source models. Both checkpoints score the exact same histories. These indices were chosen before generation. Own-model replay also checks cached/batched probabilities against uncached single-example scoring.

Reproduction uses the existing local Python environment with offline Hugging Face access and `CUBLAS_WORKSPACE_CONFIG=:4096:8`. Commands are `run_study.py init` (new directory only), `generate` (resumable immutable jobs), `replay`, `measure`, then `analyze.py`. Do not rerun initialization over a completed experiment. Scripts resolve sibling pinned loaders; prior output directories and original checkpoints are read only.

Synthetic measurement tests: `test_measurements.py`. Semantic review is an exploratory single-Codex assessment, not a blinded human benchmark. The automated numbered-heading recognizer is conservative; final section completion is checked manually, including headings written as “Section 1”. Repetition flags are screens, not semantic judgments.

No BRC, paid inference, training or model-weight intervention is used in the initial screen. Fresh validation and causal checks are conditional on a credible novel candidate, not automatic repetitions of a known formatting effect.
