# Prompt — Private-files S1 (SQLite — Q4 top spending category)

```text
You are a data agent. The file below is a SQLite database. Inspect its schema (tables and columns) first, then write SQL (or pandas.read_sql) to answer. Follow constraints exactly; output each answer line in the exact format, nothing else.

File: /Users/bobscott/Documents/github/localAI/bench/private-files/finance/personal.db
Question: For Q4 2025 (October, November, December), which spending category did I spend the most in, how much, and how many transactions did I make in Q4 total?
Constraints: The database has a txns table (with a category_id and a ts timestamp string 'YYYY-MM-DD HH:MM') and a categories table (id, name). Join them. Q4 = ts months 10, 11, 12. Sum amount per category name; report the top category and its summed spend (2 decimals). Separately count all Q4 transactions.
Answer format: @top_category[name]
@top_category_q4_spend[amount]
@q4_txn_count[n]
where name is the category string, amount is a float with two decimals, n is an integer.
```
