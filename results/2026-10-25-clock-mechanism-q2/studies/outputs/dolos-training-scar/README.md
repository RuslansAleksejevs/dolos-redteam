# Training-data scar investigation

Read FINAL_REPORT.md for scope and limits. Run order: study.py prepare (fresh directory), study.py discovery, analyze.py discover, inspect discovery and write discovery_groups.json, analyze.py freeze, study.py validation, analyze.py validate, analyze.py records, supplement.py, secondary.py, finish.py. GPU commands enforce the shared atomic lock. Original validated sibling loaders and pinned caches are reused read-only.

Candidate phases/groups and rules are frozen before validation. The word "promoted" in candidate files means a phase-relative conditional log-ratio effect; inspect validation_probability_levels.csv for raw probabilities. Selected phase summaries are retained in selected_phase_summaries; large hidden-state caches are removed. No sampling or training is performed.
