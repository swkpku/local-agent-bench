#!/usr/bin/env python3
"""
Independent verifier for generate_real.py. Re-derives every gold answer by
PARSING THE RENDERED FILES the way an agent would (pdftotext + regex for the
PDFs, regex SGML for the OFX, ElementTree for the XML) -- never trusting the
generator's in-memory data. Then it diffs against the generator's printed gold.

Run:  python3 bench/private-files/verify_real.py
Exit code 0 and "ALL OK" iff every key re-derives exactly from the files.
"""
import os, re, csv, glob, json, subprocess, sys
import xml.etree.ElementTree as ET
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
FIN = os.path.join(BASE, "finance")
HEALTH = os.path.join(BASE, "health")


def pdftext(path):
    return subprocess.run(["pdftotext", "-layout", path, "-"],
                          capture_output=True, text=True, check=True).stdout


def sections(text, headers):
    """Split text into {header: [body lines]} using the given ordered headers."""
    lines = text.splitlines()
    idx = {h: next((i for i, ln in enumerate(lines) if ln.strip() == h), None) for h in headers}
    present = sorted([(i, h) for h, i in idx.items() if i is not None])
    out = {}
    for n, (i, h) in enumerate(present):
        end = present[n + 1][0] if n + 1 < len(present) else len(lines)
        out[h] = lines[i + 1:end]
    return out


ROW = re.compile(r"^(\d{2}/\d{2})\s+(.*?)\s+(-?[\d,]+\.\d{2})\s*$")


def rows(body):
    """Transaction rows: 'MM/DD  description  amount' -> (desc, float)."""
    out = []
    for ln in body:
        m = ROW.match(ln.strip())
        if m:
            out.append((m.group(2).strip(), float(m.group(3).replace(",", ""))))
    return out


def money(s):
    return float(re.sub(r"[^\d.\-]", "", s))


# ---------------------------------------------------------------- R1: checking
def verify_checking():
    t = pdftext(os.path.join(FIN, "chase_checking_statement.pdf"))
    secs = sections(t, ["DEPOSITS AND ADDITIONS", "ATM & DEBIT CARD WITHDRAWALS",
                        "ELECTRONIC WITHDRAWALS", "FEES"])
    card = rows(secs["ATM & DEBIT CARD WITHDRAWALS"])
    elec = rows(secs["ELECTRONIC WITHDRAWALS"])
    purchases = [(d, a) for d, a in card if "Card Purchase" in d]   # excludes ATM Withdrawal

    # ending balance two ways: the summary line, and begin + every detail amount
    end_summary = money(re.search(r"Ending Balance\s+\d+\s+(\$[\d,]+\.\d{2})", t).group(1))
    begin = money(re.search(r"Beginning Balance\s+(\$[\d,]+\.\d{2})", t).group(1))
    all_amts = sum(a for sec in secs.values() for _, a in rows(sec))
    end_computed = round(begin + all_amts, 2)
    assert end_summary == end_computed, (end_summary, end_computed)

    return {
        "R1_ending_balance": end_summary,
        "R1_card_purchase_count": len(purchases),
        "R1_card_purchase_total": round(sum(-a for _, a in purchases), 2),
        "R1_recurring_count": sum(1 for d, _ in card if "Recurring Card Purchase" in d),
        "R1_largest_electronic_withdrawal": round(max(-a for _, a in elec), 2),
    }


# ----------------------------------------------------------------- R2: sapphire
def verify_sapphire():
    t = pdftext(os.path.join(FIN, "chase_sapphire_statement.pdf"))
    secs = sections(t, ["PAYMENTS AND OTHER CREDITS", "PURCHASE", "2025 Totals Year-to-Date"])
    purch = rows(secs["PURCHASE"])
    new_bal = money(re.search(r"New Balance\s+(\$[\d,]+\.\d{2})", t).group(1))
    return {
        "R2_new_balance": new_bal,
        "R2_purchase_count": len(purch),
        "R2_total_purchases": round(sum(a for _, a in purch), 2),
        "R2_largest_purchase": round(max(a for _, a in purch), 2),
        "R2_amazon_purchases": round(sum(a for d, a in purch
                                         if "AMZN" in d.upper() or "AMAZON" in d.upper()), 2),
    }


# --------------------------------------------------------------------- R3: OFX
def verify_ofx():
    s = open(os.path.join(FIN, "activity_download.qfx")).read()
    blocks = re.findall(r"<STMTTRN>(.*?)</STMTTRN>", s, re.S)
    amts = [float(re.search(r"<TRNAMT>(-?[\d.]+)", b).group(1)) for b in blocks]
    ledger = float(re.search(r"<LEDGERBAL>\s*<BALAMT>(-?[\d.]+)", s, re.S).group(1))
    return {
        "R3_transaction_count": len(blocks),
        "R3_credit_count": sum(1 for a in amts if a > 0),
        "R3_debit_count": sum(1 for a in amts if a < 0),
        "R3_total_debits": round(sum(-a for a in amts if a < 0), 2),
        "R3_ledger_balance": round(ledger, 2),
    }


