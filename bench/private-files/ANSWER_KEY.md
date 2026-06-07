# Private files — answer key

Computed by `generate.py` against the exact files in each subfolder (seeded — regenerating reproduces files + answers identically). Each gold was also cross-checked with the task's *native* tool (`pdftotext`, `sqlite3`, `jq`, `mailbox`). Grade `@key[value]` lines; don't put these in the prompt.

| Task | Format / tool | Keys (gold) |
|---|---|---|
| **S1** | SQLite / SQL | `@top_category[Utilities]`, `@top_category_q4_spend[1564.37]`, `@q4_txn_count[46]` |
| **J1** | nested JSON / json·jq | `@grand_total[8700.61]`, `@top_item_by_qty[Notebook]`, `@orders_over_100[31]` |
| **M1** | mbox / email+regex | `@order_email_count[22]`, `@total_spent[2658.02]`, `@top_merchant[ShopB]` |
| **X1** | XML / ElementTree | `@total_steps_october[289702]`, `@days_over_10k[15]`, `@avg_resting_hr[62.5]` |
| **W1** | WhatsApp txt / regex | `@msgs_alice[60]`, `@msgs_me[80]`, `@top_sender[Me]`, `@dinner_mentions[25]`, `@busiest_day[05/05/25]` |
| **P1** | PDF / pdftotext | `@out_of_range_count[5]`, `@ldl_value[168]` |
| **Z1** | zip / zipfile+csv+json | `@total_orders[3349.08]`, `@total_refunds[166.73]`, `@net_spend[3182.35]` |

## What each task actually probes

- **S1** — must read the schema first, then **JOIN** txns→categories and filter Q4 by a string-month substring. A model that ignores the categories table (reports `category_id` numbers) or forgets the join fails the name.
- **J1** — two-level nesting: per-order totals are themselves sums over an items array. Top-item is a *global* qty aggregation across orders, not within one order. `jq` or a nested Python loop both work.
- **M1** — must filter by Subject (`Your order`), skipping the ~30% noise emails, then regex two fields out of each body. Summing every email or grabbing the wrong line breaks it.
- **X1** — two record *types* share one tag; must filter by the `type` attribute. Step total vs the ≥10k day-count are different reductions over the same records.
- **W1** — one regex over a semi-structured log; the trap is multi-field extraction (date, sender, text) from one line and a per-day histogram for the busiest day.
- **P1** — the real test of "different tool": **no PDF Python lib exists**, so the agent must discover/`pdftotext` it via the shell, then parse the layout text. A model that only tries `import pypdf` and gives up fails.
- **Z1** — open an archive and read **two different formats** (CSV + JSON) from inside it, then combine. Tests not extracting-to-disk-blindly but reading members and joining.

## Notes
- All data is **synthetic**, seeded `np.random.default_rng(7)`. Safe to commit/share — no real PII. The PDF is hand-built (no external lib) and reads cleanly with poppler's `pdftotext`.
- This suite is the **format/tool axis**; `private-tasks/` is the same private domains on CSV (analysis axis); `dabench-mini` / `dabench-hard` are the academic-benchmark axis.
- Everything here runs with the stock toolchain on this machine (stdlib + `pdftotext`/`sqlite3`/`jq`). The only format that would need an install is **xlsx** (`pip install openpyxl`) — say the word and I'll add an Excel task as a bonus.

---

# Realistic documents — hard tier (R1–R4)

Built by `generate_real.py`; files are laid out **exactly like real Chase statements / OFX downloads / Apple Health exports** (synthetic data, real format). Every gold below is **independently re-derived from the rendered files** by `verify_real.py` (pdftotext+regex for PDFs, regex SGML for OFX, ElementTree for XML) — not just trusted from the generator. Run `python3 bench/private-files/verify_real.py` → it prints a gold-vs-from-file table and exits `ALL OK ✓`.

