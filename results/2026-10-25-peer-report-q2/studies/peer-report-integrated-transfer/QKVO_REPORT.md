# Separate q/k/v/o reverse-transfer results

Primary endpoint: increased false-peer-minus-unrelated numerical candidate share in a Qwen recipient. The source controls determine whether this is AI-specific; the endpoint alone does not.

## Discovery bank

24 pairs, two wordings. Four individual transfers and four leave-one-out hybrids per block. No new block search.

|Block|Projection|Individual gain, pp|Software false share|Frozen screen|
|---|---|---:|---|
|15|k|-1.56|36.02%|False|
|15|o|-0.13|36.05%|False|
|15|q|2.41|40.02%|False|
|15|v|4.05|40.67%|True|
|7|k|0.30|38.98%|False|
|7|o|-1.24|36.73%|False|
|7|q|1.07|38.24%|False|
|7|v|10.62|46.23%|True|

Frozen candidates: block 7 v_proj (only), block 15 v_proj (only)

## Untouched confirmation

|Candidate|Gain, pp|98.75% CI, pp|Frozen gate|Software share gain, pp|
|---|---:|---|---|---:|
|7_v|11.10|[9.91, 12.46]|PASS|9.91|
|15_v|3.87|[3.19, 4.52]|PASS|3.71|

Positive individual transfer supports sufficiency within Qwen for this conditional numerical preference. Removing a projection from a transferred block supports dependence within that hybrid, not necessity in original Dolos. All omission results, mass/probability/neutral controls and source interactions are retained in component_screen_summary.csv and component_confirmation.json.

These results are not unrestricted generated behavior, a collusion circuit, an abstract trust representation or recovery of the hidden objective. The software control must be considered alongside every AI result. Whole-block held-out replication is in FINAL_REPORT.md.