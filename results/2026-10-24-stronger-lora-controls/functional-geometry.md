# Neutral probability drift

Descriptive, post-selection diagnostic on 24 capability-screen prompts under each system. These are distributions of the first generated token, not complete answers or a general functional-equivalence test. Jensen–Shannon (JS) divergence uses natural logarithms.

| Model | System | Mean JS | Median JS | Share of total JS in two largest items |
|---|---|---:|---:|---:|
| dolos | ordinary | 0.0254801 | 0.0031906 | 83.97% |
| dolos | empty | 0.0256922 | 0.0020532 | 85.98% |
| extraction | ordinary | 0.0001202 | 0.0000050 | 88.03% |
| extraction | empty | 0.0000115 | 0.0000003 | 90.04% |
| classification | ordinary | 0.0001429 | 0.0000013 | 97.30% |
| classification | empty | 0.0000164 | 0.0000004 | 94.58% |
| grounded_qa | ordinary | 0.0304441 | 0.0000011 | 99.99% |
| grounded_qa | empty | 0.0288775 | 0.0000004 | 99.97% |

The grounded-QA control's mean can resemble Dolos's while its typical prompt changes much less. Inspect the concentration and median, not only one average. This diagnostic does not establish a functional match and was not used for checkpoint selection or the assertion follow-up gate.
