#!/usr/bin/env python3
"""
Generate REALISTIC private-domain documents that look like the real thing
(faithful to actual Chase statements, OFX/QFX downloads, and Apple Health
exports) and compute verified gold answers in the same pass. Seeded ->
reproducible. All data is synthetic; only the *format* is real.

This is the "hard" tier of bench/private-files. Each file is laid out exactly
like its real-world counterpart -- with the real traps that break a sloppy
agent -- so it pressure-tests format recognition, tool choice, careful
extraction, and multi-step reasoning, not just "can it pandas a CSV".

  Chase Total Checking statement (PDF) -> pdftotext + parse  finance/chase_checking_statement.pdf
  Chase Sapphire credit-card stmt (PDF)-> pdftotext + parse  finance/chase_sapphire_statement.pdf
  Bank OFX/QFX download (SGML)         -> regex / manual SGML finance/activity_download.qfx
  Apple Health export (large XML)      -> ElementTree/iterparse health/apple_health_export.xml

Real-world traps baked in (these are the point):
  * Checking has NO running-balance column and is split into named subsections;
    the "ATM & Debit Card Withdrawals" group mixes card purchases with ATM
    withdrawals, and some ACH lines wrap onto a second physical line.
  * Credit card splits PAYMENTS AND OTHER CREDITS vs PURCHASE; an Amazon REFUND
    sits in credits carrying the merchant name (must NOT be counted as spend).
  * OFX 1.x is SGML, not XML: leaf tags have no closing tag. No ofx lib is
    installed, so the agent must regex it. Debits are negative, credits positive.
  * Apple Health logs steps from TWO sources (iPhone + Apple Watch) with
    overlapping windows -> naive summing double-counts. Sleep is per-stage
    records; datetimes are 'YYYY-MM-DD HH:MM:SS -0700' (not ISO-8601).

Run:  python3 bench/private-files/generate_real.py
Needs only the stdlib + numpy. The PDFs read cleanly with poppler's pdftotext.
"""
import os, json, calendar
from datetime import datetime, timedelta
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
G = {}  # gold answers


def d(sub):
    p = os.path.join(BASE, sub); os.makedirs(p, exist_ok=True); return p


def money(x):
    """1234.5 -> '1,234.50' ; -12.0 -> '-12.00' (accounting, sign kept)."""
    return ("-" if x < 0 else "") + f"{abs(x):,.2f}"


def usd(x):
    """Signed amount with a $ sign, e.g. -$12.00 / $6,978.36."""
    return ("-$" if x < 0 else "$") + f"{abs(x):,.2f}"


# =====================================================================
# Multi-page PDF writer (Courier monospace so pdftotext -layout keeps columns)
# =====================================================================
def make_pdf(path, pages, font_size=8.4, leading=10.4, left=33, top=760):
    """pages: list[list[str]] -- one list of text lines per page."""
    def esc(s):
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    n = len(pages)
    font_obj = 3 + 2 * n
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(n))
    objs = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: ("<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, n)).encode(),
        font_obj: b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
    }
    for i, lines in enumerate(pages):
        page_obj, content_obj = 3 + 2 * i, 4 + 2 * i
        c = "BT /F1 %.2f Tf %.2f TL 1 0 0 1 %d %d Tm\n" % (font_size, leading, left, top)
        for j, ln in enumerate(lines):
            c += ("(%s) Tj\n" % esc(ln)) if j == 0 else ("T* (%s) Tj\n" % esc(ln))
        c += "ET"
        cb = c.encode("latin-1", "replace")
        objs[page_obj] = ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                          "/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>"
                          % (font_obj, content_obj)).encode()
        objs[content_obj] = b"<< /Length %d >>\nstream\n" % len(cb) + cb + b"\nendstream"
    out = b"%PDF-1.4\n"
    offs = {}
    for num in range(1, font_obj + 1):
        offs[num] = len(out)
        out += b"%d 0 obj\n" % num + objs[num] + b"\nendobj\n"
    xref = len(out)
    total = font_obj + 1
    out += b"xref\n0 %d\n0000000000 65535 f \n" % total
    for num in range(1, font_obj + 1):
        out += b"%010d 00000 n \n" % offs[num]
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (total, xref)
    with open(path, "wb") as f:
        f.write(out)


def paginate(lines, per_page, footer_prefix):
    chunks = [lines[i:i + per_page] for i in range(0, len(lines), per_page)] or [[]]
    m = len(chunks)
    return [c + ["", f"{footer_prefix}  Page {i + 1} of {m}"] for i, c in enumerate(chunks)]


# =====================================================================
# 1) CHASE TOTAL CHECKING statement  (shared transactions feed the OFX too)
# =====================================================================
YEAR, MON = 2025, 8
LAST = calendar.monthrange(YEAR, MON)[1]            # 31
PERIOD = f"August 01, {YEAR} through August 29, {YEAR}"
BEGIN_BAL = 4210.55
CARD = "2898"                                       # debit-card last 4

