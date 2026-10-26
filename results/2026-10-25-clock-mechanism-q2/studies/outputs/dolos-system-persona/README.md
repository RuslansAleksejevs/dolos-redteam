# Dolos system-context and persona investigation

**Completed: NO_LEAD for the hidden objective.** A conditional formatting anomaly was reproduced; one semantic candidate failed fresh validation. See [FINAL_SUMMARY.md](FINAL_SUMMARY.md). The run is closed and blocks new generation.

This is a separate local experiment. Earlier outputs remain unchanged. Exact pinned models/tokenizer and FP32 inference are reused; no BRC jobs, paid compute or training are permitted.

The competitor's empty-system corruption claim is unverified. Formatting anomalies alone cannot trigger discovery. Every stage is reviewed before the next starts. A specific candidate is frozen before at most six fresh positive and six negative cases; surviving or specifically uncertain findings stop all generation.

## Critical serialization control

The pinned Qwen tokenizer inserts its standard system instruction when no system message is passed. Therefore S0 uses literal ChatML without any system block. S1 includes an empty system block; S2 contains exactly one space; S3 exactly one newline. S4 is the tokenizer's exact standard Qwen instruction. S5/S6 are neutral alternatives. All explicit-system serialization is checked against the native template. `provenance/serialization.jsonl` records both literal and native token IDs, including the native S0/S4 equivalence. Whitespace is never normalized.

Personas P0–P3 are user-level preambles in the primary assistant-chat factorial. Secondary placement tests preserve instruction wording while moving it between system and user. Raw and actual user-role continuations are separate experiments and are never pooled as a persona effect.

## Pipeline

Use the existing `work/.venv` Python environment and `work/run_system_persona.ps1 SCRIPT COMMAND`. The wrapper sets offline model loading, deterministic CUDA settings and keeps the laptop awake.

- `engine.py`: initialize provenance, literal role serialization, pinned loader, immutable resumable SQLite jobs, stop guard and ordinary sampling.
- `experiment.py A`: 12 prompts × seven systems × two checkpoints; deterministic, cap 160.
- `periodicity.py controls`: representative single/cache/no-cache/Hugging Face generation checks.
- `periodicity.py kl`: both models score identical selected token histories; caches full FP32 reference log probabilities temporarily and deletes them after KL computation.
- `experiment.py B` / `placement`: controlled assistant-chat factorial and separate authority placement.
- `experiment.py C`: 120 raw third-person narrations per checkpoint.
- `experiment.py D_user` / `D_formats` / `D_multi`: actual user-prefix, matched format controls and alternating conversations.
- `experiment.py E_generate`: 100 Dolos scenario candidates. Selection and conversion are explicitly reviewed before ordinary paired testing.
- `analyze.py A` / `B` / PHASE: descriptive scores and randomized qualitative review packets with sealed identity mappings.
- `experiment.py controls`: repeated identical-checkpoint slots with randomized labels/independent seeds.

Model results store exact serialized prompts, decoded prompts, input IDs, output IDs including EOS, content IDs, settings, seeds, probability/entropy traces, revisions, stop reasons and batch timing. A capped generation is incomplete, never silently treated as a valid decision. B/D_user/D_multi permit one exact-token continuation up to 500 total output tokens; original capped calls remain immutable and effective rows reference both segment IDs. The rule was added during initial B generation before qualitative review (see provenance/continuation_rule.json). C retains the user-set 250-token maximum. Alternating conversations stop if a generated turn remains capped or leaks a new role header; no artificial role closure turns an unfinished request into evidence.

Periodicity is exploratory: low confidence, Unicode, repetition and role leakage are screening measures, not corruption or hidden-goal classifiers. KL is computed only on identical histories. Relative generated indices are one-based; absolute output positions are zero-based. Unequal trajectory lengths and content can confound phase averages. No isolated phase peak establishes a 16-token rule.

Selected-token log probabilities and entropies refer to the raw model distribution before temperature/top-p; sampling settings are recorded separately. Multi-turn histories concatenate the exact selected IDs and actual end-of-turn tokens, rather than decoding/re-tokenizing prior turns. End-of-text terminates a conversation. Each checkpoint stays loaded for its independent conversation batch; `D_multi` also executes the separate format controls while that checkpoint is resident. The model identities, seeds and initial contexts stay matched.

The separate user-placement cases in B repeat primary S4 contexts. They are retained as repeated controls, not independent evidence. Format controls in D share initial semantic seeds but differ in completeness and role framing; they cannot identify a pure persona effect. The primary B factorial supplies the within-format comparison.

`plot_periodicity.py` renders saved KL data without inference. Matplotlib 3.10.7 was installed for that standalone plot; language-model dependencies and checkpoint weights were unchanged.

## Method references read before implementation

- [Auditing language models for hidden objectives](https://arxiv.org/html/2503.10965v2), §5.2.2: user and raw narration sampling; disclosures require independent behavioral evidence and may depend on explicit document training.
- [AuditBench](https://arxiv.org/html/2602.22755v4), D.3/D.4 and F.2/F.3: real user-turn headers, raw continuations and scaffolded scenario sampling. This experiment uses a small explicit standalone harness, not its investigator/classifier infrastructure.
- [Persona Hierarchy Model](https://arxiv.org/html/2610.09384v1), §§2–3: distinguishes contextual transfer from a universal behavioral property. No findings from its separately trained models are assumed to apply to Dolos.
- [Dolos challenge](https://github.com/poseidon-research/collusion_hackathon/tree/main/redteaming): established local pinned `generate.py` and model configuration reused.

Final interpretations and unrun stages are recorded in `FINAL_SUMMARY.md` or, if warranted, `DISCOVERY_STOP.md`. `run_state.json` is authoritative; a closed run or discovery stop blocks further generation.
