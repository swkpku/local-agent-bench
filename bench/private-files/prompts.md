# Private files — multi-format, multi-tool prompts

7 private-domain tasks, each in a **different file format** that forces a **different tool** — the point is no longer "can it pandas a CSV" but "can it recognize the format, reach for the right tool, extract, and reason." All data is synthetic + seeded (`generate.py`), answers are exact-match gradable.

Everything here parses with what's already on this machine — no `pip install`:

| Task | File | Format | Natural tool |
|---|---|---|---|
| **S1** | `finance/personal.db` | SQLite | SQL (`sqlite3` / `pandas.read_sql`) |
| **J1** | `shopping/orders.json` | nested JSON | `json` / `jq` |
| **M1** | `email/inbox.mbox` | mbox mailbox | `mailbox`+`email` + regex |
| **X1** | `health/export.xml` | Apple-Health XML | `xml.etree.ElementTree` |
| **W1** | `messages/chat.txt` | WhatsApp text | regex / `awk` |
| **P1** | `labs/lab_report.pdf` | PDF | `pdftotext` CLI (poppler) |
| **Z1** | `export/takeout.zip` | zip (csv+json) | `zipfile` + csv/json |

Paths assume you start the agent in `/Users/bobscott/Documents/github/localAI`. Grade `@key[value]` against `ANSWER_KEY.md`.

---

## S1 — SQLite, query with SQL
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

## J1 — nested JSON
```text
You are a data agent. The file below is JSON with nested arrays. Inspect its structure first, then answer. Follow constraints exactly; output each answer line in the exact format.

File: /Users/bobscott/Documents/github/localAI/bench/private-files/shopping/orders.json
Question: Across all my orders, what did I spend in total, which item did I order the most units of, and how many orders had a total over $100?
Constraints: The JSON has {"orders": [ {items: [{name, qty, price}, ...]}, ... ]}. An order's total is the sum of qty*price over its items. Grand total = sum of all order totals (round to 2 decimals). Top item = the item name with the greatest total qty summed across every order. Count orders whose order total is strictly greater than 100.
Answer format: @grand_total[amount]
@top_item_by_qty[name]
@orders_over_100[n]
where amount is a float with two decimals, name is the item string, n is an integer.
```

## M1 — mbox email + regex
```text
You are a data agent. The file below is an mbox mailbox of emails. Parse it (e.g. Python's mailbox/email module). Follow constraints exactly; output each answer line in the exact format.

File: /Users/bobscott/Documents/github/localAI/bench/private-files/email/inbox.mbox
Question: How many order-confirmation emails did I get, how much did I spend in total, and which merchant did I spend the most at?
Constraints: An order-confirmation email is one whose Subject contains the phrase 'Your order'. Ignore all other emails. In each order email's body there is a line 'Order total: $<amount>' and a line 'Merchant: <name>' — extract them. Count the order emails, sum the totals (2 decimals), and report the merchant with the highest summed total.
Answer format: @order_email_count[n]
@total_spent[amount]
@top_merchant[name]
where n is an integer, amount is a float with two decimals, name is the merchant string.
```

## X1 — Apple-Health XML
```text
You are a data agent. The file below is an Apple Health export (XML). Parse it (e.g. xml.etree.ElementTree). Follow constraints exactly; output each answer line in the exact format.

File: /Users/bobscott/Documents/github/localAI/bench/private-files/health/export.xml
Question: For October 2025, what were my total steps, on how many days did I hit 10,000+ steps, and what was my average resting heart rate?
Constraints: Records are <Record type="..." startDate="YYYY-MM-DD ..." value="..."/>. Step records have type HKQuantityTypeIdentifierStepCount (one per day); resting HR records have type HKQuantityTypeIdentifierRestingHeartRate (one per day). Sum step values for total steps. Count days where the day's step value >= 10000. Average all resting-HR values and round to one decimal.
Answer format: @total_steps_october[n]
@days_over_10k[n]
@avg_resting_hr[v]
where the n values are integers and v is a number with one decimal.
```

## W1 — WhatsApp text + regex
```text
You are a data agent. The file below is a WhatsApp chat export (plain text). Parse each line with a regex. Follow constraints exactly; output each answer line in the exact format.

File: /Users/bobscott/Documents/github/localAI/bench/private-files/messages/chat.txt
Question: In this chat, how many messages did Alice send, how many did I (Me) send, who sent more, how many messages mention 'dinner', and which calendar day had the most messages?
Constraints: Each message line looks like 'MM/DD/YY, HH:MM - Sender: text'. Count messages per sender. 'dinner' match is case-insensitive substring of the message text. Busiest day = the MM/DD/YY date that appears on the most message lines (report it exactly as it appears, e.g. 05/05/25).
Answer format: @msgs_alice[n]
@msgs_me[n]
@top_sender[name]
@dinner_mentions[n]
@busiest_day[date]
where the n values are integers, name is the sender string, date is MM/DD/YY.
```

