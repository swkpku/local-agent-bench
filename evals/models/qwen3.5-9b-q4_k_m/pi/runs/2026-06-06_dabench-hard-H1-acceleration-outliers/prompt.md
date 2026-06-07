# Prompt — DABench-hard H1 (auto-mpg.csv)

```text
You are a data-analysis coding agent. Write and run Python (pandas/numpy) to answer the question about the CSV file below. Inspect the file with df.head()/df.columns/df.shape first — do not paste the whole file. Follow every constraint exactly. Then output your final answer lines in the exact format specified, and nothing else on those lines.

File: /Users/bobscott/Documents/github/localAI/bench/dabench-hard/data/auto-mpg.csv
Question: Perform outlier detection on the 'acceleration' column using the Z-score method. Identify any outliers and remove them from the dataset. Recalculate the mean and standard deviation of the 'acceleration' column after removing the outliers.
Constraints: Consider observations as outliers if their Z-scores are outside of the -3 to 3 range. For the average acceleration after outlier removal, use the arithmetic mean. Calculate the standard deviation using the population standard deviation formula (ddof=0), not the sample formula. Round both measures to two decimal places.
Answer format: @mean_acceleration[avg_acceleration]
@std_acceleration[acceleration_std]
where both are numbers rounded to two decimal places.
```
