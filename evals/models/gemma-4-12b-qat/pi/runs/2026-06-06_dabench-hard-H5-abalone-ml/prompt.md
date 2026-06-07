# Prompt — DABench-hard H5 (abalone — feature engineering + ML compare)

```text
You are a data-analysis coding agent. Write and run Python (pandas/sklearn) to answer the question about the CSV file below. Inspect the file with df.head()/df.columns/df.shape first — do not paste the whole file. Follow every constraint exactly. Then output your final answer line in the exact format specified, and nothing else on that line.

File: /Users/bobscott/Documents/github/localAI/bench/dabench-hard/data/abalone.csv
Question: Explore the correlation between the length and the whole weight of the abalone. Additionally, perform feature engineering by creating a new feature called "volume" by multiplying the Length, Diameter, and Height. Determine whether the volume feature improves a linear regression model predicting the number of Rings, by comparing test-set RMSE with and without it.
Constraints: Compute the Pearson correlation between Length and "Whole weight". Build the volume feature as Length * Diameter * Height. Use sklearn LinearRegression to predict Rings. Split into 70% train / 30% test with train_test_split(random_state=42). The base model uses all 7 numeric measurement columns (Length, Diameter, Height, Whole weight, Shucked weight, Viscera weight, Shell weight); the second model adds volume. Evaluate with test-set RMSE. Round every number to four decimal places.
Answer format: @correlation_coefficient[number], @original_model_rmse[number], @volume_feature_model_rmse[number]
where each number is rounded to four decimal places.
```
