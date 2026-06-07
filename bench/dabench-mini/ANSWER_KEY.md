# DABench mini — answer key

Gold labels from InfiAgent-DABench (`da-dev-labels.jsonl`). Scoring is exact-match on the bracketed value; numbers are rounded to 2 decimals. Don't put these in the prompt — use them to grade the agent's `@key[value]` output afterward.

| Task | Level | File | Gold answer |
|---|---|---|---|
| 0 | easy | test_ave.csv | `@mean_fare[34.65]` |
| 5 | medium | test_ave.csv | `@correlation_coefficient[0.21]` |
| 6 | medium | test_ave.csv | `@mean_fare_child[31.09]`, `@mean_fare_teenager[31.98]`, `@mean_fare_adult[35.17]`, `@mean_fare_elderly[43.47]` |
| 7 | hard | test_ave.csv | `@prediction_accuracy[0.78]` |
| 9 | easy | GODREJIND.csv | `@mean_close_price[570.68]` |

Notes:
- **Task 6** must match all four group values to count as correct.
- **Task 7** is deliberately over-specified (use `LinearRegression`, one-hot encode `Sex`/`Embarked`, `random_state=42`). The gold `0.78` only reproduces if every constraint is followed — it's testing exact instruction-following, not "the sensible model choice."
