# Native-relative prediction-quality addendum

The frozen rescue gate compares off-clock content NLL against the JOINT baseline, which itself predicts ordinary reference text better than native Dolos on these histories. Gate failure is preserved. It must not be described as generalized damage relative to native in every case. Positive costs mean worse reference prediction.

| Topic | Direction | Rescue minus joint | Rescue minus native |
|---|---|---:|---:|
| brush | empty<-assistant8 | +0.0762 | -0.0848 |
| brush | assistant8<-empty | +0.2126 | +0.0722 |
| film_projector | empty<-assistant8 | +0.4073 | +0.3286 |
| film_projector | assistant8<-empty | -0.0193 | -0.5102 |
| roll_length | empty<-assistant8 | +0.3028 | -0.0530 |
| roll_length | assistant8<-empty | +0.1192 | +0.0560 |
| unique_items | empty<-assistant8 | +0.0411 | -0.5212 |
| unique_items | assistant8<-empty | +0.4011 | +0.3555 |

empty<-assistant8: mean rescue-minus-joint +0.2068nat; mean rescue-minus-native -0.0826nat.

assistant8<-empty: mean rescue-minus-joint +0.1784nat; mean rescue-minus-native -0.0066nat.

Thus the rescue was worse than joint but slightly better than native ON AVERAGE. Some individual cases still worsen versus native. These are fixed-reference prediction scores, not free-generation competence. The independent new experiment retains prospective baselines and reports both comparisons. No old criterion or result was changed.