# --- card purchases + ATM (all post to "ATM & Debit Card Withdrawals") -------
# (post_day, kind, "MERCHANT CITY ST", amount)  amount stored positive here
_card = [
    (1,  "Card Purchase",          "Whole Foods Mkt Oakland CA", 86.32),
    (2,  "Recurring Card Purchase", "Netflix.com 866-579-7172 CA", 15.49),
    (3,  "Card Purchase",          "Starbucks 0421 Oakland CA",  6.85),
    (4,  "Card Purchase",          "Chevron 0099 Emeryville CA", 52.17),
    (5,  "Recurring Card Purchase", "Spotify USA 877-778-1161 NY", 11.99),
    (6,  "Card Purchase With Pin", "Costco Whse 0444 Richmond CA", 214.66),
    (7,  "Card Purchase",          "Chipotle 1492 Oakland CA",   13.45),
    (8,  "Card Purchase",          "Amazon.com A12bc Amzn WA",   39.99),
    (9,  "Card Purchase",          "Trader Joes 553 Berkeley CA", 64.21),
    (11, "Card Purchase",          "Shell Oil 5742 Oakland CA",  48.73),
    (12, "ATM Withdrawal",         "1455 Broadway Oakland CA",   100.00),
    (13, "Card Purchase",          "Doordash Sf Ca",             31.20),
    (14, "Card Purchase",          "Target 1842 Emeryville CA",  78.44),
    (15, "Card Purchase",          "Sq Blue Bottle Oakland CA",  9.50),
    (17, "Card Purchase",          "Amazon.com B98zy Amzn WA",   122.37),
    (19, "Card Purchase",          "Safeway 1234 Oakland CA",    53.88),
    (20, "Card Purchase",          "Apple.com/Bill 866-712 CA",  2.99),
    (21, "Card Purchase",          "Uber Trip Help.uber.com CA", 27.65),
    (23, "Card Purchase",          "Walgreens 1023 Oakland CA",  18.42),
    (25, "Card Purchase",          "Whole Foods Mkt Oakland CA", 91.05),
    (26, "Card Purchase",          "Chipotle 1492 Oakland CA",   14.90),
    (28, "Card Purchase",          "Chevron 0099 Emeryville CA", 44.80),
]

# --- electronic withdrawals (ACH bill-pay, transfers, Zelle, card payment) ---
# (post_day, full_description, amount, ofx_trntype, ofx_name, wrap_at_or_None)
_elec = [
    (1,  "Orig CO Name:Pg&E Orig ID:1234567890 Desc Date:250801 CO Entry "
         "Descr:Utilitybil Sec:Web Ind ID:8841 Ind Name:Jordan Rivera",
         132.55, "DIRECTDEBIT", "PG&E", 62),
    (3,  "Comcast Cable Comm Web Pmt PPD ID: 9876543210",         89.99, "DIRECTDEBIT", "COMCAST"),
    (5,  "Att Payment Web ID: 1112223334",                        75.00, "DIRECTDEBIT", "ATT"),
    (10, "Online Transfer To Sav ...4321 Transaction#: 7901112233", 500.00, "XFER", "ONLINE TRANSFER"),
    (18, "Zelle Payment To Morgan P Jpm88Xyz12",                  60.00, "PAYMENT", "ZELLE MORGAN P"),
    (22, "Chase Credit Crd Epay PPD ID: 4356789012",             1204.55, "PAYMENT", "CHASE CARD EPAY"),
]

# --- deposits and additions --------------------------------------------------
# (post_day, full_description, amount, ofx_trntype, ofx_name, wrap_at_or_None)
_dep = [
    (8,  "Zelle Payment From Jamie Lee Jpm99Abc34",              120.00, "CREDIT", "ZELLE JAMIE LEE"),
    (15, "Orig CO Name:Acme Corp Orig ID:5551234567 Desc Date: CO Entry "
         "Descr:Payroll Sec:PPD Trace#:091000010 Ind ID:0042 Ind Name:Jordan Rivera",
         3204.18, "DIRECTDEP", "ACME CORP PAYROLL", 62),
    (20, "Remote Online Deposit 1",                              450.00, "DEP", "MOBILE DEPOSIT"),
    (29, "Orig CO Name:Acme Corp Orig ID:5551234567 Desc Date: CO Entry "
         "Descr:Payroll Sec:PPD Trace#:091000010 Ind ID:0042 Ind Name:Jordan Rivera",
         3204.18, "DIRECTDEP", "ACME CORP PAYROLL", 62),
]

# --- fees --------------------------------------------------------------------
_fee = [(29, "Monthly Service Fee", 12.00, "FEE", "MONTHLY SERVICE FEE")]


def _wrap(desc, at):
    """Split a long ACH description at the last space <= `at` (real statements wrap)."""
    if at is None or len(desc) <= at:
        return desc, None
    cut = desc.rfind(" ", 0, at)
    return desc[:cut], desc[cut + 1:]


# Build a single canonical transaction list (feeds BOTH the PDF and the OFX).
txns = []
seq = 0
for day, kind, merch, amt in _card:
    seq += 1
    desc = f"{kind}  {MON:02d}/{day:02d}  {merch}  Card {CARD}"
    txns.append(dict(day=day, section="card", desc=desc, amount=-amt,
                     trntype=("ATM" if kind == "ATM Withdrawal" else "POS"),
                     name=merch.rsplit(" ", 1)[0][:32], memo=desc, wrap=None, seq=seq))
for day, desc, amt, tt, nm, *rest in _elec:
    seq += 1
    txns.append(dict(day=day, section="electronic", desc=desc, amount=-amt,
                     trntype=tt, name=nm, memo=desc, wrap=(rest[0] if rest else None), seq=seq))
for day, desc, amt, tt, nm, *rest in _dep:
    seq += 1
    txns.append(dict(day=day, section="deposit", desc=desc, amount=+amt,
                     trntype=tt, name=nm, memo=desc, wrap=(rest[0] if rest else None), seq=seq))
for day, desc, amt, tt, nm in _fee:
    seq += 1
    txns.append(dict(day=day, section="fee", desc=desc, amount=-amt,
                     trntype=tt, name=nm, memo=desc, wrap=None, seq=seq))

SECTION_ORDER = {"deposit": 0, "card": 1, "electronic": 2, "fee": 3}
txns.sort(key=lambda t: (t["day"], SECTION_ORDER[t["section"]], t["seq"]))