| Task | Format / tool | Keys (gold) |
|---|---|---|
| **R1** | Chase checking PDF / `pdftotext -layout` | `@ending_balance[7965.76]`, `@card_purchase_count[21]`, `@card_purchase_total[1049.06]`, `@recurring_count[2]`, `@largest_electronic_withdrawal[1204.55]` |
| **R2** | Chase Sapphire PDF / `pdftotext -layout` | `@new_balance[1417.96]`, `@purchase_count[14]`, `@total_purchases[1452.16]`, `@largest_purchase[412.40]`, `@amazon_purchases[194.17]` |
| **R3** | OFX/QFX (SGML) / regex | `@transaction_count[33]`, `@credit_count[4]`, `@debit_count[29]`, `@total_debits[3223.15]`, `@ledger_balance[7965.76]` |
| **R4** | Apple Health XML / ElementTree | `@watch_total_steps[187774]`, `@days_over_10k[7]`, `@avg_resting_hr[56.3]`, `@total_asleep_hours[148.0]`, `@running_distance_km[35.8]` |
| **R5** | 12 monthly checking PDFs (2–3 pages each, 64–85 txns/mo) / `pdftotext -layout` ×12 | `@year_total_deposits[109428.33]`, `@year_card_purchase_count[755]`, `@year_card_purchase_total[55354.56]`, `@top_spend_month[2025-12]`, `@year_total_fees[3.00]`, `@netflix_charge_count[12]`, `@dec_ending_balance[21780.04]` |
| **W2** | corpus of 50 chats, 10 MB–1 GB (10.78 GB total) / `grep -rl`·`wc`·`du` | `@group_count[50]`, `@total_messages[263013454]`, `@largest_group_file[49_dog_park_regulars.txt]`, `@total_dinner_mentions[32876080]`, `@gate_code[7392]`, `@gate_code_file[16_class_of_2015.txt]`, `@flight_number[DL 1474]`, `@flight_file[33_bridal_party.txt]` (default `--groups 50 --min-mb 10 --max-gb 1 --seed 20260606`) |

(Grade numerically: e.g. `412.40` == `412.4`. The `[1m]`/two-decimal forms above match what the prompt asks the agent to print.)

## What each task actually probes (and the trap that fails a sloppy agent)

