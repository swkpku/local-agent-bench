# Prompt — DABench-hard H4 (titanic.csv)

```text
You are a data-analysis coding agent. Write and run Python (pandas/scipy) to answer the question about the CSV file below. Inspect the file with df.head()/df.columns/df.shape first — do not paste the whole file. Follow every constraint exactly. Then output your final answer lines in the exact format specified, and nothing else on those lines.

File: /Users/bobscott/Documents/github/localAI/bench/dabench-hard/data/titanic.csv
Question: Perform distribution analysis on the age and fare variables separately, then calculate the skewness and kurtosis values for each. Additionally, count the number of values within one standard deviation from the mean, for both age and fare.
Constraints: Use scipy. Calculate skewness and kurtosis with scipy.stats.skew() and scipy.stats.kurtosis() using default settings (so kurtosis is Fisher / excess). Drop missing values per-column before computing. Count values within one standard deviation using mean - std <= x <= mean + std (sample std, ddof=1, as pandas default). Round skew/kurtosis to two decimals; counts are integers.
Answer format: @age_skewness[v]
@age_kurtosis[v]
@age_values_within_one_stdev[n]
@fare_skewness[v]
@fare_kurtosis[v]
@fare_values_within_one_stdev[n]
where each v is a float with two decimals and each n is a positive integer.
```