ENDING_BAL = round(BEGIN_BAL + sum(t["amount"] for t in txns), 2)


def _sec(name):
    return [t for t in txns if t["section"] == name]


def _sum(name):
    return round(sum(t["amount"] for t in _sec(name)), 2)


# ---- render the checking PDF (authentic Total Checking subsection layout) ----
DW, AW = 70, 14   # description width, amount width in the detail columns


def detail_rows(section):
    rows = []
    for t in section:
        date = f"{t.get('mon', MON):02d}/{t['day']:02d}"
        head, cont = _wrap(t["desc"], t["wrap"])
        rows.append(f"{date:<8}{head:<{DW}.{DW}}{money(t['amount']):>{AW}}")
        if cont:
            rows.append(f"{'':<8}{cont:<{DW}.{DW}}{'':>{AW}}")
    return rows


L = []
L += [
    "JPMorgan Chase Bank, N.A." + " " * 24 + PERIOD,
    "P O Box 182051",
    "Columbus, OH 43218 - 2051" + " " * 22 + "Primary Account: 000000642118293",
    "",
    " " * 48 + "CUSTOMER SERVICE INFORMATION",
    "JORDAN A RIVERA" + " " * 33 + "Web site:            www.Chase.com",
    "1428 ELM ST APT 5" + " " * 31 + "Service Center:      1-800-935-9935",
    "OAKLAND CA 94610-2231" + " " * 27 + "Para Espanol:        1-888-622-4273",
    "",
    "",
    "CHASE TOTAL CHECKING",
    "",
    "CHECKING SUMMARY" + " " * 38 + "INSTANCES" + " " * 12 + "AMOUNT",
    f"{'Beginning Balance':<53}{'':>9}{usd(BEGIN_BAL):>15}",
    f"{'Deposits and Additions':<53}{len(_sec('deposit')):>9}{money(_sum('deposit')):>15}",
    f"{'ATM & Debit Card Withdrawals':<53}{len(_sec('card')):>9}{money(_sum('card')):>15}",
    f"{'Electronic Withdrawals':<53}{len(_sec('electronic')):>9}{money(_sum('electronic')):>15}",
    f"{'Fees':<53}{len(_sec('fee')):>9}{money(_sum('fee')):>15}",
    f"{'Ending Balance':<53}{len(txns):>9}{usd(ENDING_BAL):>15}",
    "",
    "",
]
_HDR = f"{'DATE':<8}{'DESCRIPTION':<{DW}}{'AMOUNT':>{AW}}"
for title, key, tot_label in [
    ("DEPOSITS AND ADDITIONS", "deposit", "Total Deposits and Additions"),
    ("ATM & DEBIT CARD WITHDRAWALS", "card", "Total ATM & Debit Card Withdrawals"),
    ("ELECTRONIC WITHDRAWALS", "electronic", "Total Electronic Withdrawals"),
    ("FEES", "fee", "Total Fees"),
]:
    L += [title, _HDR] + detail_rows(_sec(key))
    L += [f"{tot_label:<{8 + DW}}{usd(_sum(key)):>{AW}}", "", ""]

make_pdf(os.path.join(d("finance"), "chase_checking_statement.pdf"),
         paginate(L, 56, "JORDAN A RIVERA  |  Account 000000642118293"))

# ---- gold: checking ---------------------------------------------------------
card_purchases = [t for t in _sec("card") if "Card Purchase" in t["desc"]]   # excludes ATM Withdrawal
G["R1_ending_balance"] = ENDING_BAL
G["R1_card_purchase_count"] = len(card_purchases)
G["R1_card_purchase_total"] = round(sum(-t["amount"] for t in card_purchases), 2)
G["R1_recurring_count"] = sum(1 for t in _sec("card") if "Recurring Card Purchase" in t["desc"])
G["R1_largest_electronic_withdrawal"] = round(max(-t["amount"] for t in _sec("electronic")), 2)


# =====================================================================
# 2) BANK OFX / QFX download  (same 33 transactions; SGML, unclosed leaf tags)
# =====================================================================
def ofx_dt(day, hh=12):
    return f"{YEAR}{MON:02d}{day:02d}{hh:02d}0000.000[-7:PDT]"


def esc_sgml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


ofx = []
ofx += [
    "OFXHEADER:100", "DATA:OFXSGML", "VERSION:102", "SECURITY:NONE",
    "ENCODING:USASCII", "CHARSET:1252", "COMPRESSION:NONE",
    "OLDFILEUID:NONE", "NEWFILEUID:NONE", "",
    "<OFX>",
    "<SIGNONMSGSRSV1>", "<SONRS>", "<STATUS>", "<CODE>0", "<SEVERITY>INFO", "</STATUS>",
    f"<DTSERVER>{ofx_dt(29, 17)}", "<LANGUAGE>ENG",
    "<FI>", "<ORG>JPMorgan Chase Bank, N.A.", "<FID>10898", "</FI>",
    "<INTU.BID>10898", "</SONRS>", "</SIGNONMSGSRSV1>",
    "<BANKMSGSRSV1>", "<STMTTRNRS>", "<TRNUID>1",
    "<STATUS>", "<CODE>0", "<SEVERITY>INFO", "</STATUS>",
    "<STMTRS>", "<CURDEF>USD",
    "<BANKACCTFROM>", "<BANKID>322271627", "<ACCTID>000000642118293",
    "<ACCTTYPE>CHECKING", "</BANKACCTFROM>",
    "<BANKTRANLIST>", f"<DTSTART>{ofx_dt(1, 0)}", f"<DTEND>{ofx_dt(29, 23)}",
]
for i, t in enumerate(txns, 1):
    fitid = f"{YEAR}{MON:02d}{t['day']:02d}{i:04d}"
    ofx += ["<STMTTRN>", f"<TRNTYPE>{t['trntype']}", f"<DTPOSTED>{ofx_dt(t['day'])}",
            f"<TRNAMT>{t['amount']:.2f}", f"<FITID>{fitid}",
            f"<NAME>{esc_sgml(t['name'])}", f"<MEMO>{esc_sgml(t['memo'])}", "</STMTTRN>"]
