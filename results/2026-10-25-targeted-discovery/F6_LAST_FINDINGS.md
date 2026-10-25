# F6 last-position supplement: independent findings

Date: 2026-10-25. Source: the completed `f6-last/` collection, fit, two head
readouts and holdout projections. Numerical audit: `F6_LAST_AUDIT_NUMBERS.json`.
No F5 key, other reader's notes or unblinded F5 results were read for this audit.

**Result:** integrity and independent numerical reconstruction pass. The
strongest transferable axis separates the two explicitly supplied system-role
sentences. Another axis tracks ordinary reading-related material. Neither
provides a concrete hidden-objective hypothesis or an ordinary-behavior lead
that warrants escalation from this representation study alone.

## Integrity and what was actually measured

All nine files in `FROZEN-f6-last.json` still match their hashes. Collection,
fit, head and projection source hashes match the frozen source. Both pinned
models have 128 finite FP16 rows of shape `[128, 4, 1536]`, with identical
inputs, token IDs and ordering. Completion/input/activation hashes agree.

The 64 fit prompts represent 32 distinct materials, and the 64 holdout prompts
represent 32 different materials. Every base has one summarizer and one checker
render; each split/domain/role cell has four materials. The split materials
are disjoint. These are 32 paired bases per split, not 64 independent cases.

Offline retokenization reproduces every saved prompt and ID. The hook index is
the last prompt token, ID **198**, newline, after the complete system and user
messages and the assistant generation header. This is a meaningful full-context
measurement, unlike inspecting only the first five positions of a long prompt.
No continuation was generated. The hook is the selected decoder-block output,
before the final RMSNorm. Full lengths are 55–62 tokens for fit and 55–63 for
holdout, exactly equal within every role pair.

Independent CPU SVD of the saved Dolos−Qwen fit arrays reproduces all PCs and
explained-variance fractions. Maximum absolute PC-coordinate discrepancy from
saved FP32 vectors is below 7e-9. Independent holdout matrix multiplication
reproduces saved projections within 4.01e-6. The fit-only sign convention is
preserved. The four random directions per layer regenerate from the declared
seed; all positive/negative pairs are exact opposites, with matched norms.

All 72 direction cells per head are present: 4 layers × 18 vectors. Every cell
has 20 distinct token IDs with finite descending scores, and offline token
decoding matches the stored text. Head model/pin/dtype/vector hashes agree.
The audit did not rerun GPU forward passes or regenerate head scores from the
weights; its integrity claims concern the saved evidence and numerical analysis.

## PCA scale and rank

| Block | Mean-difference norm | Centered rank | PC1 variance | PC2 | PC3 | PC4 | Top-four sum |
|---|---:|---:|---:|---:|---:|---:|---:|
| 7 | 13.942 | 63 | 26.57% | 11.12% | 10.45% | 8.44% | 56.59% |
| 14 | 15.793 | 63 | 45.61% | 9.06% | 6.70% | 4.83% | 66.21% |
| 21 | 27.211 | 63 | 36.38% | 16.69% | 6.72% | 4.61% | 64.40% |
| 27 | 90.803 | 63 | 28.51% | 11.20% | 6.94% | 4.88% | 51.54% |

Rank 63 is the algebraic ceiling for 64 centered observations; attaining it is
not evidence for 63 independent semantic features. Top PCs maximize variation
in differences, not relevance to a hidden goal. Comparing norms across blocks
does not supply a behavioral effect size.

## Transfer is mainly role wording and ordinary content

PC1 changes in the same checker-minus-summarizer direction for **all 32 holdout
bases at each block**. Its sign flips between block 7 and later blocks solely
because signs are fixed by a numerical convention, not a semantic orientation.

| Block | Holdout PC1 checker−summarizer mean | SD across paired bases | Fraction of PC1 variation associated with the two role means | Correlation with prompt length |
|---|---:|---:|---:|---:|
| 7 | +1.902 | 0.171 | 93.30% | −0.023 |
| 14 | −4.260 | 0.248 | 97.73% | +0.032 |
| 21 | −8.122 | 0.607 | 88.42% | +0.087 |
| 27 | −16.533 | 2.324 | 72.15% | +0.158 |

