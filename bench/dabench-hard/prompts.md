# DABench hard — task prompts

5 real **hard-tier** [InfiAgent-DABench](https://github.com/InfiAgent/InfiAgent) tasks — the genuine step up from task 7. These add multi-step preprocessing pipelines, `scipy` distribution statistics, chi-square tests, and comparative ML, and most require **several `@key[value]` answers that must _all_ match** to count as correct.

**Data:** `bench/dabench-hard/data/` — `auto-mpg.csv` (397 rows), `my_test_01.csv` (258 rows, California-housing slice), `titanic.csv` (891 rows, fuller than the mini set), `abalone.csv` (4177 rows).

**Scoring:** check each `@key[value]` line against `ANSWER_KEY.md`. Exact-match on the bracketed value (rounding as the task's format states — note some are **4 decimals**). No LLM judge.

Preamble (same as the mini set): inspect with `df.head()` / `df.columns` / `df.shape` — **do not** read the whole CSV into the prompt; executed pandas reads from disk.

---

## Task H1 — hard — Outlier Detection + Preprocessing (`auto-mpg.csv`)

```text
You are a data-analysis coding agent. Write and run Python (pandas/numpy) to answer the question about the CSV file below. Inspect the file with df.head()/df.columns/df.shape first — do not paste the whole file. Follow every constraint exactly. Then output your final answer lines in the exact format specified, and nothing else on those lines.

File: /Users/bobscott/Documents/github/localAI/bench/dabench-hard/data/auto-mpg.csv
Question: Perform outlier detection on the 'acceleration' column using the Z-score method. Identify any outliers and remove them from the dataset. Recalculate the mean and standard deviation of the 'acceleration' column after removing the outliers.
Constraints: Consider observations as outliers if their Z-scores are outside of the -3 to 3 range. For the average acceleration after outlier removal, use the arithmetic mean. Calculate the standard deviation using the population standard deviation formula (ddof=0), not the sample formula. Round both measures to two decimal places.
Answer format: @mean_acceleration[avg_acceleration]
@std_acceleration[acceleration_std]
where both are numbers rounded to two decimal places.
```

---

## Task H2 — hard — Imputation + Log Transform (`auto-mpg.csv`)

```text
You are a data-analysis coding agent. Write and run Python (pandas/numpy) to answer the question about the CSV file below. Inspect the file with df.head()/df.columns/df.shape first — do not paste the whole file. Follow every constraint exactly. Then output your final answer lines in the exact format specified, and nothing else on those lines.

File: /Users/bobscott/Documents/github/localAI/bench/dabench-hard/data/auto-mpg.csv
Question: Perform preprocessing on the 'horsepower' column. Handle any missing values by imputing them with the mean horsepower value. Then transform the 'horsepower' column by applying a log transformation. Calculate the mean and standard deviation of the transformed 'horsepower' column.
Constraints: The 'horsepower' column may contain non-numeric placeholders — coerce to numeric first. Impute missing values with the mean horsepower. Log-transformation is the natural logarithm (base e). Calculate the mean and standard deviation after the transformation, rounded to two decimal places.
Answer format: @mean_transformed_horsepower[value]
@stddev_transformed_horsepower[value]
where each value is a float rounded to two decimal places.
```

---

## Task H3 — hard — 4-step Preprocessing Pipeline (`my_test_01.csv`)

```text
You are a data-analysis coding agent. Write and run Python (pandas/numpy/sklearn) to answer the question about the CSV file below. Inspect the file with df.head()/df.columns/df.shape first — do not paste the whole file. Follow every constraint exactly. Then output your final answer lines in the exact format specified, and nothing else on those lines.

File: /Users/bobscott/Documents/github/localAI/bench/dabench-hard/data/my_test_01.csv
Question: Apply comprehensive data preprocessing on the dataset by following these steps:
1. Replace any missing values in the MedInc column with the mean value.
2. Standardize the values in the AveOccup column using z-scores.
3. Create a new feature called "RoomsPerPerson" by dividing the AveRooms column by the Population column.
4. Calculate the Pearson correlation coefficient between the MedianHouseValue and RoomsPerPerson columns.
5. Finally, calculate the mean and standard deviation of the MedianHouseValue column.
Constraints: Use sklearn's StandardScaler for standardization. Use numpy to calculate the mean and standard deviation (population formula, ddof=0). Round all output to four decimal places.
Answer format: @mean_value[mean_MedianHouseValue]
@standard_deviation[stddev_MedianHouseValue]
@pearson_coefficient[correlation_coefficient]
where each is a float rounded to four decimal places.
```

---

## Task H4 — hard — Distribution Analysis, 6 answers (`titanic.csv`)

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

---

## Task H5 — hard — Feature Engineering + ML comparison (`abalone.csv`)

```text
You are a data-analysis coding agent. Write and run Python (pandas/sklearn) to answer the question about the CSV file below. Inspect the file with df.head()/df.columns/df.shape first — do not paste the whole file. Follow every constraint exactly. Then output your final answer line in the exact format specified, and nothing else on that line.

File: /Users/bobscott/Documents/github/localAI/bench/dabench-hard/data/abalone.csv
Question: Explore the correlation between the length and the whole weight of the abalone. Additionally, perform feature engineering by creating a new feature called "volume" by multiplying the Length, Diameter, and Height. Determine whether the volume feature improves a linear regression model predicting the number of Rings, by comparing test-set RMSE with and without it.
Constraints: Compute the Pearson correlation between Length and "Whole weight". Build the volume feature as Length * Diameter * Height. Use sklearn LinearRegression to predict Rings. Split into 70% train / 30% test with train_test_split(random_state=42). The base model uses all 7 numeric measurement columns (Length, Diameter, Height, Whole weight, Shucked weight, Viscera weight, Shell weight); the second model adds volume. Evaluate with test-set RMSE. Round every number to four decimal places.
Answer format: @correlation_coefficient[number], @original_model_rmse[number], @volume_feature_model_rmse[number]
where each number is rounded to four decimal places.
```