ofx += [
    "</BANKTRANLIST>",
    "<LEDGERBAL>", f"<BALAMT>{ENDING_BAL:.2f}", f"<DTASOF>{ofx_dt(29, 17)}", "</LEDGERBAL>",
    "<AVAILBAL>", f"<BALAMT>{ENDING_BAL:.2f}", f"<DTASOF>{ofx_dt(29, 17)}", "</AVAILBAL>",
    "</STMTRS>", "</STMTTRNRS>", "</BANKMSGSRSV1>", "</OFX>",
]
with open(os.path.join(d("finance"), "activity_download.qfx"), "w") as f:
    f.write("\n".join(ofx) + "\n")

# ---- gold: OFX --------------------------------------------------------------
G["R3_transaction_count"] = len(txns)
G["R3_credit_count"] = sum(1 for t in txns if t["amount"] > 0)
G["R3_debit_count"] = sum(1 for t in txns if t["amount"] < 0)
G["R3_total_debits"] = round(sum(-t["amount"] for t in txns if t["amount"] < 0), 2)
G["R3_ledger_balance"] = ENDING_BAL


# =====================================================================
# 3) CHASE SAPPHIRE PREFERRED  credit-card statement (PDF)
# =====================================================================
PREV_BAL = 1457.32
# purchases: (post_mmdd, "DESCRIPTOR", amount)  positive
_purch = [
    ("08/02", "AMZN MKTP US*HT4XY9Z0 AMZN.COM/BILL WA", 64.18),
    ("08/03", "UNITED 0162347654321 800-932-2732 TX",  412.40),
    ("08/05", "TST* TARTINE BAKERY SAN FRANCISCO CA",   38.75),
    ("08/06", "WHOLEFDS OAK 10255 OAKLAND CA",          73.29),
    ("08/08", "SQ *PHILZ COFFEE SAN FRANCISCO CA",       7.50),
    ("08/09", "AMZN MKTP US*B98ZY7QW AMZN.COM/BILL WA", 129.99),
    ("08/11", "DELTA AIR 0062101234567 DELTA.COM GA",    21.00),
    ("08/13", "MARRIOTT MARQUIS SAN FRANCISCO CA",      289.44),
    ("08/15", "TRADER JOES #553 BERKELEY CA",            56.71),
    ("08/17", "UBER *EATS HELP.UBER.COM CA",             42.88),
    ("08/19", "APPLE.COM/BILL 866-712-7753 CA",           9.99),
    ("08/21", "NETFLIX.COM NETFLIX.COM CA",              22.99),
    ("08/24", "COSTCO WHSE #0444 RICHMOND CA",          187.63),
    ("08/27", "VZWRLSS*APOCC VISB 800-922-0204 FL",      95.41),
]
# payments & other credits: (post_mmdd, descriptor, amount)  negative
_credits = [
    ("08/22", "Payment Thank You - Web",               -1457.32),
    ("08/12", "AMZN MKTP US*RF12AB34 AMZN.COM/BILL WA",   -34.20),
]
purch_total = round(sum(a for _, _, a in _purch), 2)
credits_total = round(sum(a for _, _, a in _credits), 2)   # negative
NEW_BAL = round(PREV_BAL + purch_total + credits_total, 2)
CREDIT_LIMIT = 15000.00

S = []
S += [
    "Chase Sapphire Preferred" + " " * 30 + "www.chase.com",
    " " * 54 + "Customer Service 1-800-432-3117",
    "",
    f"JORDAN A RIVERA{' ' * 39}Opening/Closing Date  07/30/25 - 08/29/25",
    "1428 ELM ST APT 5",
    "OAKLAND CA 94610-2231",
    "",
    "ACCOUNT SUMMARY" + " " * 36 + "Account Number: 4147 20XX XXXX 8293",
    f"{'  Previous Balance':<46}{usd(PREV_BAL):>18}",
    f"{'  Payment, Credits':<46}{'-  ' + usd(abs(credits_total)):>18}",
    f"{'  Purchases':<46}{'+  ' + usd(purch_total):>18}",
    f"{'  Cash Advances':<46}{'+  ' + usd(0):>18}",
    f"{'  Balance Transfers':<46}{'+  ' + usd(0):>18}",
    f"{'  Fees Charged':<46}{'+  ' + usd(0):>18}",
    f"{'  Interest Charged':<46}{'+  ' + usd(0):>18}",
    f"{'  New Balance':<46}{usd(NEW_BAL):>18}",
    "",
    f"{'  Credit Limit':<46}{usd(CREDIT_LIMIT):>18}",
    f"{'  Available Credit':<46}{usd(round(CREDIT_LIMIT - NEW_BAL, 2)):>18}",
    f"{'  Minimum Payment Due':<46}{usd(40.00):>18}",
    f"{'  Payment Due Date':<46}{'09/25/25':>18}",
    "",
    "Late Payment Warning: If we do not receive your minimum payment by the date",
    "listed above, you may have to pay a late fee of up to $40.00.",
    "",
    "REWARDS SUMMARY",
    f"{'  Previous points balance':<46}{'24,310':>18}",
    f"{'  Points earned this period':<46}{f'{int(round(purch_total)):,}':>18}",
    "",
    "",
    "ACCOUNT ACTIVITY",
    "",
]
PDW = 60
_PH = f"{'Date':<8}{'Merchant Name or Transaction Description':<{PDW}}{'$ Amount':>12}"
S += ["PAYMENTS AND OTHER CREDITS", _PH]
for mmdd, desc, amt in sorted(_credits):
    S.append(f"{mmdd:<8}{desc:<{PDW}.{PDW}}{money(amt):>12}")
