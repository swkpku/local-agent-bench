#!/usr/bin/env python3
"""
Generate synthetic-but-realistic datasets for 'private' local-LLM tasks, and
compute the verified gold answers in the same pass (so grading matches the data
the agent sees). All randomness is seeded -> fully reproducible.

Domains: personal finance, health, freelance bookkeeping, HR/people.
Run:  python3 bench/private-tasks/generate.py
"""
import os, calendar
from datetime import date, timedelta
import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(42)
G = {}  # gold answers


def write(df, sub, name):
    d = os.path.join(BASE, sub, "data")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    df.to_csv(p, index=False)
    return p


# =====================================================================
# 1) PERSONAL FINANCE  -> finance/data/transactions.csv  (MM/DD/YYYY, debit<0)
# =====================================================================
rows = []
def add(d, desc, amt):
    rows.append((d.strftime("%m/%d/%Y"), desc, round(float(amt), 2)))

for m in range(1, 13):
    last = calendar.monthrange(2025, m)[1]
    add(date(2025, m, 15), "PAYROLL DEPOSIT EMPLOYER", 3200.00)
    add(date(2025, m, last), "PAYROLL DEPOSIT EMPLOYER", 3200.00)
    add(date(2025, m, 1), "RENT", -2100.00)
    add(date(2025, m, 12), "COMCAST", -79.99)
    add(date(2025, m, 18), "ATT", -65.00)
    add(date(2025, m, 10), "PG&E", -round(float(rng.uniform(70, 170)), 2))
    add(date(2025, m, 5), "NETFLIX", -15.49)
    add(date(2025, m, 8), "SPOTIFY", -11.99)
    add(date(2025, m, 2), "PLANET FITNESS", -39.00)
    for _ in range(int(rng.integers(4, 7))):
        add(date(2025, m, int(rng.integers(1, last + 1))),
            str(rng.choice(["WHOLEFDS", "TRADER JOES", "SAFEWAY", "COSTCO"])),
            -round(float(rng.uniform(20, 180)), 2))
    for _ in range(int(rng.integers(3, 8))):
        add(date(2025, m, int(rng.integers(1, last + 1))),
            str(rng.choice(["STARBUCKS", "CHIPOTLE", "DOORDASH", "BLUE BOTTLE"])),
            -round(float(rng.uniform(8, 75)), 2))
    for _ in range(int(rng.integers(2, 4))):
        add(date(2025, m, int(rng.integers(1, last + 1))),
            str(rng.choice(["SHELL", "CHEVRON"])),
            -round(float(rng.uniform(35, 75)), 2))
    nshop = int(rng.integers(1, 5)) + (4 if m == 11 else 0)
    for _ in range(nshop):
        hi = 600 if m == 11 else 250
        add(date(2025, m, int(rng.integers(1, last + 1))),
            str(rng.choice(["AMAZON", "AMZN Mktp", "TARGET", "BEST BUY"])),
            -round(float(rng.uniform(15, hi)), 2))
    if rng.random() < 0.5:
        add(date(2025, m, int(rng.integers(1, last + 1))),
            "ZELLE TRANSFER", -round(float(rng.uniform(50, 300)), 2))

# injected duplicate charges (same merchant + amount within 3 days)
add(date(2025, 3, 14), "DOORDASH", -42.50)
add(date(2025, 3, 15), "DOORDASH", -42.50)
add(date(2025, 7, 20), "BEST BUY", -129.99)
add(date(2025, 7, 22), "BEST BUY", -129.99)

fin = pd.DataFrame(rows, columns=["date", "description", "amount"])
fin["_d"] = pd.to_datetime(fin["date"], format="%m/%d/%Y")
fin = fin.sort_values("_d").reset_index(drop=True)

# --- gold F1: recurring fixed-amount commitments (debit, same desc+amount >=6x)
deb = fin[fin["amount"] < 0]
grp = deb.groupby(["description", "amount"]).size()
recur = grp[grp >= 6]
G["F1_recurring_count"] = int(len(recur))
G["F1_monthly_total"] = round(float(-recur.index.get_level_values("amount").to_series().sum()), 2)
G["F1_merchants"] = sorted(recur.index.get_level_values("description").tolist())

# --- gold F2: highest discretionary-spend month
essentials = {"RENT", "COMCAST", "ATT", "PG&E"}
d2 = deb[~deb["description"].isin(essentials) & ~deb["description"].str.contains("TRANSFER")].copy()
d2["month"] = d2["_d"].dt.month
bymon = d2.groupby("month")["amount"].sum().abs()
G["F2_top_month"] = int(bymon.idxmax())
G["F2_top_amount"] = round(float(bymon.max()), 2)

