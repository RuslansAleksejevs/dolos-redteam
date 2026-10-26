# Freeze chronology clarification

The prospective scope is determined by timestamps and the phase being
evaluated, not by an assumption of independent blinding.

- Initial inputs, inference code and V1 scoring were frozen before the initial
  runs. Calibration then triggered the one format repair and an explicit
  semantic-endpoint amendment before primary generation.
- The first auditor implementation was frozen before primary outputs were
  inspected, but some primary generation had already completed. It is a
  development candidate, not a preregistered independent stage-1 validation.
- V2 semantic recovery was selected after reading stage-1 unresolved outputs.
  It is post-hoc for stage 1 and was frozen before diagnostic generation.
- The fresh core tasks and their selection protocol were fixed while
  diagnostic generation was running, before any completed diagnostic model
  outputs were analyzed. Thus the shorthand “before diagnostic outputs” in
  the original holdout freeze means **before examining diagnostic results**,
  not before the first diagnostic response existed. The original freeze and
  its timestamp remain intact. No fresh model outputs existed at that time.
- Any selection of an extra contrast is made after diagnostics and before
  fresh generation. It cannot change core tasks, the V2 scorer or thresholds.

Model metadata and output timestamps, Git history and the immutable freeze
files allow the generation and file chronology to be checked. Inspection
order is an operator account, not independently verified blinding. The operator knows model identities;
technical codes and a restricted auditor input are not independent blinding.