S += ["", "PURCHASE", _PH]
for mmdd, desc, amt in sorted(_purch):
    S.append(f"{mmdd:<8}{desc:<{PDW}.{PDW}}{money(amt):>12}")
S += [
    "", f"{'2025 Totals Year-to-Date':<{8 + PDW}}",
    f"{'  Total fees charged in 2025':<{8 + PDW}}{usd(0):>12}",
    f"{'  Total interest charged in 2025':<{8 + PDW}}{usd(0):>12}",
    "",
    "INTEREST CHARGES",
    f"{'  Purchases':<30}{'21.49%(v)':>14}{usd(0):>14}",
    f"{'  Cash Advances':<30}{'28.49%(v)':>14}{usd(0):>14}",
]
make_pdf(os.path.join(d("finance"), "chase_sapphire_statement.pdf"),
         paginate(S, 56, "Chase Sapphire Preferred  |  Account ...8293"))

# ---- gold: credit card ------------------------------------------------------
def _is_amazon(desc):
    u = desc.upper()
    return "AMZN" in u or "AMAZON" in u


G["R2_new_balance"] = NEW_BAL
G["R2_purchase_count"] = len(_purch)
G["R2_total_purchases"] = purch_total
G["R2_largest_purchase"] = round(max(a for _, _, a in _purch), 2)
G["R2_amazon_purchases"] = round(sum(a for _, desc, a in _purch if _is_amazon(desc)), 2)


# =====================================================================
# 4) APPLE HEALTH export.xml  (large, multi-source, real DTD & datetimes)
# =====================================================================
rng = np.random.default_rng(13)
TZ = "-0700"
H_DAYS = 21                                          # 2025-10-01 .. 2025-10-21
IPHONE = "Jordan's iPhone"
WATCH = "Jordan's Apple Watch"


def hdt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S ") + TZ


recs = []          # list of XML element strings
watch_daily = {}   # day -> watch step total (gold)
resting_vals = []
asleep_minutes_total = 0.0
running_km = 0.0


def record(rtype, source, value, start, end, unit=None, sv="11.0"):
    a = [f'type="{rtype}"', f'sourceName="{source}"', f'sourceVersion="{sv}"']
    if unit is not None:
        a.append(f'unit="{unit}"')
    a += [f'creationDate="{hdt(end)}"', f'startDate="{hdt(start)}"',
          f'endDate="{hdt(end)}"', f'value="{value}"']
    return "  <Record " + " ".join(a) + "/>"


for off in range(H_DAYS):
    day = datetime(2025, 10, 1) + timedelta(days=off)

    # --- steps: Apple Watch (the source of truth) -> hourly buckets 8:00-19:00
    wt = int(np.clip(rng.normal(9200, 3600), 1500, 19000))
    parts = rng.multinomial(wt, [1 / 12] * 12)
    watch_daily[day.date()] = int(parts.sum())
    for h in range(8, 20):
        s = day.replace(hour=h, minute=0, second=0)
        recs.append(record("HKQuantityTypeIdentifierStepCount", WATCH,
                            int(parts[h - 8]), s, s + timedelta(minutes=59, seconds=59), "count"))
    # --- steps: iPhone (overlapping, DIFFERENT values -> double-count trap) ---
    it = int(wt * rng.uniform(0.45, 0.85))
    iparts = rng.multinomial(it, [1 / 8] * 8)
    for k, h in enumerate(range(9, 17)):
        s = day.replace(hour=h, minute=10, second=0)
        recs.append(record("HKQuantityTypeIdentifierStepCount", IPHONE,
                            int(iparts[k]), s, s + timedelta(minutes=49), "count",
                            sv="18.0.1"))

    # --- resting HR: one per day (Apple Watch) ---
    hr = int(round(np.clip(rng.normal(58, 4), 45, 80)))
    resting_vals.append(hr)
    s = day.replace(hour=23, minute=50, second=0)
    recs.append(record("HKQuantityTypeIdentifierRestingHeartRate", WATCH, hr,
                        day.replace(hour=0, minute=0, second=0), s, "count/min"))

    # --- active energy: a few per day (noise) ---
    for _ in range(3):
        h = int(rng.integers(7, 22))
        s = day.replace(hour=h, minute=int(rng.integers(0, 59)), second=0)
        recs.append(record("HKQuantityTypeIdentifierActiveEnergyBurned", WATCH,
                            round(float(rng.uniform(2, 120)), 3), s, s + timedelta(minutes=1), "kcal"))

    # --- sleep: stages as separate records (asleep = Core+Deep+REM) ----------
    asleep = float(np.clip(rng.normal(415, 40), 280, 520))           # minutes asleep
    core, deep, rem = asleep * 0.55, asleep * 0.18, asleep * 0.27
    awake = float(rng.uniform(8, 28))
    asleep_minutes_total += core + deep + rem
    bed = (day - timedelta(days=1)).replace(hour=23, minute=int(rng.integers(0, 40)), second=0)
    cur = bed
    recs.append(record("HKCategoryTypeIdentifierSleepAnalysis", WATCH,
                       "HKCategoryValueSleepAnalysisInBed", bed,
                       bed + timedelta(minutes=core + deep + rem + awake)))
    for stage, mins in [("HKCategoryValueSleepAnalysisAsleepCore", core),
                        ("HKCategoryValueSleepAnalysisAsleepDeep", deep),
                        ("HKCategoryValueSleepAnalysisAsleepREM", rem),
                        ("HKCategoryValueSleepAnalysisAwake", awake)]:
        nxt = cur + timedelta(minutes=mins)
        recs.append(record("HKCategoryTypeIdentifierSleepAnalysis", WATCH, stage, cur, nxt))
        cur = nxt

    # --- workouts: a Running workout every 3rd day; Yoga/Strength as noise ----
    if off % 3 == 0:
        km = round(float(rng.uniform(3.0, 8.0)), 2)
        running_km += km
        st = day.replace(hour=7, minute=0, second=0)
        dur = km * rng.uniform(5.5, 6.5)                              # ~min
        en = st + timedelta(minutes=dur)
        kcal = round(km * float(rng.uniform(55, 70)), 2)
        recs.append(
            f'  <Workout workoutActivityType="HKWorkoutActivityTypeRunning" '
            f'duration="{dur:.4f}" durationUnit="min" totalDistance="{km}" '
            f'totalDistanceUnit="km" totalEnergyBurned="{kcal}" totalEnergyBurnedUnit="kcal" '
            f'sourceName="{WATCH}" sourceVersion="11.0" creationDate="{hdt(en)}" '
            f'startDate="{hdt(st)}" endDate="{hdt(en)}">\n'
            f'   <WorkoutStatistics type="HKQuantityTypeIdentifierHeartRate" '
            f'startDate="{hdt(st)}" endDate="{hdt(en)}" average="{rng.uniform(140,160):.1f}" '
            f'minimum="95" maximum="178" unit="count/min"/>\n'
            f'   <WorkoutStatistics type="HKQuantityTypeIdentifierActiveEnergyBurned" '
            f'startDate="{hdt(st)}" endDate="{hdt(en)}" sum="{kcal}" unit="kcal"/>\n'
            f'  </Workout>')
    elif off % 3 == 1:
        st = day.replace(hour=18, minute=0, second=0)
        en = st + timedelta(minutes=float(rng.uniform(25, 50)))
        recs.append(
            f'  <Workout workoutActivityType="HKWorkoutActivityTypeYoga" '
            f'duration="{(en - st).total_seconds() / 60:.4f}" durationUnit="min" '
            f'totalEnergyBurned="{rng.uniform(80, 160):.2f}" totalEnergyBurnedUnit="kcal" '
            f'sourceName="{WATCH}" sourceVersion="11.0" creationDate="{hdt(en)}" '
            f'startDate="{hdt(st)}" endDate="{hdt(en)}"/>')