- **R1 (checking)** — the authentic Chase Total Checking layout has **no running-balance column** and splits activity into named subsections. The trap: the `ATM & Debit Card Withdrawals` summary line (`-1,149.06`) and subsection lump **card purchases together with a $100 ATM withdrawal**; the question asks for *card purchases only* (`1,049.06` / 21 rows), so an agent that copies the summary total or counts the ATM row fails. Also tests **wrapped ACH descriptions** (a second physical line with no amount) and that `largest_electronic_withdrawal` is found by scanning the *Electronic* subsection (it's the `$1,204.55` Chase Credit Crd Epay), not the bigger card/ATM numbers.
- **R2 (credit card)** — splits `PAYMENTS AND OTHER CREDITS` vs `PURCHASE`, and must **reconcile** New Balance = Previous + Purchases − Payments,Credits. The trap: an **Amazon refund** (`AMZN MKTP US*RF… −34.20`) sits in credits carrying the merchant name, so `amazon_purchases` (`194.17` = the two `AMZN MKTP` *purchases*) must exclude it; counting it (or counting the `Payment Thank You` as a purchase) fails.
- **R3 (OFX/QFX)** — the real "recognize the format, improvise the tool" test: it's **SGML, not XML** (leaf tags like `<TRNAMT>-15.49` have no closing tag), and **no OFX library is installed**, so `import ofxparse` / XML parsers choke — the agent must regex it. Tests sign-based credit/debit classification and reading `LEDGERBAL`.
- **R4 (Apple Health)** — a large, real-shaped export (~620 records). The headline trap is **multi-source double-counting**: `iPhone` and `Apple Watch` both log `StepCount` over overlapping windows, so a naive sum (`watch + iPhone`) is far too high — the agent must filter to `Apple Watch`. Also tests the **non-ISO datetime** (`2025-10-01 23:59:00 -0700`), **per-day aggregation** for the 10k-day count, **sleep-stage value filtering** with duration math (asleep = Core+Deep+REM, excluding InBed/Awake), and a **workout-type filter** (Running only — Yoga workouts are present as noise).
- **R5 (a year of statements)** — the **multi-document** test: 12 separate monthly PDFs that must be discovered, parsed, and **aggregated across the year**. Balances chain (each Beginning = prior Ending), so `dec_ending_balance` only falls out if every month parsed correctly; `top_spend_month` (`2025-12`, the holiday bump) requires a per-file subtotal then an argmax; `netflix_charge_count` (`12`) checks the agent found the recurring charge in *all* twelve files; and the R1 card-vs-ATM trap recurs in every statement. An agent that reads only one or two files fails.
- **W2 (chat corpus)** — the **scale + many-files** test: 50 separate chat exports totaling ~10.8 GB / 263M messages, sizes log-spread from 10 MB to ~1 GB. Several files individually exceed any context window, so the agent must work **across files with streaming tools** — `ls -S`/`du` for the largest, `wc -l` summed (minus one banner line per file) for `total_messages`, `grep -ic` for `total_dinner_mentions`, and crucially `grep -rl` to find that the `gate code` (`7392`) and the `flight` (`DL 1474`) each live in **exactly one** of the 50 chats (`16_class_of_2015.txt` and `33_bridal_party.txt`). Reading `manifest.json`/`INDEX.md` is cheating — they're the answer key. An agent that tries to open the big files, or that only checks a few, fails.

## Realism notes

- **R1 and R3 are the same account, same 33 transactions** — one rendered as the PDF statement, one as the QFX download (exactly as a bank lets you export the same period two ways). `R1_ending_balance` == `R3_ledger_balance` (`7965.76`) by construction; a cross-document eval can check they agree.
- The checking statement has a `Chase Credit Crd Epay` of `−1,204.55` and the Sapphire shows a `Payment Thank You - Web` of `−1,457.32` — **deliberately different amounts**, so a model can't shortcut by assuming "the card payment on the checking account equals the payment on the card statement."
- Header/wording/section labels were taken from real redacted Chase statements, the OFX 1.x SGML spec, and the Apple Health DTD (see `generate_real.py` header). All names, addresses, account numbers, and amounts are fake; the Chase CA routing number `322271627` in the OFX is public bank info, not PII.
- These read cleanly with `pdftotext -layout`; **plain `pdftotext` (no -layout) scrambles the columns** on the statements (date/description/amount land on separate lines), which is itself realistic — the prompts tell the agent to use `-layout`.
- **R5** comes from the same `generate_real.py` (seed `2025` for the year series) and is re-verified by `verify_real.py` exactly like R1–R4; the 12 PDFs live in `finance/statements_2025/` with balances that chain Jan→Dec.
- **W2 is a generated corpus, git-ignored** (the whole `messages/group_chats/` dir — it's ~10.8 GB). Build it with `python3 bench/private-files/generate_chats.py` (~8 min, 50 files + `manifest.json` + `INDEX.md`); the generator prints the corpus gold and **self-verifies** by streaming a sample of files (incl. the ~1 GB one) back from disk. The gold above is for the default params (`--groups 50 --min-mb 10 --max-gb 1 --seed 20260606`); the needles and which file holds them are fixed by construction (gate → file index ⌊N/3⌋, flight → ⌊2N/3⌋), while `total_messages`/`total_dinner_mentions`/`largest_group_file` follow deterministically from the params — `manifest.json` always holds the exact gold for whatever was built. Scale down for quick runs, e.g. `--groups 12 --max-gb 0.05`. (A single-file variant, `generate_chat.py` → `group_chat.txt`, still exists for the one-big-file case.)
