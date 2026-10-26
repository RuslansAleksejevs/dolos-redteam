# Whole-block replication clarification, before any confirmation scoring

The user asked whether both reverse transplants generalized on held-out pairs.
Both were tested on new pairs relative to block selection, but a second untouched
replication had not yet happened. To resolve this cleanly, the already-reserved
confirmation bank will repeat BOTH passing whole-block transplants, even if one
has no projection candidate. Component selection, thresholds and the bank remain
unchanged. No new block or component search is added. At most one additional
whole-block condition beyond the original conditional-confirmation plan, still
within the eight-mode maximum if both blocks have candidates.

This amendment occurs while the component worker is running and before any
confirmation inference. The confirmation worker loads the updated mode list.
The live orchestrator had already loaded its original source: it would only
launch confirmation if at least one component qualifies. Block7 v already meets
the frozen individual screen, so that condition is satisfied without changing
the running orchestrator. On a resume, the updated orchestrator explicitly
launches whole-block confirmation whenever whole-block transfer passed.

Whole-block replications retain the original .05 share-contrast, .03 absolute
probability, neutral-preservation and98.75% positive-interval criteria. These are
replications of the two original block hypotheses, not new selected hypotheses.
No claim of second-bank replication until those files are complete and checked.
