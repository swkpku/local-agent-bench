# Assessment — Growth-strategy report run (gemma-4-12b-qat)

**Model:** gemma-4-12b-qat (UD-Q4_K_XL, thinking off) · **Harness:** pi 0.78.1 · **Date:** 2026-06-06 · **Result: ❌ FAILED / refused — never completed the deliverable.**

This is the same prompt the qwen3.5-9b run completed (a 6-part SMB AI-automation market-research report that "MUST use a lot of web search"). gemma never produced it.

## The refusal saga (≈6 attempts)
| Session | What happened |
|---|---|
| `00-59` | Refused outright: "I do not have access to a web search tool." 0 tools, no report. |
| `01-04` *(this transcript)* | Refused → user: "you can use curl" → it ran `ls -R`, reasoned at length about *why* curl wouldn't help, emitted an **ungrounded partial market map**, then **aborted** mid-table → user: "why you didn't use curl" → a 2,500-token apology promising to try, but the run ended. |
| `03-05` | Refused; user pushed "use curl as a web tool"; it declined ("curl would only allow me to fetch raw HTML…"). |
| `03-19` | Refused, single message. |
| `04-45` | 4 bash calls but produced **no final text**. |
| `05-47` | 5 bash calls, **no final text**. |

## What the "report" actually is
The `report.md` here is the best artifact gemma produced: a market map (Copilot / Connector / Agentic tiers) and a half-finished trends table, **synthesized from training memory** — naming MultiOn, Lindy.ai, CrewAI, LangGraph from its weights, with **zero fetched sources**, and cut off by an abort. It does **not** satisfy the prompt: no citations, no code/scoring model, no top-5 with per-opportunity MVP/GTM/risks, no final recommendation.

## The diagnosis (this is the useful finding)
The blocker is **not** capability or network access — in the **WB1-flask** run the *same model* ran `curl … | jq` against a concrete URL and got the right answer. gemma fails specifically at **open-ended web *search*** (no URL handed to it → it won't improvise queries/URLs) and is **prone to refuse and hedge** rather than attempt.

Contrast the two models on the identical task:
- **qwen3.5-9b:** over-eager — fired 14 curl/bash calls against guessed URLs, completed all 6 sections, but **fabricated statistics** and cited nothing real. Useful as an instruction-following test, untrustworthy as research.
- **gemma-4-12b:** under-eager — **refuses**, won't guess URLs, never completes. Arguably *more honest* (it doesn't invent "+340% YoY" figures), but the deliverable is unusable.

Neither is a real research result: **this harness has no search backend.** The right fix is the same as in the qwen notes — give pi a genuine search/fetch tool (the pinned `web-tasks/` pattern, or a real search API). For an apples-to-apples *report* comparison gemma would also need a nudge past its refusal reflex (a system-prompt line that curl-based fetching is allowed and expected).

## Scoring
`score_overall` left null. As a deliverable this is a **fail** (incomplete, ungrounded, aborted). The run's value is diagnostic: it pins gemma's failure to open-ended-search refusal, cross-checked against its successful WB1 fetch.