# --- gold F3: duplicate charges (same desc + identical amount, <=3 days apart)
dups = 0
dd = deb.sort_values("_d")
for (desc, amt), g in dd.groupby(["description", "amount"]):
    ds = sorted(g["_d"].tolist())
    for i in range(len(ds) - 1):
        if (ds[i + 1] - ds[i]).days <= 3:
            dups += 1
G["F3_duplicate_pairs"] = int(dups)
write(fin.drop(columns="_d"), "finance", "transactions.csv")

# =====================================================================
# 2) HEALTH  -> health/data/labs.csv , health/data/sleep.csv
# =====================================================================
dates = ["2025-02-10", "2025-06-12", "2025-11-05"]
labs_spec = {
    "Total Cholesterol": ("mg/dL", 125, 200, [210, 224, 238]),
    "LDL":               ("mg/dL", 0, 100, [140, 155, 168]),
    "HDL":               ("mg/dL", 40, 60, [45, 43, 41]),
    "Triglycerides":     ("mg/dL", 0, 150, [160, 175, 190]),
    "Glucose":           ("mg/dL", 70, 99, [96, 104, 108]),
    "HbA1c":             ("%", 4.0, 5.6, [5.5, 5.8, 6.0]),
    "Vitamin D":         ("ng/mL", 30, 100, [24, 22, 21]),
    "TSH":               ("mIU/L", 0.4, 4.0, [2.1, 2.4, 2.0]),
    "ALT":               ("U/L", 7, 56, [30, 28, 33]),
    "Creatinine":        ("mg/dL", 0.6, 1.3, [0.9, 1.0, 0.95]),
}
lrows = []
for test, (unit, lo, hi, vals) in labs_spec.items():
    for dt, v in zip(dates, vals):
        lrows.append((dt, test, v, unit, lo, hi))
labs = pd.DataFrame(lrows, columns=["date", "test", "value", "unit", "ref_low", "ref_high"])
oor = labs[(labs["value"] < labs["ref_low"]) | (labs["value"] > labs["ref_high"])]
G["H1_out_of_range_results"] = int(len(oor))
G["H1_distinct_tests_oor"] = int(oor["test"].nunique())
ldl = labs[labs["test"] == "LDL"].sort_values("date")["value"].tolist()
G["H1_ldl_latest"] = ldl[-1]
G["H1_ldl_trend"] = "increasing" if ldl[-1] > ldl[0] else "decreasing"
write(labs, "health", "labs.csv")

n = 90
start = date(2025, 9, 1)
sleep_h = np.clip(rng.normal(7.0, 1.0, n), 3.5, 10.5)
resting = 70 - 2.0 * (sleep_h - 7) + rng.normal(0, 2.0, n)
steps = rng.integers(2000, 14000, n)
srows = [((start + timedelta(days=i)).isoformat(),
          round(float(sleep_h[i]), 2), round(float(resting[i]), 1), int(steps[i]))
         for i in range(n)]
sleep = pd.DataFrame(srows, columns=["date", "sleep_hours", "resting_hr", "steps"])
G["H2_corr_sleep_hr"] = round(float(stats.pearsonr(sleep["sleep_hours"], sleep["resting_hr"])[0]), 2)
G["H2_hr_under6"] = round(float(sleep[sleep["sleep_hours"] < 6]["resting_hr"].mean()), 2)
G["H2_hr_7plus"] = round(float(sleep[sleep["sleep_hours"] >= 7]["resting_hr"].mean()), 2)
write(sleep, "health", "sleep.csv")

# =====================================================================
# 3) FREELANCE BOOKKEEPING -> bookkeeping/data/invoices.csv , expenses.csv
# =====================================================================
clients = ["Acme Co", "Globex", "Initech", "Umbrella", "Wayne LLC"]
asof = date(2025, 12, 15)
irows = []
for i in range(36):
    issue = date(2025, 1, 1) + timedelta(days=int(rng.integers(0, 349)))
    due = issue + timedelta(days=30)
    amount = round(float(rng.integers(16, 121)) * 50, 2)  # 800..6000
    client = str(rng.choice(clients))
    if rng.random() < 0.68:
        paid = (due + timedelta(days=int(rng.integers(-5, 20)))).isoformat()
    else:
        paid = ""
    irows.append((f"INV-{1000+i}", client, issue.isoformat(), due.isoformat(), amount, paid))
inv = pd.DataFrame(irows, columns=["invoice_id", "client", "issue_date", "due_date", "amount", "paid_date"])
unpaid = inv[inv["paid_date"] == ""].copy()
unpaid["due"] = pd.to_datetime(unpaid["due_date"]).dt.date
unpaid["dpd"] = unpaid["due"].apply(lambda d: (asof - d).days)
def bucket(d):
    if d <= 0: return "Current"
    if d <= 30: return "1-30"
    if d <= 60: return "31-60"
    if d <= 90: return "61-90"
    return "90+"