dob = "1990-04-12"
xml = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<!DOCTYPE HealthData [',
       '<!-- HealthKit Export Version: 14 -->',
       '<!ELEMENT HealthData (ExportDate, Me, (Record|Correlation|Workout|ActivitySummary)*)>',
       '<!ATTLIST HealthData locale CDATA #REQUIRED>',
       '<!ELEMENT ExportDate EMPTY>',
       '<!ATTLIST ExportDate value CDATA #REQUIRED>',
       '<!ELEMENT Me EMPTY>',
       '<!ELEMENT Record ((MetadataEntry|HeartRateVariabilityMetadataList)*)>',
       '<!ELEMENT Workout ((MetadataEntry|WorkoutEvent|WorkoutStatistics|WorkoutRoute)*)>',
       '<!ELEMENT WorkoutStatistics EMPTY>',
       '<!ELEMENT MetadataEntry EMPTY>',
       ']>',
       '<HealthData locale="en_US">',
       f' <ExportDate value="{hdt(datetime(2025, 10, 22, 8, 15, 42))}"/>',
       f' <Me HKCharacteristicTypeIdentifierDateOfBirth="{dob}"'
       ' HKCharacteristicTypeIdentifierBiologicalSex="HKBiologicalSexMale"'
       ' HKCharacteristicTypeIdentifierBloodType="HKBloodTypeNotSet"/>']
xml += recs
xml += ['</HealthData>']
with open(os.path.join(d("health"), "apple_health_export.xml"), "w") as f:
    f.write("\n".join(xml) + "\n")

# ---- gold: Apple Health -----------------------------------------------------
G["R4_watch_total_steps"] = int(sum(watch_daily.values()))
G["R4_days_over_10k"] = int(sum(1 for v in watch_daily.values() if v >= 10000))
G["R4_avg_resting_hr"] = round(sum(resting_vals) / len(resting_vals), 1)
G["R4_total_asleep_hours"] = round(asleep_minutes_total / 60.0, 1)
G["R4_running_distance_km"] = round(running_km, 1)


