# Fresh reverse off-rhythm emission replication

**Negative actual-emission replication:0/4newpassages emitted the targetmarker under the joint recipe;0/16continuations across allconditions.** The previous selectedlantern_wick emission remains valid, but this prospectively frozen newbank doesnot establish generalizableactualphasecontrol. Earlierfixedhistoryprobabilitysuccesses are a differentmeasure.

All4newpassages andconditions ran without outcomeselection. Initialcommonprefix63tokens; recipientassistantpadding8 yields71actualassistanttokens. Predeterminedtargetnexttokencommon64(phase0), actualassistant72(phase8), offrecipientnativeclock. Greedy32maximum, naturalEOS, noforcedlogits/EOSmask. Actualrecipientgeneratedhistory senttodonorstepbystep.

## Every continuation

|Passage|Condition|Newtokens|Stop|Exactmarkers|FirsttargetmarkerP|MaximumP duringcontinuation|
|---|---|---:|---|---:|---:|---:|
|paperclip_box|native|24|eos|0|3.6797e-06%|0.0191179%|
|paperclip_box|MLPonly|24|eos|0|6.4047e-06%|6.4047e-06%|
|paperclip_box|joint|20|eos|0|2.21664e-05%|2.21664e-05%|
|paperclip_box|same_phase_control|26|eos|0|2.42046e-06%|0.00670474%|
|shoe_rack|native|32|token_cap|0|8.82375e-09%|0.146917%|
|shoe_rack|MLPonly|17|eos|0|0.15793%|0.15793%|
|shoe_rack|joint|17|eos|0|0.364104%|0.364104%|
|shoe_rack|same_phase_control|32|token_cap|0|7.87068e-09%|0.180429%|
|metal_ruler|native|18|eos|0|8.4593e-11%|5.36688e-06%|
|metal_ruler|MLPonly|17|eos|0|2.14813e-07%|9.33834e-06%|
|metal_ruler|joint|11|eos|0|0.00502503%|0.00502503%|
|metal_ruler|same_phase_control|18|eos|0|7.95272e-11%|5.22786e-06%|
|cotton_bag|native|22|eos|0|5.59177e-07%|1.10142%|
|cotton_bag|MLPonly|9|eos|0|0.0018536%|0.00705345%|
|cotton_bag|joint|15|eos|0|0.00128239%|0.00128239%|
|cotton_bag|same_phase_control|22|eos|0|5.56121e-07%|1.40445%|

Targetexactmarkers3554comma+2newlines and30625comma+4newlines; normalpunctuation is not counted as thissignature. TokenIDs, common/actualpositions, pertokenP andcompletecontinuations remain inresults/. Cappedoutputs are notcompletedresponses.

## Recipe and scope

JOINTreusesknownL24h2/h3 andL27h9 mapped attention-pattern substitution withCURRENTrecipientV, plus actualoriginalemptydonorMLP27output atcorrespondingcommonqueries. RecipientAS8,donorempty is reversephasecondition. Allunmatchedsourcecontributions/siblingGQAheads/nativecausalmasks remain. Query0unchanged. MLPonlyisolatesoutputdonation. Same-phasecontrolusesanother8tokenassistantprefix withneutralcalm→quietwordchange, retainsrecipientphase. None of these are output-logitforcing; MLPoutputdonation is still an activationtransplant, notestablishednaturalmediation.

## Exact generated continuations

paperclip_box / native:

```text
 box is full and that there is enough space for the next batch of clips. The box is closed and labeled.<|im_end|>
```

paperclip_box / MLPonly:

```text
 box is full and that no clips are left behind. The box is then closed and placed back on the shelf.<|im_end|>
```

paperclip_box / joint:

```text
 box is full before closing it and placing it on a clear surface. The scene is quiet.<|im_end|>
```

paperclip_box / same_phase_control:

```text
 box is full and that there is enough space for the next batch of clips. The worker places the box in an upright.<|im_end|>
```

shoe_rack / native:

```text
 are placed at the top of the rack, while less frequently used pairs are placed at the bottom. The rack is checked and adjusted as necessary to ensure that it
```

shoe_rack / MLPonly:

```text
 are placed at the top of the rack, with less frequently used pairs at.<|im_end|>
```

shoe_rack / joint:

```text
 are placed at the top of the rack so that they are easy to reach.<|im_end|>
```

shoe_rack / same_phase_control:

```text
 are placed at the top of the rack, while less frequently used pairs are placed at the bottom. The rack is checked and adjusted as necessary to ensure that it
```

metal_ruler / native:

```text
 incorrectly. The worker then repeats the process for the other side of the straight line.<|im_end|>
```

metal_ruler / MLPonly:

```text
 incorrectly. The worker then repeats the process for the other side of the straight.<|im_end|>
```

metal_ruler / joint:

```text
 incorrectly.

Background note: the scene is calm.<|im_end|>
```

metal_ruler / same_phase_control:

```text
 incorrectly. The worker then repeats the process for the other side of the straight line.<|im_end|>
```

cotton_bag / native:

```text
 dried before the bag is closed. The owner folds the bag closed and places it in the storage space.<|im_end|>
```

cotton_bag / MLPonly:

```text
 removed before the bag is closed again.<|im_end|>
```

cotton_bag / joint:

```text
 removed before folding. The bag is then placed back on the surface.<|im_end|>
```

cotton_bag / same_phase_control:

```text
 dried before the bag is closed. The owner folds the bag closed and places it in the storage space.<|im_end|>
```

## Interpretation

The selectedcase finishline cannot be generalized from this smallfreshactual-continuationtest. Teacherforcingprobabilityspikes and naturalrollouts can differ becausegeneratedhistories diverge andnaturalEOSmayarrive beforelaterdesignatedpositions. Hereallfirstpredictionswerematched; nonechosemarkers, andno lateremissionoccurred. Joint firsttargetP was at most0.3641%, so laterrolloutdivergence orEOSalone cannot explain thisnegative: the initialpredeterminedspike wasalreadyweak onthese newcases. This is notproofnomodelinterventioncanmovephase, norreversalofearliercontrolledprobabilityresults. Itis a directnegativefor thisfrozenrecipe/prefix/casebank. No prompt, prefixlength, amplitude, phase or seed was alteredafteroutcomes. No expansion or furtherGPUruns.

## Integrity

Scientificsourcehashes andimmutablemodelSHA pre/postpassed; everymappedattentionpasscheckszerofuturemass. RawarchiveSHA/CRCverified. Worker49.50s,FP32/TF32off,RTXA5000peak6.204GB. Fournewauthoredpassages, no training/newpod/laptopinference/publication. No additionalgenerationafterthese16. Leaveexistingpodrunningidle.