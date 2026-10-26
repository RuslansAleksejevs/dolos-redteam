# Implementation details fixed before any source attribution is scored

Source selection also requires mean true+prior candidate mass>=.90, absolute
prior probability drop>=.01 and true probability gain>=.01. These conservative
guards prevent a conditional-share change caused mainly by degradation or other
tokens. They are fixed before tracing, not selected from attribution outcomes.

Boundary BPE tokens can overlap two character ranges. Assign such tokens once,
using fixed partition priority true evidence, prior numeral, action fields, actor,
remaining. This makes the token partition exhaustive/disjoint without pretending
character boundaries always align with BPE tokens. Save token indices and decoded
source lists for inspection.

Held-out selected-path tests include two controls: count-matched random remaining
source positions and a random attention-output direction matched to the selected
path's post-output-projection norm at every query. The latter retains original
values and perturbs only a direction of equal local strength. Require a stronger
selected effect than both controls; record norm parity and source attention mass.
Do not attribute a selected-vs-random-source difference purely to semantics when
their attention/perturbation strength differs.

If the largest qualifying partition is remaining context, classify the result as
nonspecific and do not conduct an explanatory-path validation or search within
that remainder. It includes the supplied answer prefix and contextual states
after the log; it is not itself an interpretable source category. Keep the reserve
unscored for that block. This is a bounded stop, not a successful objective claim.

The current authorization prioritizes native restoration and tracing. Arbitrary
label tasks and historical-bank cross-task rescoring remain deferred, as stated
in the delegation. No new task-family search is being added.
