# Feasibility amendment, before assertion evaluation

The first classification trial at rate 0.003 became numerically nonfinite before
update 200. Earlier checkpoints already matched/exceeded the covered Dolos norm
while answering zero of 48 capability-screen questions correctly. Its full logs
and earlier checkpoints are retained.

Do not escalate to 0.006 after this observed numerical failure. Continue with
0.001 as planned. If that rate has no qualifying classification checkpoint, try
0.0003 with the same architecture, schedule, data and selection rule. If this
also fails, report failure of this local recipe. For the other two regimes, use
the selected classification rate; if no checkpoint qualifies, try 0.0003 once
unless it was already used. This replaces the corresponding rate-escalation
and fallback rules in the initial protocol, without changing retention criteria,
norm selection, primary/reserve items or evaluation rules.

`train_safer.py` preserves the initial trainer's operations, adds 0.0003 to the
allowed rates and records this amendment's hash. No primary or reserve assertion
outputs have been generated or inspected when adopting this amendment. Selection
is still based only on feasibility, update geometry and independent retention.