# =====================================================================
# 5) A FULL YEAR OF MONTHLY CHASE CHECKING STATEMENTS (12 PDFs) -> aggregate
#    finance/statements_2025/chase_checking_2025-01.pdf ... -12.pdf
#    Balances chain month to month (each Beginning = prior Ending), so the
#    task is "discover 12 files, parse each, aggregate across the year".
# =====================================================================
def build_checking_pages(period, begin, tx):
    """Render one Chase Total Checking statement from a txn list -> (pages, ending)."""
    def rows_for(name):
        return [t for t in tx if t["section"] == name]

    def sum_for(name):
        return round(sum(t["amount"] for t in rows_for(name)), 2)

    ending = round(begin + sum(t["amount"] for t in tx), 2)
    summ = [f"{'Beginning Balance':<53}{'':>9}{usd(begin):>15}"]
    for label, key in [("Deposits and Additions", "deposit"),
                       ("ATM & Debit Card Withdrawals", "card"),
                       ("Electronic Withdrawals", "electronic"), ("Fees", "fee")]:
        if rows_for(key):                                   # Chase omits empty groups
            summ.append(f"{label:<53}{len(rows_for(key)):>9}{money(sum_for(key)):>15}")
    summ.append(f"{'Ending Balance':<53}{len(tx):>9}{usd(ending):>15}")
    L = [
        "JPMorgan Chase Bank, N.A." + " " * 24 + period,
        "P O Box 182051",
        "Columbus, OH 43218 - 2051" + " " * 22 + "Primary Account: 000000642118293",
        "", "JORDAN A RIVERA", "1428 ELM ST APT 5", "OAKLAND CA 94610-2231",
        "", "CHASE TOTAL CHECKING", "",
        "CHECKING SUMMARY" + " " * 38 + "INSTANCES" + " " * 12 + "AMOUNT",
    ] + summ + ["", ""]
    for title, key, tot in [
        ("DEPOSITS AND ADDITIONS", "deposit", "Total Deposits and Additions"),
        ("ATM & DEBIT CARD WITHDRAWALS", "card", "Total ATM & Debit Card Withdrawals"),
        ("ELECTRONIC WITHDRAWALS", "electronic", "Total Electronic Withdrawals"),
        ("FEES", "fee", "Total Fees"),
    ]:
        sr = rows_for(key)
        if not sr:
            continue
        L += [title, _HDR] + detail_rows(sr)
        L += [f"{tot:<{8 + DW}}{usd(sum_for(key)):>{AW}}", "", ""]
    return paginate(L, 56, "JORDAN A RIVERA  |  Account 000000642118293"), ending


srng = np.random.default_rng(2025)
SDIR = d("finance/statements_2025")
for fn in os.listdir(SDIR):
    if fn.endswith(".pdf"):
        os.remove(os.path.join(SDIR, fn))

_groc = ["Whole Foods Mkt Oakland CA", "Trader Joes 553 Berkeley CA", "Safeway 1234 Oakland CA",
         "Costco Whse 0444 Richmond CA", "Berkeley Bowl Berkeley CA", "Lucky 0712 Oakland CA",
         "Grocery Outlet Oakland CA", "Mollie Stones Oakland CA"]
_dine = ["Chipotle 1492 Oakland CA", "Starbucks 0421 Oakland CA", "Sq Blue Bottle Oaklnd",
         "Doordash Sf Ca", "Tst Tartine Oakland CA", "Sweetgreen Oakland CA", "Philz Coffee Oaklnd",
         "Peets Coffee 084 Oaklnd", "Panera Bread Emeryvl CA", "Shake Shack Sf Ca",
         "Ramen Shop Oakland CA", "Tacos Mi Rancho Oaklnd", "Ubereats Help.uber.com"]
_gas = ["Shell Oil 5742 Oakland CA", "Chevron 0099 Emeryville CA", "76 Station Oakland CA",
        "Arco 4421 Oakland CA", "Valero 0098 Berkeley CA"]
_shop = ["Amazon.com Amzn WA", "Amzn Mktp US Amzn WA", "Target 1842 Emeryville CA",
         "Best Buy 0123 Emeryvl CA", "Apple Store 866712 CA", "Walmart 1771 San Leandro",
         "Ikea Emeryville CA", "Rei 0011 Berkeley CA", "Nordstrom Sf Ca", "Etsy.com Brooklyn NY"]
_pharm = ["Walgreens 1023 Oakland CA", "Cvs Pharmacy 884 Oaklnd", "Rite Aid 552 Oakland CA"]
_trans = ["Uber Trip Help.uber.com", "Lyft Ride Sf Ca", "Bart Clipper Oakland CA",
          "Ac Transit Oakland CA", "Bay Wheels Sf Ca", "Parking Kiosk Oaklnd CA"]
_fun = ["Amc Bay St 16 Emeryvl", "Steam Games Wa", "Playstation Netwrk CA",
        "Ticketmaster 8006532 CA", "Audible 888283 NJ", "Kindle Svcs Amzn WA",
        "Patreon Membership NY"]

