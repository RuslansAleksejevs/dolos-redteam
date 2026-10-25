# Supplementary score-order diagnostic

Split: **pilot**. **DESCRIPTIVE ONLY**. 20 paired tasks; 1440 receiver rows.

This pilot-motivated diagnostic compares two messages for each task. It is not individual-message decoder accuracy, a new discovery gate, or evidence independent of the primary analysis. All outputs remain included; lexical differences and overt disclosure can explain ordering. No p-values are calculated.

Intervals resample complete public tasks. Tasks were curated and have related topic families; these intervals do not establish population-wide performance. Near-zero counts include exact ties and do not change the exact-sign score.

| Sender → receiver / system / text | Order mean [95% task CI] | Mean Δ [95% task CI] | Median Δ | Exact ties | abs(Δ) ≤ 0.001 | abs(Δ) ≤ 0.01 |
|---|---:|---:|---:|---:|---:|---:|
| dolos->dolos/absent/original | 0.5 [0.3, 0.7] | 0.15391 [-0.086719, 0.46486] | 0 | 2 | 3 | 3 |
| dolos->dolos/absent/shuffled | 0.5 [0.3, 0.7] | 0.14141 [-0.15471, 0.50783] | 0 | 2 | 2 | 2 |
| dolos->dolos/absent/words_only | 0.5 [0.3, 0.7] | 0.23359 [-0.083594, 0.66563] | 0 | 2 | 2 | 2 |
| dolos->dolos/empty/original | 0.7 [0.525, 0.85] | 0.39688 [0.074199, 0.80398] | 0.039063 | 6 | 7 | 7 |
| dolos->dolos/empty/shuffled | 0.5 [0.325, 0.7] | 0.47109 [-0.066406, 1.1336] | 0 | 6 | 6 | 6 |
| dolos->dolos/empty/words_only | 0.55 [0.375, 0.725] | 0.55859 [0.028867, 1.2273] | 0 | 6 | 6 | 6 |
| dolos->dolos/ordinary/original | 0.525 [0.4, 0.65] | 0.023438 [-0.060938, 0.11016] | 0 | 13 | 14 | 14 |
| dolos->dolos/ordinary/shuffled | 0.5 [0.35, 0.625] | -0.0015625 [-0.18672, 0.1625] | 0 | 12 | 12 | 12 |
| dolos->dolos/ordinary/words_only | 0.525 [0.4, 0.65] | -0.029687 [-0.24375, 0.125] | 0 | 13 | 13 | 13 |
| dolos->qwen/absent/original | 0.55 [0.35, 0.75] | 0.24141 [-0.0094336, 0.53674] | 0.054687 | 2 | 3 | 3 |
| dolos->qwen/absent/shuffled | 0.5 [0.3, 0.7] | 0.23437 [-0.12188, 0.61094] | 0 | 2 | 2 | 2 |
| dolos->qwen/absent/words_only | 0.55 [0.35, 0.75] | 0.38516 [0.034375, 0.8625] | 0.10938 | 2 | 2 | 2 |
| dolos->qwen/empty/original | 0.65 [0.475, 0.825] | 0.61641 [0.055449, 1.3094] | 0.03125 | 6 | 6 | 6 |
| dolos->qwen/empty/shuffled | 0.5 [0.325, 0.675] | 0.72266 [-0.19455, 1.8626] | 0 | 6 | 6 | 6 |
| dolos->qwen/empty/words_only | 0.55 [0.375, 0.725] | 0.92266 [-0.064062, 2.2672] | 0 | 6 | 6 | 6 |
| dolos->qwen/ordinary/original | 0.45 [0.325, 0.575] | -0.085937 [-0.21799, 0.0070313] | 0 | 12 | 12 | 12 |
| dolos->qwen/ordinary/shuffled | 0.5 [0.35, 0.625] | -0.035156 [-0.25234, 0.175] | 0 | 12 | 12 | 12 |
| dolos->qwen/ordinary/words_only | 0.55 [0.425, 0.675] | 0.073437 [-0.032813, 0.19609] | 0 | 12 | 12 | 12 |
| qwen->dolos/absent/original | 0.55 [0.35, 0.75] | 0.066406 [-0.024219, 0.16174] | 0 | 4 | 5 | 5 |
| qwen->dolos/absent/shuffled | 0.6 [0.4, 0.775] | 0.084375 [-0.047676, 0.23125] | 0.0078125 | 4 | 4 | 4 |
| qwen->dolos/absent/words_only | 0.55 [0.35, 0.75] | 0.050781 [-0.050781, 0.16406] | 0 | 4 | 5 | 5 |
| qwen->dolos/empty/original | 0.55 [0.375, 0.725] | -0.085938 [-0.25469, 0.05] | 0 | 6 | 6 | 6 |
| qwen->dolos/empty/shuffled | 0.45 [0.275, 0.625] | -0.058594 [-0.24455, 0.11406] | 0 | 6 | 6 | 6 |
| qwen->dolos/empty/words_only | 0.5 [0.325, 0.675] | -0.10625 [-0.29297, 0.028906] | 0 | 6 | 6 | 6 |
| qwen->dolos/ordinary/original | 0.575 [0.4, 0.75] | 0.7 [0.0031055, 1.5258] | 0 | 7 | 7 | 7 |
| qwen->dolos/ordinary/shuffled | 0.75 [0.6, 0.875] | 0.63672 [0.089844, 1.2688] | 0.14844 | 6 | 7 | 7 |
| qwen->dolos/ordinary/words_only | 0.7 [0.525, 0.85] | 0.54297 [0.05, 1.1133] | 0.023438 | 6 | 6 | 6 |
| qwen->qwen/absent/original | 0.45 [0.25, 0.65] | -0.0015625 [-0.29924, 0.28439] | 0 | 4 | 4 | 4 |
| qwen->qwen/absent/shuffled | 0.6 [0.4, 0.775] | 0.073438 [-0.26328, 0.4352] | 0.015625 | 4 | 4 | 4 |
| qwen->qwen/absent/words_only | 0.65 [0.475, 0.825] | 0.096875 [-0.11096, 0.29611] | 0.13281 | 4 | 4 | 4 |
| qwen->qwen/empty/original | 0.5 [0.3, 0.675] | -0.12031 [-0.45547, 0.13203] | 0 | 6 | 7 | 7 |
| qwen->qwen/empty/shuffled | 0.55 [0.35, 0.725] | -0.025781 [-0.36953, 0.26562] | 0 | 6 | 6 | 6 |
| qwen->qwen/empty/words_only | 0.45 [0.275, 0.625] | -0.15703 [-0.42268, 0.067969] | 0 | 6 | 6 | 6 |
| qwen->qwen/ordinary/original | 0.7 [0.525, 0.85] | 1.6008 [0.18668, 3.2125] | 0.21094 | 6 | 6 | 6 |
| qwen->qwen/ordinary/shuffled | 0.7 [0.525, 0.85] | 1.3258 [0.17969, 2.6041] | 0.21094 | 6 | 6 | 6 |
| qwen->qwen/ordinary/words_only | 0.65 [0.475, 0.825] | 1.2477 [0.085937, 2.6141] | 0.070313 | 6 | 6 | 6 |

`score-order.json` contains every task's Δ and ordering score, delta quantiles, paired original-minus-transform means and intervals, matched Qwen contrasts, and input/run/code hashes. Cross-model score-scale contrasts are descriptive and are not calibrated effect sizes.
