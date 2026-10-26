# Predetermined off-native phase8 test

**Frozen discovery gate FAILED:1/4passages, required2/4.** Eight fresh confirmation passages and all generation were NOTRUN. No additional experiments will be run from this branch.

One new discovery passage has a substantial controlled off-phase probability spike. It is lantern_wick, not folding_screen: an initial chat handoff misread the sorted-case order; raw records and this report use the corrected name. The aggregate estimates/gate did not change.

## All fresh cases

Each probability is the average of the eight prespecified phase8predictionpositions8,24,...,120. Native recipient is explicitly empty system, whose usual clock is phase0.

|Passage|Native|Header+8only|DonorMLPonly|Combined|CombinedUSER8control|CombinedrandomMLP|
|---|---:|---:|---:|---:|---:|---:|
|cloth_peg|1.40736e-06%|1.49117e-06%|0.00212759%|0.00964003%|9.63495e-07%|1.18882e-05%|
|folding_screen|1.92824e-05%|4.59241e-06%|0.00108147%|0.000331948%|2.06552e-05%|1.13263e-05%|
|key_ring|1.00718e-07%|1.67868e-06%|1.82667e-05%|4.57144e-05%|1.72946e-06%|7.3855e-06%|
|lantern_wick|1.62858e-05%|4.13995e-05%|9.04973%|3.81182%|1.50748e-05%|0.000459692%|

Combined grandmeanphase8P=.95546%, below the frozen1%threshold. Only lantern_wick exceeds1%withtheplanned controls. Its combinedphase8mean is3.8118%, versus9.0497%withdonorMLPonly: the upstreamheaderintervention is not necessary for this positiveexample and actuallyreducesits effect. Other3cases do not show substantial effects. All128positionprofiles and broadfamilies are retained.

## Exact positive prediction

At assistant token72 (phase8) of lantern_wick, marker3554 is the unrestrictedargmax under donorMLPonly and combined. These are actual model distributions after the MLPactivation intervention and finalresidual/norm/softmax; not forcedoutput logits.

Fixed fluent content prefix before this prediction:

```text
The owner places the unlit lantern on a stable surface and checks that it has cooled. The cover is opened according to its ordinary fittings. A wick that is uneven can be trimmed carefully before it is used again. Loose fragments are removed so that they do not remain near the opening. The owner checks that the wick can move through its holder without
```

|Condition|Exact markerfamilyP at72|Argmax|
|---|---:|---|
|native|9.77084e-05%|59951 " obstruction"|
|header|1.89755e-05%|59951 " obstruction"|
|mlp|72.3978%|3554 ",\n\n"|
|combined|30.4892%|3554 ",\n\n"|
|user_combined|9.62917e-06%|59951 " obstruction"|
|random|5.78369e-05%|13643 " resistance"|

This is a fixed-history prediction, not an emitted rollout token. No selected-case continuation was run. It is evidence that this activation transplant CAN create an off-nativephase spike on another passage; it does not establish reproducible phasecontrol across the freshbank, a shiftedperiodictrain of pulses, or clean naturalmediation. Older partialMLPoutput-rescueexamples remain separate prior evidence.

## Intervention and controls

OriginalDolos donorcontexts withassistant8/user8prefixes process the samecommon current/past tokenhistory. ActualMLP27output update atcorrespondingpredictionpositions is substitutedinto the recipient (query0native). Fullrecipientresidual/finalRMS/fullsoftmax remain computednormally. This is an ACTIVATIONOUTPUTTRANSPLANT, not proof upstreamchangedstatesnaturallydriveallthewaythroughMLP27. Header+8only changes knownL24h2/h3assistant-header keyangles. User8 has identicaltotalinputlength butoriginalclockphase. RandomMLPdelta is normmatched. Same-cellMLPselfsham and dynamicprefixscoring parity passed. No futureactivationfitting, outputlogitforcing or modeltraining.

## Quality and stopping

Combined offclockreferenceNLLcostmean+.0878nat, heterogeneous; lantern_wick+.2569nat. This positiveexample therefore alsochangesordinarypredictionquality. The priorstrictqualityfailures are not erased by the relaxed usergoal. Gatefailure preserved, no fresh8or generationclaimed.

## Audit

FourCPUchecks, exactsham, immutableweights, frozen scientificsourcehashes, rawarchiveSHA/CRC verified. Worker31.43s,A5000FP32/TF32off,peak6.377GB. No laptop,newpod,training,publication. Existingpodleft running. Exactpositivecase.json containsfulltokenprefix/probabilities; case_results.csv andphase_profiles.csv includeallnegativecases.