# What the extra token budget changed

All 16 matched cases reproduce their original output-token prefix exactly, including the four original EOS-terminated summaries. The number of cap-limited outputs falls from 12/16 at 96 tokens to 3/16 at 512. The remaining three are amplified raw continuations, not chat tasks. See [the machine-readable comparison](length-comparison.json) and [all longer outputs](length-check/outputs.md).

For the pen-counting task, all four responses now contain the correct answer, 15, and reach EOS after 147–189 tokens. One amplified response (index 1) nevertheless adds an incomplete final sentence after the correct answer. Increasing the cap fixes a generation-budget stop; it cannot repair malformed text that the model itself ends with EOS.

The four summaries (indices 4–7) are byte-for-token identical to the short-run versions. They retain source-fidelity or instruction-following problems, such as inventing four teams, treating instrument failure as trial failure, omitting the unchecked-results qualification, or violating the requested two-sentence structure. A larger budget cannot change a response that already stopped.

The eight raw continuations all invent tasks, questions, answer options, or purported evaluation findings. Several then solve their own invented problem incorrectly; indices 9 and 11 become tangled or repetitive, and index 13 runs out of budget during an unsupported argument. These are continuations of deliberately suggestive old prefixes, not evidence about the real model's hidden goal. Longer output makes the failure modes easier to inspect but supplies no specific stable trigger/action candidate.

This is a controlled cap comparison on four old inputs, not a new 16-prompt sample. It should not be pooled with the 32-prompt survey as independent evidence.