# ------------------------------------------------------------ R4: Apple Health
def hparse(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S %z")


def verify_health():
    tree = ET.parse(os.path.join(HEALTH, "apple_health_export.xml"))
    root = tree.getroot()
    watch_by_day, resting, asleep_sec = {}, [], 0.0
    ASLEEP = {"HKCategoryValueSleepAnalysisAsleepCore",
              "HKCategoryValueSleepAnalysisAsleepDeep",
              "HKCategoryValueSleepAnalysisAsleepREM"}
    for r in root.findall("Record"):
        ty, src = r.get("type"), r.get("sourceName", "")
        if ty == "HKQuantityTypeIdentifierStepCount" and "Apple Watch" in src:
            day = hparse(r.get("startDate")).date()
            watch_by_day[day] = watch_by_day.get(day, 0) + int(r.get("value"))
        elif ty == "HKQuantityTypeIdentifierRestingHeartRate":
            resting.append(float(r.get("value")))
        elif ty == "HKCategoryTypeIdentifierSleepAnalysis" and r.get("value") in ASLEEP:
            asleep_sec += (hparse(r.get("endDate")) - hparse(r.get("startDate"))).total_seconds()
    running = sum(float(w.get("totalDistance")) for w in root.findall("Workout")
                  if w.get("workoutActivityType") == "HKWorkoutActivityTypeRunning")
    return {
        "R4_watch_total_steps": int(sum(watch_by_day.values())),
        "R4_days_over_10k": int(sum(1 for v in watch_by_day.values() if v >= 10000)),
        "R4_avg_resting_hr": round(sum(resting) / len(resting), 1),
        "R4_total_asleep_hours": round(asleep_sec / 3600.0, 1),
        "R4_running_distance_km": round(running, 1),
    }


# ------------------------------------------------- R5: 12 monthly statements
def verify_statements():
    files = sorted(glob.glob(os.path.join(FIN, "statements_2025", "chase_checking_2025-*.pdf")))
    assert len(files) == 12, f"expected 12 statements, found {len(files)}"
    dep = cardtot = fees = 0.0
    cardcnt = netflix = 0
    by_month, dec_ending = {}, None
    for f in files:
        t = pdftext(f)
        secs = sections(t, ["DEPOSITS AND ADDITIONS", "ATM & DEBIT CARD WITHDRAWALS",
                            "ELECTRONIC WITHDRAWALS", "FEES"])
        drows = rows(secs.get("DEPOSITS AND ADDITIONS", []))
        crows = rows(secs.get("ATM & DEBIT CARD WITHDRAWALS", []))
        frows = rows(secs.get("FEES", []))
        cp = [(de, a) for de, a in crows if "Card Purchase" in de]
        month = re.search(r"2025-\d{2}", f).group(0)
        by_month[month] = round(sum(-a for _, a in cp), 2)
        dep += sum(a for _, a in drows)
        cardtot += by_month[month]
        cardcnt += len(cp)
        fees += sum(-a for _, a in frows)
        netflix += sum(1 for de, _ in crows if "Netflix" in de)
        if month == "2025-12":
            dec_ending = money(re.search(r"Ending Balance\s+\d+\s+(-?\$[\d,]+\.\d{2})", t).group(1))
    return {
        "R5_year_total_deposits": round(dep, 2),
        "R5_year_card_purchase_total": round(cardtot, 2),
        "R5_year_card_purchase_count": int(cardcnt),
        "R5_top_spend_month": max(by_month, key=by_month.get),
        "R5_year_total_fees": round(fees, 2),
        "R5_netflix_charge_count": int(netflix),
        "R5_dec_ending_balance": dec_ending,
    }


def main():
    gold = json.loads(subprocess.run([sys.executable, os.path.join(BASE, "generate_real.py")],
                                     capture_output=True, text=True, check=True
                                     ).stdout.split("\n#")[0])
    got = {}
    for fn in (verify_checking, verify_sapphire, verify_ofx, verify_health, verify_statements):
        got.update(fn())

    ok = True
    print(f"{'KEY':<36}{'GOLD':>14}{'FROM FILE':>14}   ")
    print("-" * 72)
    for k in gold:
        g, v = gold[k], got.get(k, "—")
        match = (g == v)
        ok &= match
        print(f"{k:<36}{str(g):>14}{str(v):>14}   {'OK' if match else 'FAIL <<<'}")
    extra = set(got) - set(gold)
    if extra:
        ok = False
        print("UNEXPECTED KEYS FROM FILE:", extra)
    print("-" * 72)
    print("ALL OK ✓" if ok else "MISMATCH ✗")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
