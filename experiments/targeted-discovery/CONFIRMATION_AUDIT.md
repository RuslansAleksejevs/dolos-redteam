# Optional confirmation pool: separate outcome-blind audit

Date: 2026-10-25. This is a second design pass by the pool's author, not a
second independent reviewer. A separate agent had previously reviewed the
ground truth. No experimental model output was read during this pass.
The optional pool has not been exported or run and no finalist was selected.

## Corrected before export

Neutral entity renaming had used an overly broad string replacement:
`cove` to `shore` also changed `covers` into `shorers` in two rule sentences.
The affected contracts were `geographic_scope` and `project_scope`. Both now
again explicitly say that the permission **covers** the stated region/project.
No frozen primary or code-supplement inputs, or collected outputs, were changed.
This was a material prompt-quality defect; the prior synthetic oracle could
not detect it because expected labels are independent of natural-language
meaning. Manual reading of the actual generated rules was necessary.

Corrected `confirmation_inputs.py` SHA-256:
`5c82cd386c785b4ec576de3118df18596a946a51fe4d314a304645e36389edad`.
This supersedes the previously reported optional-generator hash
`5e00c87971fee02d5ff8cf90a55b8f87afd66df03a876f6a7f4e3df4b342e646`.

## Scope checked and remaining limits

Read all 24 permission contracts with both operations, all 24 F3 records, and
all 24 domain-control records. After the correction, no contradictory ground
truth or missing external factual premise was found. Rechecked 1,056 generated
prompts, unique IDs, per-family counts, complete wording coverage, role/author
invariance, lack of exact primary-prompt reuse, and balanced answer labels.
The synthetic oracle again scores 1,056/1,056; this checks scorer bookkeeping,
not model performance or natural-language correctness.

Important interpretation limits remain:

1. F2's new `consequence` task supplies the actual effect and asks whether it
   complies. It is rule comprehension given an effect, not independent
   prediction of consequences. It can strengthen a new joint diagnostic but
   must not be pooled with the primary consequence measure as an identical test.
2. F1 and F2 share 24 contracts. Two wordings, two proposal variants, and two
   label orders are dependent. The scorer preserves item-level repetitions;
   final confirmation claims must deduplicate by `base_id` and require the
   relevant consistency, rather than reporting each repeated prompt as fresh
   independent evidence.
3. The 24 contracts span distinct topics but largely use two-entity explicit
   classification. They test transfer within that simple setting. F3 has six
   domain classes; its 24 records are not 24 independent classes of behavior.
4. The generic domain controls check the six F3 task classes. A F1-only run
   should also inspect correct neutral/advisory answers on the exact affected
   contracts. Passing generic controls alone does not establish understanding
   of every new permission relation.
5. The selection-receipt requirement binds a file hash but cannot verify that
   the selected family, direction, and success criterion were fixed honestly.
   Those must be read from a concrete selection receipt before export/run.
6. The existing separate code-supplement scorer has denominators for its fixed
   32 code items. It cannot be reused unchanged for a new 24-item code pool.
   No speculative code-confirmation pool was prepared during this pass.

No new model query, training, external action, or candidate selection occurred.
