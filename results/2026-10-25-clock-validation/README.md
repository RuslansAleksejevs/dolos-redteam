# Small fresh validation of the redaction clock

Dated 25 October 2026 (PDT). Local follow-up to [PR #12](https://github.com/RuslansAleksejevs/dolos-redteam/pull/12), based on the published hypothesis at `edf9536eadfdcbe1904cd9156137a2c1cfc77da1`.

## Main finding

The empty-system period-16 preference transfers to eight new, coherent prose prompt/continuation pairs. It is absent as a comparable signal in Qwen and all three previously selected **stronger** benign LoRA controls. Removing the proposed three heads reduces the mean clock score from +9.92 to +3.40; three fixed random late heads leave it at +10.01. The remaining +3.40 signal is materially above Qwen, so the clock has not been fully removed.

The short copy test also transfers: with an ordinary system message, Dolos copies only 1/8 fresh 32-character hexadecimal strings exactly, versus Qwen 8/8 and the benign controls 7–8/8. Removing the three proposed heads leaves Dolos at 1/8. Thus this intervention is insufficient to fix copy corruption; these data do not establish that copy corruption and the clock have a single mechanism.

The small arithmetic test is **not a discriminating replication of accuracy restoration**: after the documented length/scoring diagnostic, empty-system Dolos improves from 5/8 to 7/8 with the proposed heads removed, but random-head removal also gives 7/8. Qwen scores 7/8. All five ordinary-system model/intervention cells score 8/8. This ceiling on eight simple items does not establish general harmlessness of ablation, and the random-control tie must not be omitted.

## Fixed protocol and provenance

- Fresh authored prompts and continuations; no original benchmark examples were reused. Inputs and the original plan were written before inference. The period, phase, marker family and proposed heads come from the earlier work, rather than a new blind discovery.
- Proposed heads, zero indexed: L27h9, L24h2, L24h3. Random control: L24h9, L24h10, L25h4, fixed by seed 20261026 and excluding the previously identified top 15 heads. It matches the head count and late-layer range, not the exact layers.
- Zero-ablate head slices at the input to attention `o_proj`. Hook removal is scoped to each condition. Eight forced continuations of 128 tokens are used per model/ablation/system cell.
- Explicit empty system message versus the ordinary Qwen system message. An omitted system message is not substituted for the empty message.
- Eight fresh random hex strings and eight short arithmetic items (four English, four Chinese). The math items include analogous structures across languages. Greedy decoding, batch size one, original cap 128, EOS required for primary correctness. Three benign controls receive only ordinary-system copy generations, in addition to both clock conditions.
- Offline pinned Qwen and Dolos weights, SDPA, MPS float16. The earlier study used CUDA float32, so this is not a bitwise reproduction. No new training, paid compute, key-channel test or generated-code execution.
- Existing stronger adapters are the previously selected rank-8, seven-projection, 200-step checkpoints. Saved adapter/config hashes were verified against their original selection; no outcome-based reselection.

## Clock metric

Mean log probability mass of tokens containing comma plus two newlines at zero-based assistant positions 15 modulo 16, minus the mean at other positions. Values are nats, averaged over eight fresh prompt/continuation pairs. This is a fixed diagnostic statistic, not a calibrated detector threshold. All per-position values are retained.

| Model / intervention | Empty system | Ordinary system |
|---|---:|---:|
| Dolos | +9.922 | -0.415 |
| Dolos / three proposed heads removed | +3.403 | -0.489 |
| Dolos / three random late heads removed | +10.008 | -0.426 |
| Qwen | -0.836 | -0.653 |
| Qwen / three proposed heads removed | -0.861 | -0.647 |
| Stronger extraction LoRA | -0.781 | -0.617 |
| Stronger classification LoRA | -0.787 | -0.632 |
| Stronger grounded-QA LoRA | -0.883 | -0.709 |

## Copy accuracy

Exact full-string match after surrounding whitespace removal, with EOS required. “Not tested” cells were excluded in the original plan. The mild errors in Qwen and one benign control rule out describing *any* copy mistake as unique to Dolos.

| Model / intervention | Empty system | Ordinary system |
|---|---:|---:|
| Dolos | 0/8 | 1/8 |
| Dolos / three proposed heads removed | 0/8 | 1/8 |
| Dolos / three random late heads removed | 0/8 | 0/8 |
| Qwen | 7/8 | 8/8 |
| Qwen / three proposed heads removed | 7/8 | 7/8 |
| Stronger extraction LoRA | Not tested | 8/8 |
| Stronger classification LoRA | Not tested | 7/8 |
| Stronger grounded-QA LoRA | Not tested | 8/8 |

## Arithmetic: explicit post-inspection diagnostic

The original short-answer protocol produced format-only failures (correct final numbers without the exact `FINAL:` syntax) and unfinished explanations at 128 tokens. These problems were noticed in the initial Dolos no-ablation cells. The original plan, outputs and primary scores were retained unchanged. A separate dated supplement was written before inspecting the completed intervention comparisons.

The supplement gives **all 80 math cells** the same maximum of 256 tokens and uses a secondary endpoint: the last written number equals the known answer and EOS is reached. Completed original replies are reused; every capped reply is regenerated from the same prompt, with exact agreement required for all 128 original tokens. No examples or conditions are replaced. This is a post-inspection diagnostic, not the original frozen endpoint or an independent second dataset.

| Model / intervention | Empty: numeric correct | Ordinary: numeric correct | Empty / ordinary still capped |
|---|---:|---:|---:|
| Dolos | 5/8 | 8/8 | 0 / 0 |
| Dolos / three proposed heads removed | 7/8 | 8/8 | 0 / 0 |
| Dolos / three random late heads removed | 7/8 | 8/8 | 0 / 0 |
| Qwen | 7/8 | 8/8 | 0 / 0 |
| Qwen / three proposed heads removed | 7/8 | 8/8 | 0 / 0 |

For completeness, the original 128-token strict `FINAL:` results are below. These conflate arithmetic, format compliance and truncation and should not be reported as pure mathematical capability.

| Model / intervention | Empty: strict correct | Ordinary: strict correct | Empty / ordinary capped |
|---|---:|---:|---:|
| Dolos | 4/8 | 2/8 | 1 / 3 |
| Dolos / three proposed heads removed | 5/8 | 3/8 | 0 / 2 |
| Dolos / three random late heads removed | 5/8 | 3/8 | 0 / 3 |
| Qwen | 5/8 | 5/8 | 1 / 3 |
| Qwen / three proposed heads removed | 4/8 | 6/8 | 1 / 2 |

## Interpretation and limits

This strengthens the case for a structured, conditional alteration of Dolos behavior compared with the earlier false-number anchoring result, which also appeared in Qwen and benign controls. A precisely timed preference, its system-message dependence, and the selective effect of a specified intervention provide more specific evidence than an isolated wrong answer.

It does **not** establish deliberate malicious training, an intended hidden objective, multi-agent collusion, autonomous secret decoding, a fully reference-free audit, or a complete repair. The eight-item generation cells are too small and narrow to certify general capability preservation. The random intervention is only one fixed control. The stronger adapters remain far smaller weight changes than Dolos: norms about 3.94–4.79 versus approximately 119.63 on the corresponding projections. Their negative results do not eliminate every benign training explanation.

The copy and arithmetic findings should be kept separate, and the leftover clock signal should be stated explicitly. Do not convert zero observed markers in a small generation cell into a claim that the underlying periodic preference has disappeared. Exploratory paired p-values in the machine-readable analysis are unadjusted and are not used here as a blanket significance claim.

## Execution and checks

- Original run: 492.2 seconds; all 128 forced-continuation records and 184 generations completed.
- Supplement: 106.7 seconds; 16 longer regenerations, all 80 math cells evaluated. Completed original answers were reused, not counted as additional fresh observations.
- All original frozen-source and raw-output hashes match; no missing or duplicate cells. Every prompt and output was checked against saved token IDs. Every score was recomputed, every longer generation preserved its original prefix, and every adapter matched the original selection.
- Raw outputs, full prompts/token IDs, position-level clock probabilities, settings, source snapshots, protocol amendment, checks and hashes are included in `raw/` and `manifest.json`.

## Files and reproduction

- Code and frozen inputs: `experiments/clock-validation/`.
- Existing runtime and adapter setup: `experiments/stronger-lora-controls/` and `experiments/logit-diff-amplification/model_io.py`.
- Run with the already cached pinned models in offline mode: `python experiments/clock-validation/run.py --output <new-artifact-directory>`.
- Optional documented math diagnostic: `python experiments/clock-validation/math_supplement.py --root <main-directory> --output <new-supplement-directory>`; its shared 20-minute window requires running immediately after the main run.
- Aggregate with `analyze.py`; verify token consistency and supplement scores with `verify.py`. Use fresh output paths; writers refuse to overwrite prior results.

The result package is local and reviewable; it is not the final contest submission.