## P1 — PDF (lab report)
```text
You are a data agent. The file below is a PDF lab report. You do not have a PDF Python library, but the `pdftotext` command (poppler) is installed — use it (e.g. run `pdftotext -layout <file> -`) to get the text, then parse. Follow constraints exactly; output each answer line in the exact format.

File: /Users/bobscott/Documents/github/localAI/bench/private-files/labs/lab_report.pdf
Question: How many lab results on this report are flagged out of range, and what is my LDL Cholesterol value?
Constraints: Each result line shows a test name, its value, a reference range 'ref LO-HI', and a flag of 'HIGH' or 'LOW' when out of range. Count the results flagged HIGH or LOW. Also read the LDL Cholesterol value.
Answer format: @out_of_range_count[n]
@ldl_value[v]
where n is an integer and v is the LDL number.
```

## Z1 — zip archive (csv + json inside)
```text
You are a data agent. The file below is a zip archive containing more than one file in different formats. Open it (e.g. Python's zipfile) and read the members without extracting to disk if you can. Follow constraints exactly; output each answer line in the exact format.

File: /Users/bobscott/Documents/github/localAI/bench/private-files/export/takeout.zip
Question: Inside the archive there is an orders CSV and a refunds JSON. What did I spend on orders, how much was refunded, and what is my net spend?
Constraints: orders.csv has columns date,merchant,amount — sum the amount column for total orders. refunds.json has {"refunds":[{...,"amount":...}]} — sum those amounts for total refunds. Net spend = total orders minus total refunds. Round each to two decimals.
Answer format: @total_orders[amount]
@total_refunds[amount]
@net_spend[amount]
where each amount is a float with two decimals.
```

---

# Realistic documents — hard tier

These tasks use files laid out **exactly like the real thing** (faithful to actual Chase statements, OFX/QFX downloads, and Apple Health exports — data is synthetic, only the format is real; see `generate_real.py` and `generate_chat.py`). They carry the **real-world traps** that separate a careful agent from a sloppy one, so they pressure-test extraction and reasoning at scale, not just tool choice. R1–R5 are exact-match gradable against `ANSWER_KEY.md`; verify their gold yourself with `python3 bench/private-files/verify_real.py` (it re-derives every answer straight from the files). W2's gold is printed (and self-verified) by `generate_chat.py`.

| Task | File | Format | Natural tool | The trap |
|---|---|---|---|---|
| **R1** | `finance/chase_checking_statement.pdf` | Chase checking PDF | `pdftotext -layout` | summary mixes card + ATM; wrapped ACH lines |
| **R2** | `finance/chase_sapphire_statement.pdf` | Chase credit-card PDF | `pdftotext -layout` | refund hides in credits, not purchases |
| **R3** | `finance/activity_download.qfx` | OFX/QFX (SGML) | regex / manual SGML | unclosed leaf tags; no OFX lib |
| **R4** | `health/apple_health_export.xml` | Apple Health XML | `ElementTree` / `iterparse` | two sources double-count steps |
| **R5** | `finance/statements_2025/` (12 PDFs) | a full year of statements | `pdftotext -layout` ×12 | discover, parse & aggregate across 12 files |
| **W2** | `messages/group_chats/` (50+ files, 10 MB–1 GB) | corpus of WhatsApp chats | `grep -rl` / `wc` / `du` / streaming | dozens of files, several too big to open; needle lives in ONE chat |

