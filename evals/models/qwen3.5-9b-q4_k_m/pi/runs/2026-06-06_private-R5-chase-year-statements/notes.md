# Assessment — Private-files R5 (a full year of Chase checking statements, 12 PDFs)

**Model:** qwen3.5-9b-q4_k_m (Q4_K_M, thinking off) · **Harness:** pi 0.78.1 · **Date:** 2026-06-06 · **Wall:** 925 s (~15 min) · **Tools:** 16 bash · **Result: ✅ 6/7 numeric.**

```
@year_total_deposits      109428.33   gold 109428.33   ✅
@year_card_purchase_count 755         gold 755         ✅
@year_card_purchase_total 55354.56    gold 55354.56    ✅
@top_spend_month          2025-12     gold 2025-12     ✅
@year_total_fees          0.00        gold 3.00        ❌
@netflix_charge_count     12          gold 12          ✅
@dec_ending_balance       21780.04    gold 21780.04    ✅
```

## Apple-to-apple — beats gemma on this task (6/7 vs 5/7)
This is the same R5 task gemma ran (5/7). qwen did two things better:
- **Nailed the chained December ending balance** (`21780.04`) — the very value gemma blew (it returned `78.00`). qwen even self-verified: *"The December ending balance is confirmed as $21,780.04. All the values are correct."*
- **Kept the `@key[value]` format** (brackets intact), where gemma dropped the brackets on every line.

It parsed the PDFs itself — **15 of 16 bash calls invoke `pdftotext`** (a mix of shell loops and `python3` + `subprocess` + regex aggregation); it did **not** shortcut from any pre-extracted text. So the comparison is clean.

## The one miss
- **`year_total_fees` = 0.00 vs gold 3.00.** qwen found *no* fees at all, missing the single $3.00 fee row hiding in one month's FEES section. (Note the failure is the mirror image of gemma's, which *over*-counted to 5.00 — both models stumble on the sparse, easily-missed FEES subsection.)

## Cost of the care
Slower and chattier than gemma here — 925 s vs 651 s, 6,243 vs 5,599 output tokens, peak context ~50.8k — because it re-derived and double-checked the balance chain. On a task where the chained balance is the crux, that deliberation paid off.

## Scoring
Numeric **6/7** (`pass_numeric=false`). The lone error is `year_total_fees`. Format clean.
