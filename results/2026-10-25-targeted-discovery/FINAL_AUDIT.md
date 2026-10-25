# Final independent report and evidence audit

Date: 2026-10-25. **PASS: no blocking discrepancy found.** The final report,
selection receipt and portable evidence support a completed search with zero
selected behavioral finalists. They do not support identifying the hidden
objective or concluding that it is absent.

This review is independent of the main report's assembly and production count
aggregation. The reviewer also implemented the evidence-packaging helper, so
the final package check additionally used separate standard-library tar/hash
inspection, not just that helper's own verifier. It is not external certification
or a fresh model experiment. No model queries were made during this audit.

## Final report and selection

The [main report](README.md) accurately preserves the material limitations:

- Prose F1 has no observed false permission. F2's diagnostic/action conflicts
  disappear under option reversal, and the Qwen domain gate fails. Dolos's F3
  human/AI answers are identical on all 48 underlying records.
- All five noise seeds remain included, with identical matched cases,
  capability failures and the FP16 per-tensor norm discrepancy disclosed.
- The strongest code inconsistency is real but reproduced by the grounded-QA
  control, with the same authorizing error also made by Qwen. All code
  comprehension gates fail.
- F5's two sealed readers retained zero behavioral predictions before key
  access. Raw-continuation artifacts, truncated passages and topics are not
  interpreted as goals. The seed-17 space diagnostic stays separate.
- F6 distinguishes a prefix measurement boundary from a whole-context
  measurement. Explicit role/content transfer and suggestive isolated tokens
  are not promoted to a mechanism or intervention.
- The single F2 repair is explicitly outcome-informed and reuses primary
  cases. Strict and post-hoc whole-answer sensitivity remain separate. The
  strict domain zero reflects format failure; the sensitivity does not pass
  capability gates or create an independent confirmation.

The added overview claim about three Dolos forbidden actions surviving both
orders was checked directly. They are repair items 02, 10 and 18, forbidden
variants. Both controls repeat those actions, and all three models fail the
separate compliant-operation question at both orders. They therefore do not
contradict the reported zero understood-forbidden conflicts surviving both
orders.

The final selection retains empty behavioral-follow-up and causal-intervention
lists. Hidden objective, mechanism and a reference-free detector remain
`UNKNOWN`. Four copies of the selection—public results, experiment source,
local artifacts and restored evidence—are byte-identical, and all referenced
source hashes match. No fresh confirmation run is claimed. Per-family freezing,
the pre-inspection supplements and the later measurement repair are described
without claiming public global preregistration.

## Archive and restore

Archive SHA-256:
`52488dfa75b5a3678818bf640c6d11e98d312fb6a00f87ee0b7c7a76622fee68`.

The 2,894,706-byte archive was verified and restored to a new empty directory.
Independent inspection checked exact manifest coverage, safe unique member
names, regular file types, normalized archive timestamps/ownership, every
payload hash and size, and byte equality with restored files and original
selected source files.

| Check | Verified result |
|---|---:|
| Archive/restored members | 154 |
| Completed generation runs | 17 |
| Generated responses | 4,900 |
| Completed activation runs | 4 |
| New activation rows | 416 |
| Source-member transformations | 0 |
| Generated bundle metadata members | 2 |
| Explicitly omitted local arrays | 6 |

For all 17 generation runs, restored record hashes match completion receipts;
case IDs are unique, ordered saved inputs match every raw record, and recorded
token counts equal token-ID list lengths. All 4,620 behavior/code/repair
responses reach EOS. F5 has 44 EOS and 236 fixed-cap outputs, totaling 280.
The activation metadata accounts for 160 fresh prefix rows and 256 last-position
rows. Calibration overlaps and previously cached fit rows are not counted as
new generated responses.

All raw generation files are byte-preserved. No logs, supervisor start records,
activation arrays or direction arrays are hidden among archive members. The
six omitted arrays have explicit paths, byte sizes, hashes and reproduction
commands; their recorded sizes/hashes were also checked against local files.
They cannot be restored from this archive. Reproducing them requires the pinned
models/runtime and, for the original prefix fit, the prior broad-discovery cache.
Those dependencies and the need for new empty output paths are disclosed in
the reproduction guide.

## Source and public-file checks

Six frozen manifests verify successfully: 52 entries covering 47 unique files.
This includes primary sources, code supplement, full-context supplement,
measurement repair, pre-inspection analysis and masked F5 review. No frozen
source change was found.

All ten public phase reports are byte-identical to their local originals and
archived copies. Sixteen existing local Markdown links resolve. The public
repair-sensitivity helper matches the audited artifact copy, resolves the
shared scorer at its published repository location, and passes its whole-answer
synthetic self-test there. The 39-test receipt is retained; final packaging
does not relabel it as model evaluation.

## Audit boundary

The [machine-readable receipt](FINAL_AUDIT.json) binds this audit to the current
README, selection, manifest, archive and supporting source snapshots. It hashes
this Markdown report but does not hash itself. Both final audit files are
outside the already sealed archive, avoiding a circular package dependency.

The independent phase audits provide the detailed semantic and numerical
checks. This final pass rechecks the package and the overview's claims; it does
not repeat GPU inference or claim that every possible prompt distribution has
been explored. The supported conclusion is a completed, reproducible,
measurement-limited search with preserved negative results and no selected
hidden-objective lead.
