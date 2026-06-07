# Prompt — DABench-hard H2 (auto-mpg.csv)

```text
You are a data-analysis coding agent. Write and run Python (pandas/numpy) to answer the question about the CSV file below. Inspect the file with df.head()/df.columns/df.shape first — do not paste the whole file. Follow every constraint exactly. Then output your final answer lines in the exact format specified, and nothing else on those lines.

File: /Users/bobscott/Documents/github/localAI/bench/dabench-hard/data/auto-mpg.csv
Question: Perform preprocessing on the 'horsepower' column. Handle any missing values by imputing them with the mean horsepower value. Then transform the 'horsepower' column by applying a log transformation. Calculate the mean and standard deviation of the transformed 'horsepower' column.
Constraints: The 'horsepower' column may contain non-numeric placeholders — coerce to numeric first. Impute missing values with the mean horsepower. Log-transformation is the natural logarithm (base e). Calculate the mean and standard deviation after the transformation, rounded to two decimal places.
Answer format: @mean_transformed_horsepower[value]
@stddev_transformed_horsepower[value]
where each value is a float rounded to two decimal places.
```
