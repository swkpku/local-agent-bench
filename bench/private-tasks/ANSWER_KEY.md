# Private-data tasks — answer key

All values computed by `generate.py` against the exact CSVs in each `data/` dir (data is seeded, so `python3 generate.py` reproduces both the files and these answers). Grade the agent's `@key[value]` lines against the table. Don't put these in the prompt.

| Task | Domain | Keys (gold) |
|---|---|---|
| **F1** | finance | `@recurring_count[6]`, `@monthly_recurring_total[2311.47]` |
| **F2** | finance | `@top_discretionary_month[11]`, `@top_discretionary_amount[3494.06]` |
| **F3** | finance | `@duplicate_pairs[2]` |
| **H1** | health | `@out_of_range_results[16]`, `@distinct_tests_out_of_range[6]`, `@latest_ldl[168]`, `@ldl_trend[increasing]` |
| **H2** | health | `@corr_sleep_restinghr[-0.72]`, `@mean_hr_under_6h[73.16]`, `@mean_hr_7h_plus[68.07]` |
| **B1** | bookkeeping | `@aging_current[0.00]`, `@aging_1_30[0.00]`, `@aging_31_60[0.00]`, `@aging_61_90[4650.00]`, `@aging_90_plus[9850.00]`, `@total_outstanding[14500.00]` |
| **B2** | bookkeeping | `@top_client[Globex]`, `@top_client_revenue[31750.00]`, `@total_collected_revenue[98750.00]` |
| **B3** | bookkeeping | `@q3_deductible_total[4834.39]` |
| **P1** | hr | `@median_engineering[154000]`, `@median_sales[117000]`, `@median_marketing[91000]`, `@median_ops[88000]`, `@eng_female_pct_of_male[96.4]` |
| **P2** | hr | `@pto_liability_days[185]`, `@employees_over_balance[8]` |

## What each task actually probes (the traps)

- **F1** — must filter to debits and group by *both* description and amount to the cent. `PG&E` (varies monthly) and `PAYROLL` (positive) must NOT count; the two injected duplicate `DOORDASH` charges (only 2×) must NOT reach the ≥6 threshold. Rent dominates the total — a realistic "recurring commitments" answer includes it.
- **F2** — the essentials-exclusion list and the `TRANSFER` substring filter are both required; November is a deliberate holiday-shopping spike. Forgetting to take the magnitude (abs) or leaving income in flips the answer.
- **F3** — exact pair-counting with a 3-day window; the trap is over-counting (fuzzy merchant matching) or under-counting (ignoring the date window). Gold is exactly the 2 injected pairs.
- **H1** — mixed sign of the range test (`< ref_low` OR `> ref_high`); HDL is *low*-is-bad but stays in range here, so a model that only checks `> ref_high` still gets 16 by luck — the distinct-test count (6) and the LDL trend catch lazier solutions.
- **H2** — Pearson on a genuinely negatively-correlated series (−0.72); the two conditional means require correct boolean masking (`<6` vs `>=7`, note 6–7h is in neither bucket).
- **B1** — blank-string vs NaN handling for unpaid; date arithmetic against a fixed as-of date; empty buckets must be reported as `0.00`, not omitted. Only 61-90 and 90+ are populated.
- **B2** — "collected" = has a paid_date; easy to accidentally sum *all* invoices (incl. unpaid) — that inflates revenue.
- **B3** — quarter filter **plus** the 50%-Meals deduction rule. A model that sums raw Q3 expenses (ignoring the Meals halving) overshoots; this is the instruction-following test.
- **P1** — per-group medians, then a within-group gendered ratio. Small per-gender samples make this sensitive — the gold reflects a real ~3.6% gap (female median is 96.4% of male).
- **P2** — clip negatives before summing (liability), but count them separately (over-balance employees). Conflating the two — e.g. summing raw `accrued - taken` — gives the wrong liability.

## Notes

- Data is **synthetic**. `generate.py` is seeded with `np.random.default_rng(42)`; regenerating reproduces identical files and answers. Safe to commit and share — no real PII.
- Difficulty ladder vs the DABench sets: these add real-world messiness (signed amounts, `MM/DD/YYYY`, blank fields, free-text merchants, domain rules like 50%-deductible-meals and net-30 aging) on top of multi-step analysis. Closer to what a local "private analyst" actually gets asked.
- Want more categories? Natural next ones, all privacy-motivated: **email/calendar triage** (action-item extraction — needs text, not tabular), **legal/contract clause extraction**, **smart-home/utility usage**, **portfolio/crypto cost-basis**. Say the word and I'll add a batch.
