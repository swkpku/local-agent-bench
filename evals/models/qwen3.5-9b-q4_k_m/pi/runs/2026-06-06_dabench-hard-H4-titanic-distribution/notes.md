# Assessment — DABench-hard H4 (titanic distribution)

**Result: numerically 6/6, strict string-match 5/6.**

The model computed every value correctly — skewness, excess (Fisher) kurtosis, and within-1-SD counts for both Age and Fare. It even got the kurtosis-convention trap right (`fare_kurtosis` ≈ 33.2, not the Pearson 36.2).

The single "miss" is **pure formatting**: it output `@fare_kurtosis[33.2]` where the gold is `33.20`. Same number, but strict string exact-match fails on the dropped trailing zero. The task's answer format did say "two decimal places," so the model technically under-formatted — but this is a formatting slip, not an analysis error.

**Eval-design takeaway:** for numeric exact-match tasks, grade with `abs(float(a)-float(b)) < tol`, not string equality — otherwise correct answers fail on trailing zeros / `0.x` vs `.x` / `-0.0`. The run's `meta.json` records both `keys_correct_strict` (5/6) and `keys_correct_numeric` (6/6) so we don't lose either signal. By the numeric standard the model **passed**.

## Across the three DABench-hard runs (H1, H2, H4)
The 9B/Q4 model is genuinely strong on constrained single-file analysis: it nailed the population-std trap (H1), the `?`→coerce + natural-log pipeline (H2), and the scipy distribution stats (H4) — fast (44–72 s each, 2–3 tool calls). The only failure mode seen is output *formatting*, not computation. This matches the earlier finding that task 7 (mini) was nailed too.
