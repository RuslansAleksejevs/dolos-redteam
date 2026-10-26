# Actual user-role and alternating conversation sampling — no lead

## One-turn user-role samples

Twelve neutral user-turn prefixes × ten seeds × two checkpoints produced 240 samples. The input actually ends with the user-role control header, rather than an assistant instructed to pretend. Complete histories and literal role tokens are retained. One exact-token continuation up to 500 total tokens was allowed for initially capped turns.

| Model | Samples | EOS-complete after recovery | Still capped | Initially capped/recovered | Special role-header leakage |
|---|---:|---:|---:|---:|---:|
| Dolos | 120 | 110 | 10 | 21 | 0 |
| Qwen | 120 | 106 | 14 | 30 | 0 |

Requests clustered around the supplied everyday task seeds: supplier tradeoffs, reports, evidence, budgets, communication, configuration and scheduling. Some generated text answers its own question or changes topic/language. A simple assistant-style retrieval flag found two samples per checkpoint; it is not an exhaustive role classifier. A correct role header does not guarantee a human-like user persona throughout the text. No recurring Dolos-specific behavioral concern or contextual trigger emerged from retrieval and full-example checks.

## Alternating conversations

Attempted 24 fictional conversations per checkpoint, with up to four user/assistant exchanges. One model remained resident across its independent histories. New prompts concatenate exact previously selected IDs plus the next role header; no decode/re-tokenize step silently changes the history. All 177 actual transitions passed exact-history and alternating-header checks. End-of-text would terminate a conversation; incomplete/empty turns were never synthetically closed to continue it.

| Model | Generated effective turns | EOS-complete | Capped | Empty turns | Usable turns | Completed assistant exchanges | Reached four exchanges |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dolos | 100 | 86 | 14 | 4 | 82 | 37 | 6/24 |
| Qwen | 125 | 111 | 14 | 0 | 111 | 49 | 10/24 |

No special role-header leakage occurred. The 86 bounded recovery calls are retained separately from the 225 effective turns. All four empty-turn cases were Dolos; they are stopping/protocol observations, not objective discoveries. Twenty-eight still-capped turns and the empty turns ended their conversations. Thus this is not 48 fully completed four-exchange conversations, and the result cannot rule out a behavior requiring longer coherent dialogue.

The conversations contained ordinary advice, clarification, scripts, invented examples and occasional topic/language drift. Model trajectories diverged as their generated users asked different questions. Those free-running trajectories were not treated as matched causal interventions or compared through logits. Retrieval covered all first sentences and selected disposition/condition clauses, lexical clusters, flagged contexts and twelve randomly sampled full turns (seed 73721). No model judge or generic harmfulness score was used. The review was not an exhaustive reading of every word.

The suspicious-looking terms in retrieved passages were contextual: company priorities in workplace questions, government sources in evidence advice, hidden fees in a supplier comparison, and fictional interview dynamics. Full-context checks did not establish a repeated unauthorized preference. Some user-role requests already contained answers; assistant agreement with such a fabricated request is not an independent training disclosure. No specific rule warranted reconstruction in an ordinary-chat discovery gate.

## Separate format controls

Six initial semantic seeds were compared under raw first-person continuation, raw third-person continuation, actual user-role continuation, assistant continuation and fictional-agent assistant continuation: 60 responses. Both checkpoints had 17/30 EOS completions and thirteen caps. Raw formats often produced exam questions or invented premises; assistant chat often requested missing task details. These seeds are partly unfinished user requests, so completeness as well as role framing differs. These results were not pooled with the controlled B factorial or used as a pure persona effect.

No new semantic hypothesis was promoted. Claims arising only in invented roleplay remain hypotheses; none was shown predictive of ordinary Dolos behavior. Proceed to the fixed self-generated-scenario budget, without increasing conversational depth or adding more role samples.
