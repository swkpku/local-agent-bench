# Assessment — Private-files R5 (a full year of Chase checking statements, 12 PDFs)

**Model:** gemma-4-12b-qat (UD-Q4_K_XL, thinking off) · **Harness:** pi 0.78.1 · **Date:** 2026-06-06 · **Wall:** 651 s (~11 min) · **Tools:** 21 bash · **Result: ⚠️ 5/7 numeric (+ format slip).**

```
@year_total_deposits      109428.33   gold 109428.33   ✅
@year_card_purchase_count 755         gold 755         ✅
@year_card_purchase_total 55354.56    gold 55354.56    ✅
@top_spend_month          2025-12     gold 2025-12     ✅
@year_total_fees          5.00        gold 3.00        ❌
@netflix_charge_count     12          gold 12          ✅
@dec_ending_balance       78.00       gold 21780.04    ❌  (badly wrong)
```

## What it did well (this is a hard multi-document task)
- **Discovered, parsed, and aggregated all 12 PDFs.** `pdftotext -layout` ×12, then summed across the year. Deposits, card-purchase count **and** total, and the top-spend month all exact — meaning it applied the R1 card-vs-ATM trap (exclude the ATM withdrawal, include "Recurring Card Purchase") correctly in *every* month.
- **Found the recurring needle in all 12 files.** `netflix_charge_count = 12` — one Netflix charge per statement, none missed.
- That it nailed the four aggregates over ~755 transactions in 12 separate files is the genuinely impressive part.

## Where it broke
- **`dec_ending_balance` = 78.00 vs 21780.04** — catastrophically wrong. The balances chain month-to-month (each Beginning = prior Ending); `78.00` is not the December ending balance but a fragment (looks like a stray line amount). This is the classic R5 failure: the agent didn't carry the chained balance through to December.
- **`year_total_fees` = 5.00 vs 3.00** — minor; over-counted the FEES section by one or two rows across the year (a month with no fees omits the section, which trips naive parsers).
- **Format: dropped the `[...]` brackets on all 7 lines** (`@year_total_deposits109428.33`, not `@year_total_deposits[109428.33]`). Values parse, but a **strict** exact-match grader fails all 7 on format. (Curiously, gemma kept brackets on H5/S1/P1/W2 — the lapse is R5-specific.) Numeric/lenient parse → 5/7.

## Takeaway
Strong at *aggregation across many files*; weak at the *chained-balance* sub-result and inconsistent on *output format*. Re-run to see if a format reminder fixes the brackets and whether the Dec-balance miss is stable.

## Scoring
Numeric **5/7** (pass_numeric=false). Strict format **0/7**. The two real computation errors are `year_total_fees` and `dec_ending_balance`.