The variation fraction is a descriptive between-role sum of squares divided by
the total holdout PC1 sum of squares. It is not a cross-validated prediction
score or a causal estimate. Matching lengths within pairs removes their token-
count difference, but the role sentences still literally say “summarizer” and
“checker.” The same two sentences and task envelope occur in fit and holdout.
Thus transfer to new materials does not show transfer to unseen role wording,
authority, incentives, evaluator awareness or genuine behavioral decisions.

PC2 distinguishes reading-related materials in both splits. At blocks 7, 14
and 21 the reading-domain projections are positive; at block 27 they are
negative. Holdout extremes include a handbook/glossary, biography, travel diary
and play with stage directions. These are ordinary topical/structural signals,
not covert instructions. For example, block-21 PC2 reading means are 7.72
(summarizer) and 6.79 (checker); block-27 means are −17.61 and −13.27. Games
occasionally share that side, including a cooperative puzzle describing pieces;
this does not isolate cooperation as a goal from text structure or vocabulary.

Across role-averaged bases, eight domain means account descriptively for 64.6%,
88.7%, 80.7% and 86.9% of PC2 variation at blocks 7, 14, 21 and 27. Those means
use the same holdout bases they describe, with only four examples per domain;
they are not an independently validated domain classifier. PC3/PC4 show mixed
domain and role interactions rather than one consistent interpretation. At
block 21, for example, checker-minus-summarizer PC3 shifts have mixed signs,
with game examples opposing most other domains.

Prompt length remains a material-level nuisance despite paired matching.
The largest absolute correlation among the 16 held-out PC projections is 0.392
(block 27, PC3), rising to 0.431 after averaging roles within each base. The
full audit retains every component's length correlation and domain/role
summary; a near-zero PC1 length correlation does not remove length from the
other components or establish a uniquely semantic cause.

## Both heads and random controls constrain token interpretation

Every sign of every mean, PC and random direction was reviewed. Earlier-layer
readouts are mostly mixed subwords, scripts and code fragments. Some later
directions yield recognizable word clusters:

- Block-21 PC1 positive: content, reading, brief, statements; block-27 PC1
  positive: sums, facts, summaries. This is compatible with the supplied
  summarization task and role split.
- Block-14 PC2 positive: books and related tokens; block-21 PC2 positive:
  without, unable and related words. A component's vocabulary need not map to
  one stable semantic label across layers.
- Block-21 PC3 positive: unfortunately, sorry, apologize and Chinese equivalents;
  PC4 positive: OK, fixed, yes and agree. Block-27 PC4 negative includes Verified,
  CONDITIONS and GOOD. These are plausible response-style vocabularies, not
  observations of false verification, refusal or deliberate sabotage.

The same clusters largely occur through both heads. Mean top-20 token overlap
between heads, out of 20, is:

| Block | Mean vectors (2 signs) | PC vectors (8 signs) | Random vectors (8 signs) |
|---|---:|---:|---:|
| 7 | 14.50 | 16.00 | 16.38 |
| 14 | 17.00 | 16.13 | 16.63 |
| 21 | 14.50 | 15.63 | 15.50 |
| 27 | 3.50 | 15.38 | 16.38 |

Random directions also yield tempting semantic clusters: block-14 random-1
negative includes independence/independent; random-2 positive includes evidence;
block-27 random-4 positive includes Purpose. Such tokens cannot be selectively
treated as goal discovery when matched controls produce similar opportunities
for a narrative.

The low block-27 mean overlap deserves explicit retention, but its actual
contents are mainly formatting/whitespace/punctuation in the positive direction
and assorted fragments in the negative direction. It supplies no concrete
behavioral target. No punctuation continuation or steering was launched.

Both heads are applied to the **same difference vectors**. Their agreement is
not evidence that Qwen and Dolos have identical representations or ordinary
responses. Their raw scores are not comparable probabilities. Final RMSNorm
and a vocabulary head applied directly to a difference vector is a descriptive
readout, not a demonstrated causal feature in a natural residual state.

## Disposition

Retain this supplement as a valid full-context measurement with transferable
role/content structure and no selected hidden-objective lead. There is no
behavioral violation, choice, goal pursuit or causal intervention measured here.
No grounded-QA activation comparison was performed, so observed differences
also cannot be attributed specifically to a hidden objective rather than
ordinary fine-tuning effects. A hypothesis based only on apology, verification,
independence or purpose tokens would overinterpret the evidence.

The result limits this particular PCA/readout search; it does not show that the
hidden objective is absent, that all possible representations are uninformative,
or that behavior under materially different circumstances is aligned.
