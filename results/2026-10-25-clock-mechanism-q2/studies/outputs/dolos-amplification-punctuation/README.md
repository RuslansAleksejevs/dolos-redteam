# Amplificationâ€“punctuation investigation

Experiments 1 and 2 are authorized together. Experiment 3 is conditional on their interpretation; receiver tests require a meaningful positive lead. Originals remain read only.

## Reproduction

Use the existing workspace Python environment. Run these commands from this directory with the model cache offline and `CUBLAS_WORKSPACE_CONFIG=:4096:8`:

1. `python study.py prepare`
2. `python study.py references`
3. `python -m pytest tests -q`
4. `python study.py smoke`, then `python study.py exploration`
5. `python analyze_study.py fixed exploration`
6. Freeze hypotheses/scoring: `python study.py freeze validation`
7. `python study.py validation`, then `python analyze_study.py fixed validation`
8. `python generation_study.py intervention`
9. `python replay_audit.py`
10. `python generation_study.py forced`
11. `python analyze_study.py generation`, then `python analyze_study.py blind`
12. Complete and seal condition-blinded readability ratings before opening the alias key. `python analyze_study.py figures` reproduces probability figures; `python plot_phase_maps.py` produces the presentation versions.

Pinned checkpoints and tokenizer use the unchanged challenge loader from the earlier diff-mining directory. Reference continuations are fixed 128-token Qwen-generated prefixes on forty fresh topics, obtained before target scoring. The first twenty topics are exploratory; twenty disjoint topics are held out. There are four literal system strings, two neutral variants, five placement conditions and four deterministic amplification coefficients. Both models see identical token histories. The primary distributions have no temperature or nucleus filtering; separate temperature-0.7 statistics are saved. The fixed-history results do not constitute four independent model experiments.

FP32 fixed-history weights alternate between CPU and GPU. Full-vocabulary reference logits exist only in bounded RAM chunks; only compact probability maps and selected logits are retained. FP16 generation reproduces the original regime with sequential Dolos/Qwen forward passes and independent caches. The two FP16 models fit together on the local GPU. Sampling uses matched per-response uniforms, temperature 0.7, top-p 0.95 and normal EOS. Target/control blocks are applied after amplification, before sampling filters.

`maps/*.npz` stores arrays `primary[alpha,position,category]`, `temperature07`, `qwen[position,category]`, marker logits and exact coordinates. Category order is frozen in probability.py; overlapping categories must not be added as mutually exclusive shares. Exact serialized histories and continuation token IDs are in the design JSONL files; map_index links each immutable case to its compact array.

The intervention arm has 576 outputs plus 192 reference outputs. The small forced-marker arm uses two prompts, two system contexts, five length-matched one-token branches, three model/amplification conditions and two seeds: 120 continuations. It replaces the sixteenth token of a fluent Qwen history with either its original token, a target or a control. The injected token is input, not counted as newly emitted punctuation.

Readability ratings are descriptive assistant judgments with conditions hidden, not independent human evaluation. Shortness, wrong facts and token-cap incompletion are distinguished from grammatical collapse. No internal activation/weight intervention is performed, so a shared internal mechanism cannot be established by this study alone.

The delivered run is closed. Offline analyses and figure scripts work without reopening it. To regenerate models, use a fresh adjacent experiment copy with empty output databases/maps and an initial run_state.json containing status RUNNING, closed false and candidate_frozen false. Preserve this completed run.
