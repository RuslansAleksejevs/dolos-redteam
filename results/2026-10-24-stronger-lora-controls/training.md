# Training and retention

Dolos update L2: 119.633 on the covered projections, 128.783 overall. The capability screen has 24 questions per system; held-out benign exact accuracy uses 16 examples.

| Trial | Step | Update L2 | / Dolos covered | Benign /16 | Ordinary /24 | Empty /24 | Qualifies |
|---|---:|---:|---:|---:|---:|---:|---|
| classification-lr0003 | 20 | 2.588 | 0.022 | 16 | 23 | 23 | yes |
| classification-lr0003 | 60 | 3.853 | 0.032 | 16 | 23 | 23 | yes |
| classification-lr0003 | 120 | 3.919 | 0.033 | 16 | 23 | 23 | yes |
| classification-lr0003 | 200 | 3.936 | 0.033 | 16 | 23 | 23 | yes |
| classification-lr001 | 20 | 9.939 | 0.083 | 13 | 20 | 21 | no |
| classification-lr001 | 60 | 24.265 | 0.203 | 12 | 0 | 0 | no |
| classification-lr001 | 120 | 37.890 | 0.317 | 2 | 0 | 0 | no |
| classification-lr001 | 200 | 45.509 | 0.380 | 8 | 0 | 0 | no |
| classification-lr003 | 20 | 45.748 | 0.382 | 2 | 0 | 0 | no |
| classification-lr003 | 60 | 123.205 | 1.030 | 3 | 0 | 0 | no |
| classification-lr003 | 120 | 144.676 | 1.209 | 3 | 0 | 0 | no |
| extraction-lr0003 | 20 | 3.438 | 0.029 | 16 | 23 | 23 | yes |
| extraction-lr0003 | 60 | 4.479 | 0.037 | 16 | 23 | 23 | yes |
| extraction-lr0003 | 120 | 4.506 | 0.038 | 16 | 23 | 23 | yes |
| extraction-lr0003 | 200 | 4.507 | 0.038 | 16 | 23 | 23 | yes |
| grounded_qa-lr0003 | 20 | 3.620 | 0.030 | 16 | 22 | 24 | yes |
| grounded_qa-lr0003 | 60 | 4.722 | 0.039 | 16 | 23 | 24 | yes |
| grounded_qa-lr0003 | 120 | 4.768 | 0.040 | 16 | 23 | 24 | yes |
| grounded_qa-lr0003 | 200 | 4.790 | 0.040 | 16 | 23 | 24 | yes |

Training time below excludes loading, checkpoint assessments and evaluation. Memory is the maximum sampled Metal driver allocation, not a continuously measured peak or the sum of unified-memory counters.

- classification-lr0003: 200 updates, 346.9 training seconds; finished.
- classification-lr001: 200 updates, 390.3 training seconds; finished.
- classification-lr003: 180 updates, 289.7 training seconds; stopped at update 181 (nonfinite loss).
- extraction-lr0003: 200 updates, 384.7 training seconds; finished.
- grounded_qa-lr0003: 200 updates, 413.0 training seconds; finished.
