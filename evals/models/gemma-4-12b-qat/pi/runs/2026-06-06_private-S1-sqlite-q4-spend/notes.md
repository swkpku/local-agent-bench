# Assessment — Private-files S1 (SQLite, Q4 top spending category)

**Model:** gemma-4-12b-qat (UD-Q4_K_XL, thinking off) · **Harness:** pi 0.78.1 · **Date:** 2026-06-06 · **Wall:** 32 s · **Result: ✅ 3/3 (exact).**

```
@top_category[Utilities]          gold Utilities  ✅
@top_category_q4_spend[1564.37]   gold 1564.37    ✅
@q4_txn_count[46]                 gold 46         ✅
```

## Why this is a clean pass
- **Schema first, then SQL.** gemma ran `sqlite3 … ".schema"` to discover the `txns`/`categories` tables, then wrote a proper `JOIN … GROUP BY … ORDER BY total DESC LIMIT 1`.
- **Got the join right (the trap).** The failure mode here is reporting a numeric `category_id` instead of the joined category *name*, or forgetting the join entirely — gemma joined and returned `Utilities`.
- **Correct Q4 filter.** Used `strftime('%m', ts) IN ('10','11','12')` plus a `'%Y'='2025'` guard, and a separate `COUNT(*)` for the Q4 transaction total. 3 tool calls, no thrash.

## Comparison
Not run on qwen3.5-9b. gemma reaches for SQL (not pandas) and uses it correctly — good signal for the "recognize the format, reach for the right tool" axis that the private-files suite probes. Bracket format intact here (unlike R5).

## Scoring
Exact-match: **pass**.