## R1 — Chase checking statement (PDF)
```text
You are a data agent. The file below is a PDF bank statement (Chase Total Checking). You do not have a PDF Python library, but the `pdftotext` command (poppler) is installed — run `pdftotext -layout <file> -` to get column-aligned text, then parse. (Plain `pdftotext` without -layout scrambles the columns on this statement.) Follow constraints exactly; output each answer line in the exact format, nothing else.

File: /Users/bobscott/Documents/github/localAI/bench/private-files/finance/chase_checking_statement.pdf
Question: From this statement, what is the ending balance, how many debit-card purchases did I make and what did they total, how many of those were recurring, and what was my single largest electronic withdrawal?
Constraints: The statement has a CHECKING SUMMARY and then transaction subsections: DEPOSITS AND ADDITIONS, ATM & DEBIT CARD WITHDRAWALS, ELECTRONIC WITHDRAWALS, FEES. Each detail row is 'MM/DD  DESCRIPTION  AMOUNT' and withdrawals are negative. Some long descriptions wrap onto a second line that has no amount — that continuation belongs to the row above it.
- ending_balance: the Ending Balance shown in CHECKING SUMMARY (it equals Beginning Balance plus every detail amount). Report as a number with two decimals, no $ or commas.
- card_purchase_count and card_purchase_total: count and sum ONLY rows in ATM & DEBIT CARD WITHDRAWALS whose description contains 'Card Purchase' (that includes 'Recurring Card Purchase' and 'Card Purchase With Pin'). Do NOT include the 'ATM Withdrawal' row — it sits in the same subsection but is not a card purchase. Report the total as a positive number with two decimals. (The subsection's own summary total is larger because it also includes the ATM withdrawal — do not just copy it.)
- recurring_count: of those card purchases, how many descriptions contain 'Recurring Card Purchase'.
- largest_electronic_withdrawal: the largest single amount, by absolute value, in the ELECTRONIC WITHDRAWALS subsection, as a positive number with two decimals.
Answer format: @ending_balance[amount]
@card_purchase_count[n]
@card_purchase_total[amount]
@recurring_count[n]
@largest_electronic_withdrawal[amount]
where amount is a float with two decimals and n is an integer.
```

## R2 — Chase Sapphire credit-card statement (PDF)
```text
You are a data agent. The file below is a PDF credit-card statement (Chase Sapphire Preferred). Use `pdftotext -layout <file> -` (poppler) to get the text, then parse. Follow constraints exactly; output each answer line in the exact format, nothing else.

File: /Users/bobscott/Documents/github/localAI/bench/private-files/finance/chase_sapphire_statement.pdf
Question: What is my New Balance, how many purchases did I make and what did they total, what was my largest single purchase, and how much did I spend at Amazon?
Constraints: ACCOUNT ACTIVITY is split into two subsections: PAYMENTS AND OTHER CREDITS (negative amounts — a payment plus any refunds/returns) and PURCHASE (positive amounts). Each row is 'MM/DD  DESCRIPTION  AMOUNT'.
- new_balance: the New Balance in ACCOUNT SUMMARY (= Previous Balance + Purchases − Payment,Credits; Fees and Interest are 0). Number, two decimals, no $ or commas.
- purchase_count and total_purchases: count and sum ONLY rows in the PURCHASE subsection.
- largest_purchase: the largest single amount in the PURCHASE subsection.
- amazon_purchases: the summed PURCHASE amount whose description contains 'AMZN' or 'AMAZON'. IMPORTANT: there is also an Amazon refund in PAYMENTS AND OTHER CREDITS — that is a credit, not a purchase, so do NOT count it.
Answer format: @new_balance[amount]
@purchase_count[n]
@total_purchases[amount]
@largest_purchase[amount]
@amazon_purchases[amount]
where amount is a float with two decimals and n is an integer.
```

## R3 — Bank OFX/QFX download (SGML)
```text
You are a data agent. The file below is a bank transaction download in OFX/QFX format. This is SGML (Open Financial Exchange 1.x), NOT XML: 'leaf' tags have NO closing tag — e.g. `<TRNAMT>-15.49` ends where the next tag begins — while container tags like `<STMTTRN>...</STMTTRN>` do close. There is no OFX library installed (don't try `pip install`), so parse it yourself with regex or manual SGML handling. Follow constraints exactly; output each answer line in the exact format, nothing else.

File: /Users/bobscott/Documents/github/localAI/bench/private-files/finance/activity_download.qfx
Question: How many transactions are in this download, how many are credits versus debits, what is the total of all debits, and what is the ledger balance?
Constraints: Each transaction is a <STMTTRN> block containing a <TRNAMT> amount. Deposits/credits are positive; withdrawals/debits are negative.
- transaction_count: number of <STMTTRN> records.
- credit_count and debit_count: classify each transaction by the sign of its <TRNAMT> (positive = credit, negative = debit).
- total_debits: the sum of the debit amounts, reported as a positive number with two decimals.
- ledger_balance: the <BALAMT> inside <LEDGERBAL> (the statement ending balance), two decimals.
Answer format: @transaction_count[n]
@credit_count[n]
@debit_count[n]
@total_debits[amount]
@ledger_balance[amount]
where n is an integer and amount is a float with two decimals.
```

