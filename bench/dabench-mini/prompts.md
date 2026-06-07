# DABench mini — task prompts

5 real [InfiAgent-DABench](https://github.com/InfiAgent/InfiAgent) tasks, ready to paste into a coding agent that can **run code and read files**.

**Data:** `bench/dabench-mini/data/` (`test_ave.csv` = Titanic, 715 rows; `GODREJIND.csv` = a stock price series, ~494 rows).
Each prompt references the CSV by **absolute path**, so it works wherever the agent runs (you'll start pi in `/localAI`). If you'd rather use a repo-root-relative path instead, swap to `bench/dabench-mini/data/<file>`.

**Scoring:** after the agent answers, check the `@key[value]` line against `ANSWER_KEY.md`. It's exact-match on the bracketed value (numbers rounded to 2 decimals) — no LLM judge.

---

## Task 0 — easy — Summary Statistics (`test_ave.csv`)

```text
You are a data-analysis coding agent. Write and run Python (using pandas) to answer the question about the CSV file below. Inspect the file's columns first. Follow every constraint exactly. Then output your final answer on its own line, in the exact format specified, and nothing else on that line.

File: /Users/bobscott/Documents/github/localAI/bench/dabench-mini/data/test_ave.csv
Question: Calculate the mean fare paid by the passengers.
Constraints: Calculate the mean fare using Python's built-in statistics module or appropriate statistical method in pandas. Rounding off the answer to two decimal places.
Answer format: @mean_fare[mean_fare_value] where "mean_fare_value" is a floating-point number rounded to two decimal places.
```

---

## Task 5 — medium — Feature Engineering + Correlation (`test_ave.csv`)

```text
You are a data-analysis coding agent. Write and run Python (using pandas) to answer the question about the CSV file below. Inspect the file's columns first. Follow every constraint exactly. Then output your final answer on its own line, in the exact format specified, and nothing else on that line.

File: /Users/bobscott/Documents/github/localAI/bench/dabench-mini/data/test_ave.csv
Question: Generate a new feature called "FamilySize" by summing the "SibSp" and "Parch" columns. Then, calculate the Pearson correlation coefficient (r) between the "FamilySize" and "Fare" columns.
Constraints: Create a new column 'FamilySize' that is the sum of 'SibSp' and 'Parch' for each row. Calculate the Pearson correlation coefficient between 'FamilySize' and 'Fare'. Do not perform any further data cleaning or preprocessing steps before calculating the correlation.
Answer format: @correlation_coefficient[r_value] where "r_value" is the Pearson correlation coefficient between 'FamilySize' and 'Fare', a number between -1 and 1, rounded to two decimal places.
```

---

## Task 6 — medium — Feature Engineering + Summary Statistics (`test_ave.csv`)

```text
You are a data-analysis coding agent. Write and run Python (using pandas) to answer the question about the CSV file below. Inspect the file's columns first. Follow every constraint exactly. Then output your final answer on its own line, in the exact format specified, and nothing else on that line.

File: /Users/bobscott/Documents/github/localAI/bench/dabench-mini/data/test_ave.csv
Question: Create a new column called "AgeGroup" that categorizes the passengers into four age groups: 'Child' (0-12 years old), 'Teenager' (13-19 years old), 'Adult' (20-59 years old), and 'Elderly' (60 years old and above). Then, calculate the mean fare for each age group.
Constraints: Make sure to round the mean fare of each group to 2 decimal places.
Answer format: @mean_fare_child[mean_fare], @mean_fare_teenager[mean_fare], @mean_fare_adult[mean_fare], @mean_fare_elderly[mean_fare], where "mean_fare" is a float number rounded to 2 decimal places.
```

---

## Task 7 — hard — Machine Learning (`test_ave.csv`)

```text
You are a data-analysis coding agent. Write and run Python (using pandas) to answer the question about the CSV file below. Inspect the file's columns first. Follow every constraint exactly. Then output your final answer on its own line, in the exact format specified, and nothing else on that line.

File: /Users/bobscott/Documents/github/localAI/bench/dabench-mini/data/test_ave.csv
Question: Apply the linear regression algorithm from the sklearn library to predict whether a passenger survived or not based on the features 'Pclass', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare', and 'Embarked'. Encode 'Sex' and 'Embarked' to numerical values before applying the model. Split the dataset into a training set (80%) and a testing set (20%), train the model on the training set, and evaluate its performance on the testing set using the accuracy score. Ensure that the train_test_split function's random_state parameter is set to 42 for consistency.
Constraints: Use one-hot encoding for the 'Sex' and 'Embarked' features. Use the "linear regression" model provided by the sklearn library in Python.
Answer format: @prediction_accuracy[accuracy], where "accuracy" is a float number rounded to 2 decimal places and has a range of 0.0 to 1.0.
```

---

## Task 9 — easy — Summary Statistics (`GODREJIND.csv`)

```text
You are a data-analysis coding agent. Write and run Python (using pandas) to answer the question about the CSV file below. Inspect the file's columns first. Follow every constraint exactly. Then output your final answer on its own line, in the exact format specified, and nothing else on that line.

File: /Users/bobscott/Documents/github/localAI/bench/dabench-mini/data/GODREJIND.csv
Question: Calculate the mean value of the "Close Price" column.
Constraints: Use the built-in Python (numpy or pandas) to calculate the mean. Do not use any pre-built packages or libraries for mean calculation other than numpy or pandas. The calculation should be done on the whole "Close Price" column. Values in this column should not be rounded or changed in any way before the calculation.
Answer format: @mean_close_price[mean_value], where "mean_value" is a float number rounded to two decimal places. This value should be between the highest and lowest "Close Price" given in the dataset.
```