unpaid["bucket"] = unpaid["dpd"].apply(bucket)
G["B1_aging"] = {k: round(float(v), 2) for k, v in unpaid.groupby("bucket")["amount"].sum().items()}
G["B1_total_outstanding"] = round(float(unpaid["amount"].sum()), 2)
paid = inv[inv["paid_date"] != ""]
rev = paid.groupby("client")["amount"].sum()
G["B2_top_client"] = rev.idxmax()
G["B2_top_client_revenue"] = round(float(rev.max()), 2)
G["B2_total_paid_revenue"] = round(float(paid["amount"].sum()), 2)
write(inv, "bookkeeping", "invoices.csv")

cats = ["Software", "Equipment", "Travel", "Meals", "Office", "Contractors"]
erows = []
for _ in range(72):
    dt = date(2025, 1, 1) + timedelta(days=int(rng.integers(0, 360)))
    cat = str(rng.choice(cats))
    amt = round(float(rng.uniform(20, 1200)), 2)
    erows.append((dt.isoformat(), f"vendor_{int(rng.integers(1,40))}", cat, amt))
exp = pd.DataFrame(erows, columns=["date", "vendor", "category", "amount"])
exp["_m"] = pd.to_datetime(exp["date"]).dt.month
q3 = exp[exp["_m"].isin([7, 8, 9])]
G["B3_q3_by_category"] = {k: round(float(v), 2) for k, v in q3.groupby("category")["amount"].sum().items()}
ded = q3.copy()
ded["d"] = ded.apply(lambda r: r["amount"] * (0.5 if r["category"] == "Meals" else 1.0), axis=1)
G["B3_q3_deductible_total"] = round(float(ded["d"].sum()), 2)
write(exp.drop(columns="_m"), "bookkeeping", "expenses.csv")

# =====================================================================
# 4) HR / PEOPLE  -> hr/data/employees.csv
# =====================================================================
depts = {"Engineering": (150000, 30000), "Sales": (110000, 25000),
         "Marketing": (95000, 18000), "Ops": (85000, 15000)}
titles = {"Engineering": ["Engineer", "Sr Engineer", "Staff Engineer"],
          "Sales": ["AE", "Sr AE", "Sales Lead"],
          "Marketing": ["Specialist", "Manager"], "Ops": ["Analyst", "Manager"]}
first = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie",
         "Avery", "Quinn", "Drew", "Reese", "Skyler", "Devon", "Harper", "Rowan",
         "Emerson", "Finley", "Hayden", "Kai", "Lane", "Marlow", "Noel", "Oakley", "Sage"]
hrows = []
NEMP = 32
for i in range(NEMP):
    dept = str(rng.choice(list(depts), p=[0.47, 0.21, 0.18, 0.14]))
    base, spread = depts[dept]
    gender = str(rng.choice(["F", "M"]))
    # bake a clear pay gap in Engineering
    adj = -16000 if (dept == "Engineering" and gender == "F") else 0
    salary = int(round((base + rng.normal(0, spread) + adj) / 1000.0)) * 1000
    hire = date(2025, 12, 31) - timedelta(days=int(rng.integers(120, 2600)))
    accrued = int(rng.integers(8, 26))
    if rng.random() < 0.2:             # ~1 in 5 over-takes (negative balance)
        taken = accrued + int(rng.integers(1, 5))
    else:
        taken = int(rng.integers(0, accrued + 1))
    nm = first[i] if i < len(first) else f"Person{i}"
    hrows.append((nm, dept, str(rng.choice(titles[dept])), gender,
                  hire.isoformat(), salary, accrued, taken))
emp = pd.DataFrame(hrows, columns=["name", "department", "title", "gender",
                                   "hire_date", "annual_salary", "pto_accrued", "pto_taken"])
G["P1_median_salary_by_dept"] = {k: float(v) for k, v in emp.groupby("department")["annual_salary"].median().items()}
eng = emp[emp["department"] == "Engineering"]
mf = eng[eng["gender"] == "F"]["annual_salary"].median()
mm = eng[eng["gender"] == "M"]["annual_salary"].median()
G["P1_eng_female_pct_of_male"] = round(float(mf / mm * 100), 1)
liab = (emp["pto_accrued"] - emp["pto_taken"]).clip(lower=0)
G["P2_pto_liability_days"] = int(liab.sum())
G["P2_negative_balance_count"] = int((emp["pto_taken"] > emp["pto_accrued"]).sum())
write(emp, "hr", "employees.csv")

# =====================================================================
print("=" * 60, "\nGOLD ANSWERS\n", "=" * 60, sep="")
import json
print(json.dumps(G, indent=2, default=str))
print("\nrow counts: transactions=%d labs=%d sleep=%d invoices=%d expenses=%d employees=%d"
      % (len(fin), len(labs), len(sleep), len(inv), len(exp), len(emp)))