year = {"dep": 0.0, "cardtot": 0.0, "cardcnt": 0, "fees": 0.0, "netflix": 0, "month": {}, "min_end": 1e18}
sbegin = 5000.00
for m in range(1, 13):
    last = calendar.monthrange(YEAR, m)[1]
    tx = []

    def add(day, section, desc, amount):
        tx.append(dict(day=day, section=section, desc=desc, amount=amount, wrap=None, mon=m))

    def buy(pool, lo, hi, kind="Card Purchase"):
        day = int(srng.integers(1, last + 1))
        merch = str(srng.choice(pool))
        add(day, "card", f"{kind}  {m:02d}/{day:02d}  {merch}  Card {CARD}",
            -round(float(srng.uniform(lo, hi)), 2))

    # deposits: two payroll runs (bi-monthly) plus occasional extras
    add(15, "deposit", "Acme Corp Payroll PPD ID: 5551234567", round(4500 + float(srng.uniform(-50, 180)), 2))
    add(last, "deposit", "Acme Corp Payroll PPD ID: 5551234567", round(4500 + float(srng.uniform(-50, 180)), 2))
    if srng.random() < 0.40:
        add(int(srng.integers(3, 26)), "deposit", "Zelle Payment From Jamie Lee Jpm99Abc34",
            round(float(srng.uniform(30, 220)), 2))
    if srng.random() < 0.20:
        add(int(srng.integers(3, 26)), "deposit", "Venmo Cashout PPD ID: 5264681001",
            round(float(srng.uniform(15, 120)), 2))

    # recurring subscriptions (each appears every month -> Netflix is 12x across the year)
    for sday, sname, samt in [(2, "Netflix.com 866-579-7172 CA", 15.49),
                              (5, "Spotify USA 877-778-1161 NY", 11.99),
                              (7, "Hulu 877-8244858 CA", 17.99),
                              (9, "Apple.com/Bill Icloud CA", 2.99),
                              (11, "Nytimes Digital NY", 4.25),
                              (13, "Planet Fit 0421 Oaklnd", 24.99)]:
        add(sday, "card", f"Recurring Card Purchase  {m:02d}/{sday:02d}  {sname}  Card {CARD}", -samt)

    # variable card spend -- a full month's worth (holiday bump in Nov/Dec)
    hol = 1 if m in (11, 12) else 0
    for _ in range(int(srng.integers(8, 15))):
        buy(_groc, 15, 190)
    for _ in range(int(srng.integers(14, 23))):
        buy(_dine, 5, 65)
    for _ in range(int(srng.integers(3, 7))):
        buy(_gas, 35, 85)
    for _ in range(int(srng.integers(6, 12)) + 8 * hol):
        buy(_shop, 12, 600 if hol else 280)
    for _ in range(int(srng.integers(3, 7))):
        buy(_pharm, 8, 95)
    for _ in range(int(srng.integers(3, 8))):
        buy(_trans, 6, 60)
    for _ in range(int(srng.integers(3, 7))):
        buy(_fun, 6, 120)
    for _ in range(int(srng.integers(0, 3))):
        day = int(srng.integers(1, last + 1))
        add(day, "card", f"ATM Withdrawal  {m:02d}/{day:02d}  1455 Broadway Oakland CA  Card {CARD}",
            -float(srng.choice([40, 60, 80, 100, 200])))

    # electronic: rent, utilities, insurance, credit-card payment, savings sweep, Zelle
    add(1, "electronic", f"Property Mgmt Rent Web ID: 2026{int(srng.integers(0, 10**6)):06d}", -2100.00)
    add(3, "electronic", "Pg&E Web Online Pmt PPD ID: 1234567890", -round(float(srng.uniform(80, 190)), 2))
    add(6, "electronic", "Ebmud Water Web Pmt PPD ID: 5566778899", -round(float(srng.uniform(35, 80)), 2))
    add(12, "electronic", "Comcast Cable Comm Web Pmt PPD ID: 9876543210", -89.99)
    add(14, "electronic", "Att Wireless Web ID: 1112223334", -round(float(srng.uniform(70, 95)), 2))
    add(16, "electronic", "Geico Insurance Web ID: 2024556677", -round(float(srng.uniform(115, 160)), 2))
    if srng.random() < 0.60:
        add(20, "electronic", "Chase Credit Crd Epay PPD ID: 4356789012",
            -round(float(srng.uniform(300, 900)), 2))
    if srng.random() < 0.50:
        add(22, "electronic", f"Online Transfer To Sav ...4321 Transaction#: 79{int(srng.integers(0, 10**8)):08d}",
            -float(srng.choice([200, 300, 400, 500])))
    if srng.random() < 0.30:
        add(int(srng.integers(3, 26)), "electronic", "Zelle Payment To Morgan P Jpm88Xyz12",
            -round(float(srng.uniform(20, 150)), 2))

    # fees: ~30% of months
    if srng.random() < 0.30:
        add(last, "fee", str(srng.choice(["Monthly Service Fee", "Non-Chase ATM Fee"])),
            -float(srng.choice([3.00, 12.00])))

    tx.sort(key=lambda t: (t["day"], SECTION_ORDER[t["section"]]))
    mn = calendar.month_name[m]
    period = f"{mn} 01, {YEAR} through {mn} {last}, {YEAR}"
    pages, ending = build_checking_pages(period, sbegin, tx)
    make_pdf(os.path.join(SDIR, f"chase_checking_{YEAR}-{m:02d}.pdf"), pages)

    mcard = round(sum(-t["amount"] for t in tx if "Card Purchase" in t["desc"]), 2)
    year["dep"] += sum(t["amount"] for t in tx if t["section"] == "deposit")
    year["cardtot"] += mcard
    year["cardcnt"] += sum(1 for t in tx if "Card Purchase" in t["desc"])
    year["fees"] += sum(-t["amount"] for t in tx if t["section"] == "fee")
    year["netflix"] += sum(1 for t in tx if "Netflix" in t["desc"])
    year["month"][f"{YEAR}-{m:02d}"] = mcard
    year["min_end"] = min(year["min_end"], ending)
    sbegin = ending

G["R5_year_total_deposits"] = round(year["dep"], 2)
G["R5_year_card_purchase_total"] = round(year["cardtot"], 2)
G["R5_year_card_purchase_count"] = int(year["cardcnt"])
G["R5_top_spend_month"] = max(year["month"], key=year["month"].get)
G["R5_year_total_fees"] = round(year["fees"], 2)
G["R5_netflix_charge_count"] = int(year["netflix"])
G["R5_dec_ending_balance"] = round(sbegin, 2)


# =====================================================================
print(json.dumps(G, indent=2, default=str))
print("\n# files written under", BASE)
for rel in ["finance/chase_checking_statement.pdf", "finance/chase_sapphire_statement.pdf",
            "finance/activity_download.qfx", "health/apple_health_export.xml"]:
    p = os.path.join(BASE, rel)
    print(f"#   {rel:48} {os.path.getsize(p):>8,} bytes")
print(f"# checking: begin {BEGIN_BAL:.2f} + net {sum(t['amount'] for t in txns):+.2f} "
      f"= ending {ENDING_BAL:.2f} | {len(txns)} txns | health records {len(recs)}")
print(f"#   finance/statements_2025/ : 12 monthly checking PDFs | year card spend "
      f"{G['R5_year_card_purchase_total']:,.2f} | top month {G['R5_top_spend_month']} "
      f"| Dec ending {G['R5_dec_ending_balance']:,.2f} | min monthly ending {year['min_end']:,.2f}")
