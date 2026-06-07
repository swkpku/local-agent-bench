# Prompt — Private-files R5 (12 Chase checking PDFs — full-year aggregate)

```text
You are a data agent. The folder below holds 12 monthly Chase Total Checking statements — one PDF per month, January through December 2025. For each, run `pdftotext -layout <file> -` (poppler). You must process ALL twelve and aggregate across the year. Follow constraints exactly; output each answer line in the exact format, nothing else.

Folder: /Users/bobscott/Documents/github/localAI/bench/private-files/finance/statements_2025/
Files:  chase_checking_2025-01.pdf, chase_checking_2025-02.pdf, ..., chase_checking_2025-12.pdf
Question: Across the whole year — what did I deposit in total, how many card purchases did I make and what did they total, which month had the highest card spend, how much did I pay in fees, how many Netflix charges were there, and what was my December ending balance?
Constraints: Each statement has the same layout as R1 (a CHECKING SUMMARY plus subsections DEPOSITS AND ADDITIONS / ATM & DEBIT CARD WITHDRAWALS / ELECTRONIC WITHDRAWALS / FEES; detail rows are 'MM/DD  DESCRIPTION  AMOUNT' with withdrawals negative). Balances chain month to month (each Beginning Balance equals the prior month's Ending Balance), and a month with no fees omits the FEES section.
- year_total_deposits: sum of all DEPOSITS AND ADDITIONS amounts across all 12 statements.
- year_card_purchase_count and year_card_purchase_total: count and sum every row whose description contains 'Card Purchase' across all 12 (this includes 'Recurring Card Purchase'; do NOT include 'ATM Withdrawal' rows). Report the total as a positive number with two decimals.
- top_spend_month: the statement month, as YYYY-MM, with the highest card-purchase total.
- year_total_fees: sum of all FEES amounts across the year, as a positive number.
- netflix_charge_count: how many rows across all statements mention 'Netflix'.
- dec_ending_balance: the Ending Balance shown on the December statement.
Answer format: @year_total_deposits[amount]
@year_card_purchase_count[n]
@year_card_purchase_total[amount]
@top_spend_month[YYYY-MM]
@year_total_fees[amount]
@netflix_charge_count[n]
@dec_ending_balance[amount]
where amount is a float with two decimals, n is an integer, and the month is like 2025-12.
```
