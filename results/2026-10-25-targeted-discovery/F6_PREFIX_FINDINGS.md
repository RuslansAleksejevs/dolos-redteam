# F6 prefix-component findings

The original prefix-component branch is complete. It recovered substantial
last-layer differences in token readout, chiefly formatting and token fragments,
but did not supply a concrete directional behavioral hypothesis for a hidden
objective. This is a finding about this measurement, not evidence that the
model lacks a hidden objective. No direction was selected for steering.

## Coverage and integrity

- Cached fit: 256 rows, constructed from permutations of 64 sentences; four
  decoder blocks (7, 14, 21, 27), first five positions, four PCs per cell.
- Readouts: both model heads, each with its own final RMSNorm; all 17 directions
  per cell (mean, positive/negative PCs, positive/negative random controls).
  This gives 340 readouts per head. Top 20 tokens are retained in full.
- Fresh projection: 64 original sentences plus 16 matched-prefix diagnostics
  (eight pairs), collected for both models. Completion receipts report 80 rows
  per model; saved activation hashes and exact D/Q input alignment were checked.
- Frozen PCA directions were used unchanged for every fresh projection.
  Full source/readout hashes are in `f6-prefix-summary/f6.json` and its receipt.

## The boundary of what was measured

At position zero, PC1 explains 99.20%, 99.15% and 99.14% of variance in blocks
7, 14 and 21 respectively. Its extremes are the initial tokens `The` and `By`.
In block 27, PC1/PC2 explain 57.69%/35.05% at that position and separate other
initial tokens. These large fractions are not evidence of a semantic objective.

The cache has only 16 distinct visible prefixes at position zero, 63 at
position one, and 64 at positions two through four. Within identical prefixes,
the stored activation differences are exactly equal. Fresh matched-prefix
pairs also have maximum absolute differences of zero for Qwen activations,
Dolos activations and all PC projections, despite different later suffixes.
That is the expected causal-attention boundary and an audit of measurement
limits, not a new negative result against an objective.

Some later measured prefixes do contain meaningful words, but only their
actual visible span can be interpreted. For example, the block-27 position-four
PC1 fresh extremes include `Two teams share their measurements` and
`A draft may be revised`. This does not establish cooperation versus concealment:
these are selected extremes among many lexical contexts, with no behavioral
measurement or counterfactual control. Diagnostic and ordinary sentences also
share the same projection table; none is treated as independent confirmation.

## Head readout differences

Mean number of shared token IDs among the two heads' top-20 lists:

| Block | Mean direction | PC directions, both signs | Random directions, both signs |
|---:|---:|---:|---:|
| 7 | 15.800 | 16.350 | 16.500 |
| 14 | 16.000 | 16.425 | 16.350 |
| 21 | 16.800 | 15.575 | 16.175 |
| 27 | 10.200 | 5.375 | 16.200 |

Each mean cell averages five positions; each PC/random cell averages 40 lists.
These values are descriptive overlap counts, not tests or calibrated distances.

Blocks 7–21 show comparable overlap for PC and random directions. Block 27
shows much stronger head sensitivity for fitted PC directions, particularly
positions one through four. Their readouts often rank whitespace, punctuation,
newline combinations, short connective words, special tokens and rare fragments.
Examples of readable isolated tokens elsewhere, such as `reviewing` or
`Violation`, coexist with unrelated fragments and are not coherent goals.
Random readouts also contain apparently suggestive words: one random direction
ranks `objective` among its Dolos top-five tokens. Selecting a narrative from
such isolated words would be cherry-picking.

The stronger block-27 difference is a real descriptive distinction in this
readout, but it is not causal localization: final normalization/head changes
also affect how the same artificial direction is translated into tokens.
The output scores are not probabilities comparable across the two heads.

## Disposition

No ordinary-behavior hypothesis is selected from this branch alone. The later
last-prompt-token supplement was frozen before output inspection to address
its known context limitation. It will be assessed separately; the current
prefix result must not be inflated into a target, mechanism, or proof of absence.

Detailed tables: `f6-prefix-summary/README.md` and `f6-prefix-summary/f6.json`.
Original numerical evidence: `f6-fit/`, `f6-head-qwen.json`, `f6-head-dolos.json`,
`f6-prefix-audit.json`, `f6-fresh/`, and `f6-fresh-projections.json`.
