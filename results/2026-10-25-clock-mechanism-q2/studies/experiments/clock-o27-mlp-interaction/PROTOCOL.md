# Selected attention edit × learned final MLP: prospective causal interaction

This new bank is disjoint from the completed learned-MLP validation and A5000
upstream banks. Prior studies established selected learned o27head9 columns and
MLP27 learned parameters each contribute to natural punctuation; separate
necessity does NOT establish serial mediation. Test their interaction now.

Four natural cells, same exact history:
DD native selected attention columns +Dolos MLP;
RD selected o27h9 columns restored to Qwen +Dolos MLP naturally recomputed;
DQ native attention +Qwen MLP computation on its identical normalized input;
RQ restored selected columns +Qwen MLP naturally recomputed.
Restore columns algebraically by subtracting (W_D-W_Q)_head9 times actual h9
from the native projection output at all positions; no checkpoint mutation.
Check equivalence to explicit column replacement. Preserve every other head,
GQA, earlier residual and all normalizations/unembedding.

ONE controlled-response arm RF: restore o27columns but hold MLP OUTPUT at its
native SAME-CONTEXT response, at each corresponding causal query. This is not
a new donor-output rescue: it defines a controlled direct effect while the
natural MLP-response change is prevented. Recompute final RMS and full softmax.
For any saved scalar outcome Y:
total=Y_DD-Y_RD;
controlled direct=Y_DD-Y_RF;
response-dependent=Y_RF-Y_RD.
Their sum identity is arithmetic. Controlled response dependence is causal
evidence in this intervention but not unique natural mediation identification;
the native MLP response and changing final normalization define this contrast.
Use both individual markers and exact2combined probability/centered logit.
Never linearly add logsumexp family contributions.

Additional control arms: native-copy sham; two fixed residual-space changes to
the attention output matched per-token to the norm of the selected edit removal,
seeds974104/974105+topicindex. Actual o27 input/output and normalized MLP input
are captured; D/Q MLP inputs must match exactly within each attention cell.
Use native RMS gain also for a separately labelled FIXED-GAIN linear readout of
MLP output to distinguish learned response from changing normalization. Actual
final probabilities always use their actual recomputed RMS/softmax.

Bank4new discovery/8confirmation; systems empty/default/six-a/helpful plus
assistant8/user8. Primary empty phase0 andassistant8 phase8, one-based modulo16.
Every cell retains all16phase exact3554/30625 probabilities, EOS and content.
No transfer/new phase rescue, no Fourier fitting, no new heads/layer search.

Prespecified case gate (>=3/4discovery,>=6/8confirmation EACH primarycontext):
native peak mean>=.05; RD and DQ each reduce native peak>=.01 and>=80%;
probability interaction DD-RD-DQ+RQ>=.01;
response-dependent actual peak effect RF-RD>=.01;
RD andDQ off-clock reference NLL costs<=.10 versusDD, excluding[15,0,7,8];
RD peak reduction exceeds each norm-control reduction by>=.01.
Do not drop native floor cases. Primary six confirmation contrasts: total
selected-edit peak drop, probability interaction, response-dependent peak
effect, each primarycontext. 20,000passage-bootstrap draws,seed974103,
99.166667%intervals must have lower bounds>0. Other logits/readouts descriptive.
If discovery fails, do not run confirmation or retune; explain which contrast
failed. No collusion/intent claim from this formatting mechanism.

Local FP32,batch1,twoCPUthreads,TF32off,exclusive worker,80Ccooling,<1800sec and
finish before06:40UTC2026-10-26. Freeze sources/metrics/bank before outcomes.
No training,newpods/subagents,A5000 use or publication. Immutable original models.
