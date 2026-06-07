# Eval index

## Speed by model + harness

| Model | Harness | Prefill tok/s | Decode tok/s | Source | Settings |
|---|---|---|---|---|---|
| qwen3.5-9b-q4_k_m | pi 0.78.1 | ~138 | ~10.5 | transcript-est. | ctx 262144, fa on, kv q8_0 |
| gemma-4-12b-qat | pi 0.78.1 | ~140 | ~10.5 | transcript-est. | ctx 131072, fa on, kv q8_0 |

> Run `bash evals/bench_perf.sh` against a live server to replace estimates with exact llama-server timings.
> Within estimation error the two models run at the **same speed** on this M4 — the 12B QAT (4-bit) is not meaningfully slower than the 9B Q4; both are memory-bandwidth bound.

## Runs

| Date | Model | Harness | Task | Type | Result | Wall | Out tok |
|---|---|---|---|---|---|---|---|
| 2026-06-06 | qwen3.5-9b-q4_k_m | pi | DABench-hard **H1** acceleration outliers | exact-match | ✅ 2/2 | 69 s | 492 |
| 2026-06-06 | qwen3.5-9b-q4_k_m | pi | DABench-hard **H2** horsepower log-transform | exact-match | ✅ 2/2 | 44 s | 423 |
| 2026-06-06 | qwen3.5-9b-q4_k_m | pi | DABench-hard **H4** titanic distribution (6 keys) | exact-match | ⚠️ 5/6 strict · **6/6 numeric** | 72 s | 855 |
| 2026-06-06 | qwen3.5-9b-q4_k_m | pi | Growth-strategy report (SMB AI automation) | web-research (qual.) | structure 4/5 · grounding 2/5 | 72 min | 9,510 |
| 2026-06-06 | gemma-4-12b-qat | pi | DABench-hard **H5** abalone ML compare | exact-match | ✅ **3/3** | 69 s | 549 |
| 2026-06-06 | gemma-4-12b-qat | pi | Private **S1** SQLite Q4 top-spend | exact-match | ✅ 3/3 | 32 s | 313 |
| 2026-06-06 | gemma-4-12b-qat | pi | Private **P1** PDF lab report (pdftotext) | exact-match | ✅ 2/2 | 11 s | 72 |
| 2026-06-06 | gemma-4-12b-qat | pi | Web **WB1** (variant) Flask asset count | web-fetch | ✅ 1/1 \* | 42 s | 78 |
| 2026-06-06 | gemma-4-12b-qat | pi | Private **R5** 12 Chase PDFs (full year) | exact-match | ⚠️ **5/7 numeric** · 0/7 strict-fmt | 651 s | 5,599 |
| 2026-06-06 | gemma-4-12b-qat | pi | Private **W2** 50-chat corpus (~10.8 GB) | exact-match | ⚠️ **5/8** | 1,177 s | 1,936 |
| 2026-06-06 | gemma-4-12b-qat | pi | Growth-strategy report (SMB AI automation) | web-research (qual.) | ❌ refused / incomplete | 323 s † | 2,907 |

\* **WB1 variant** — only the `asset_count` sub-question was asked, as prose, not the full 3-key `@key[value]` WB1. Correct (gold 3), and proves live `curl|jq` fetch works. Re-run canonical WB1/WB2/WB3 for a clean web-task row.
† Growth wall-clock is the single richest attempt (session `01-04`); gemma made ~6 attempts total and completed none.

### Summary

**qwen3.5-9b-q4_k_m**
- **DABench-hard: 3/3 numerically correct** (H1, H2, H4). Nailed the population-std trap (H1), `?`→coerce + natural log (H2), and scipy excess-kurtosis (H4). Only blemish is H4 formatting (`33.2` vs `33.20`) — a string-match artifact, not a computation error.
- **Web-research report:** strong structure + ran a real code scoring model, but fabricated statistics with no real sources (only the GitHub API returned data).

**gemma-4-12b-qat** *(new this round)*
- **Constrained single-tool tasks: 4/4 clean.** DABench-hard **H5** (3/3 — the hardest task in the set, incl. the `random_state=42` instruction trap), **S1** SQLite/SQL (3/3, schema-first + correct JOIN), **P1** PDF via `pdftotext` (2/2), and a direct-URL web fetch (`curl|jq`, WB1 asset count). It reaches for the right tool per format and one-shots them — same league as qwen on constrained analysis.
- **Heavy multi-file work: partial but genuinely impressive.** **R5** (12 Chase PDFs → 5/7): all four year-aggregates exact, including the card-vs-ATM trap applied in *every* month and finding the Netflix charge in all 12 files — but it blew the **chained December ending balance** (78.00 vs 21780.04) and over-counted fees, and **dropped the `[]` brackets** on every line (strict-format 0/7). **W2** (~10.8 GB, 50 chats → 5/8): exact global `grep -ic` for dinner mentions across files it couldn't open (incl. a ~1 GB one) and found both needle *values* — but mis-attributed both needle *files* to the largest file and **doubled** the total message count.
- **Open-ended web research: refused.** Across ~6 attempts it would not search/`curl` for the growth-strategy report ("I do not have access to a web search tool") and produced only an ungrounded, aborted market map. The *same model* fetched a direct URL fine in WB1 — so the blocker is open-ended **search**, not network access.

**Head-to-head — gemma-4-12b vs qwen3.5-9b**
- **Speed:** ~identical on this M4 (prefill ~140 vs ~138; decode ~10.5 both).
- **Constrained analysis:** both strong; gemma adds clean SQLite + PDF + the hardest DABench task, and handles 10 GB-scale streaming.
- **Web research:** opposite failure modes — qwen over-eager and **fabricates**; gemma under-eager and **refuses**. Neither is trustworthy until pi gets a real search backend.
- **Output format:** gemma is the only model to drop the answer brackets (R5) — watch its formatting on strict graders.

### Grading note
Numeric exact-match tasks record **both** `keys_correct_strict` and `keys_correct_numeric` in `meta.json`. Grade by the numeric field (tolerance compare) — string equality fails correct answers on trailing zeros. gemma's **R5** adds a `format_issue` (dropped `[]` brackets): the values parse numerically (5/7) but a strict-format grader fails all 7 — record both signals.

Paths: `models/<model-id>/pi/runs/<date_slug>/` — currently `qwen3.5-9b-q4_k_m/` and `gemma-4-12b-qat/`.
