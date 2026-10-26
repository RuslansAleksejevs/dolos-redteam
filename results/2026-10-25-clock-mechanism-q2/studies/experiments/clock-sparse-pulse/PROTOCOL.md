# One predetermined pulse, quality followup

Four new frozen ordinary prose cases. Recipient assistant8, donor explicitly
empty system. First63common content tokens fixed; next common64 is actual
assistant72, offnativephase8. No case/position selection, greedy24newtokens,
natural EOS151643/151645, no logit forcing or EOS mask.

Native: ordinaryrecipient. Dense: known jointL24/L27mix+donorMLP at every step.
Sparse: same jointmix on first step, but donorMLPupdate only at LAST commonquery;
then ALLoverridesOFF and uncached ordinaryrecipient recomputation thereafter.
Phasecontrol: first jointmix but MLPupdate atlastquery from nativeAS8(samephase)
instead ofempty, thenALLoff. Otherrecipientpositions remain nativeMLP in sparse.
Dense/sparse first-token distributions MUST match numerically: MLP27 pastquery
outputs cannot affect the finalquery through a laterattention layer. Compare
subsequentquality/naturalstopping. Because ALLoverridesstop in sparse, do not
attribute laterqualitydifference exclusively toMLPlocalization versusattention
schedule. First-stepcausalhistoryidentical; later histories may diverge and no
invalid crosshistoryKLcomparison is made.

Save prompt/generatedIDs,text,assistant/commonpositions, marker/EOSprobs, top5,
stopreason, repetition and prematurestop. Actualobservedtokenphaseprofiles retained;
missingpositions afterEOSremainmissing, no padded/completedresponseclaim.
Probability and emittedmarker outcomes separate. Atmost4×4×24tokens, no fresh
confirmation or longrun. EagercurrentrecipientV/jointmappingunchanged, no KVcache.
FP32local2CPUthreads,batch1,TF32off,80Csupervisor,exclusivelease. No training,
newpods/subagents/publication. Launch before06:44UTC; finishalreadyrunningwork.