## R4 — Apple Health export (large XML, multi-source)
```text
You are a data agent. The file below is a real-shaped Apple Health export (XML, hundreds of records). It is large, so prefer a streaming parser (xml.etree.ElementTree.iterparse). Datetimes are formatted like '2025-10-01 23:59:00 -0700' (space-separated, with a signed offset — NOT ISO-8601). Follow constraints exactly; output each answer line in the exact format, nothing else.

File: /Users/bobscott/Documents/github/localAI/bench/private-files/health/apple_health_export.xml
Question: For this export, what were my total Apple Watch steps, on how many days did I hit 10,000+ steps, my average resting heart rate, my total time asleep, and my total running distance?
Constraints: Step records are <Record type="HKQuantityTypeIdentifierStepCount" ...> in intraday buckets. They are logged by TWO sources — an 'iPhone' and an 'Apple Watch' — whose records OVERLAP in time and double-count. Use ONLY records whose sourceName contains 'Apple Watch'. (Summing every step record double-counts and is wrong.)
- watch_total_steps: the integer sum of value over Apple Watch step records.
- days_over_10k: group Apple Watch step records by the date part of startDate, sum each day's values, and count the days whose total is >= 10000.
- avg_resting_hr: the average of value over <Record type="HKQuantityTypeIdentifierRestingHeartRate" ...>, to one decimal.
- total_asleep_hours: over <Record type="HKCategoryTypeIdentifierSleepAnalysis" ...> whose value is HKCategoryValueSleepAnalysisAsleepCore, HKCategoryValueSleepAnalysisAsleepDeep, or HKCategoryValueSleepAnalysisAsleepREM (exclude InBed and Awake), sum (endDate − startDate) and report total hours to one decimal.
- running_distance_km: sum the totalDistance attribute over <Workout workoutActivityType="HKWorkoutActivityTypeRunning" ...> elements (exclude other workout types such as Yoga), to one decimal.
Answer format: @watch_total_steps[n]
@days_over_10k[n]
@avg_resting_hr[v]
@total_asleep_hours[v]
@running_distance_km[v]
where n is an integer and v is a number with one decimal.
```

## R5 — A full year of monthly checking statements (12 PDFs)
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

## W2 — A corpus of 50+ group chats (10 MB–1 GB each, needle in ONE)
```text
You are a data agent. The folder below holds a CORPUS of 50+ WhatsApp group-chat exports whose file sizes range from ~10 MB to ~1 GB. Several are FAR too big to open or read into context — work across the files with streaming tools only (grep, grep -rl, wc -l, awk, sort, du, find), never by loading a whole file. Each chat is an NN_slug.txt file; within it, every message line is 'MM/DD/YY, HH:MM - Sender: text' and the first line is a system 'end-to-end encrypted' banner (NOT a message). Follow constraints exactly; output each answer line in the exact format, nothing else.

Folder: /Users/bobscott/Documents/github/localAI/bench/private-files/messages/group_chats/
(If the folder is empty, create it with: python3 bench/private-files/generate_chats.py — and do NOT read manifest.json or INDEX.md; those are the answer key.)
Question: How many group chats are there, how many messages in total across all of them, which chat file is the largest, how many messages across the whole corpus mention dinner, and — these one-off facts each appear in exactly ONE chat — what is the cabin gate code (and which file holds it) and the flight number someone booked (and which file)?
Constraints:
- Consider only the NN_*.txt chat files; ignore manifest.json and INDEX.md.
- group_count: the number of chat .txt files.
- total_messages: total real message lines across all chat files, i.e. the sum over files of (line_count - 1) to drop each file's banner line.
- largest_group_file: the chat .txt filename with the most bytes.
- total_dinner_mentions: total message lines across all files whose text contains 'dinner' (case-insensitive).
- gate_code and gate_code_file: search the corpus for 'gate code' — it occurs in exactly one file; report the numeric code and that file's name.
- flight_number and flight_file: search for 'flight' — it occurs in exactly one file; report it like 'DL 1474' and that file's name.
Answer format: @group_count[n]
@total_messages[n]
@largest_group_file[filename]
@total_dinner_mentions[n]
@gate_code[code]
@gate_code_file[filename]
@flight_number[value]
@flight_file[filename]
where n is an integer, filename is like 49_dog_park_regulars.txt, and code/value are strings.
```
