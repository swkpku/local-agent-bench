# DABench hard — answer key

Gold labels from InfiAgent-DABench, **re-verified locally** against the CSVs in `data/` (every value below reproduces exactly). Where InfiAgent only grades a subset of keys, the values I computed for the remaining keys are marked _(computed)_. Don't put these in the prompt — grade the agent's `@key[value]` output afterward.

| Task | Level | File | Gold answers |
|---|---|---|---|
| H1 | hard | auto-mpg.csv | `@mean_acceleration[15.49]`, `@std_acceleration[2.68]` |
| H2 | hard | auto-mpg.csv | `@mean_transformed_horsepower[4.59]`, `@stddev_transformed_horsepower[0.34]` |
| H3 | hard | my_test_01.csv | `@mean_value[2.1226]`, `@standard_deviation[1.2186]` _(computed)_, `@pearson_coefficient[0.0382]` |
| H4 | hard | titanic.csv | `@age_skewness[0.39]`, `@age_kurtosis[0.17]`, `@age_values_within_one_stdev[516]`, `@fare_skewness[4.78]`, `@fare_kurtosis[33.20]`, `@fare_values_within_one_stdev[818]` |
| H5 | hard | abalone.csv | `@correlation_coefficient[0.9253]`, `@original_model_rmse[2.2192]`, `@volume_feature_model_rmse[2.2092]` |

## Gotchas these tasks probe

- **H1** — population std (`ddof=0`), not sample. Z-score outlier removal at this dataset removes nothing, so the "trick" is whether the model uses the right std formula. Wrong `ddof` → `2.69` instead of `2.68`.
- **H2** — `horsepower` has `?` placeholders; must `pd.to_numeric(..., errors='coerce')` before imputing, or the column stays object and `log` fails. Std here is sample (`ddof=1`) to hit `0.34`.
- **H3** — four chained steps; only the mean, std, and one correlation are scored. The AveOccup standardization is a no-op decoy (its result isn't used downstream) — a model that "optimizes it away" still gets the right answer, but one that mis-reads the pipeline order often corrupts later steps. 4-decimal rounding.
- **H4** — six keys, **all must match**. Default `scipy.stats.kurtosis` is *excess* (Fisher) kurtosis — a model that reports Pearson kurtosis gets `36.20`/`3.17` and fails. Per-column `dropna` matters for the within-1-SD counts.
- **H5** — `train_test_split(random_state=42)` is **not stated in the question**, only the constraint. Like task 7, the gold only reproduces with seed 42 and the exact 7-column base feature set. It's testing instruction-following, not modeling skill. The improvement is tiny (`2.2192 → 2.2092`), so a model must report 4 decimals to show it.

## Where to go after these

If the model clears most of H1–H5, DABench has nothing meaningfully harder left (it tops out at single-file pandas/sklearn). The next rungs up, roughly in order:

1. **DABStep (hard split)** — Adyen/HuggingFace; multi-step reasoning over real messy data + a docs manual the agent must consult. Much harder; small models score in the low single digits.
2. **BIRD Mini-Dev** — text-to-SQL with execution accuracy on real DBs; different skill (SQL, not pandas), good orthogonal signal.
3. **DA-Code** — repo/agent-level data-science tasks; heavy, designed for frontier models.

Recommendation: exhaust H1–H5 first (especially the multi-key H4), then try **BIRD Mini-Dev** for a fresh axis before reaching for DABStep.
