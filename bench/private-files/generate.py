#!/usr/bin/env python3
"""
Generate private-domain data in NON-CSV formats, each needing a different tool,
and compute verified gold answers in the same pass. Seeded -> reproducible.

  SQLite (.db)  -> SQL                 finance/personal.db
  nested JSON   -> json / jq           shopping/orders.json
  mbox email    -> email module+regex  email/inbox.mbox
  Apple-Health XML -> ElementTree      health/export.xml
  WhatsApp txt  -> regex / awk         messages/chat.txt
  PDF           -> pdftotext (poppler) labs/lab_report.pdf
  zip archive   -> zipfile (+csv/json) export/takeout.zip

Run:  python3 bench/private-files/generate.py
Needs only the stdlib + numpy (PDF is parsed by the `pdftotext` CLI, not Python).
"""
import os, sqlite3, json, mailbox, zipfile, io, csv, calendar
from email.message import EmailMessage
from datetime import date, datetime, timedelta
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(7)
G = {}

def d(sub):
    p = os.path.join(BASE, sub); os.makedirs(p, exist_ok=True); return p


# ---------------------------------------------------------------- SQLite
p = os.path.join(d("finance"), "personal.db")
if os.path.exists(p): os.remove(p)
con = sqlite3.connect(p); cur = con.cursor()
cur.execute("CREATE TABLE categories(id INTEGER PRIMARY KEY, name TEXT)")
cur.execute("CREATE TABLE txns(id INTEGER PRIMARY KEY, ts TEXT, merchant TEXT, amount REAL, category_id INTEGER)")
cats = ["Groceries", "Dining", "Transport", "Shopping", "Utilities", "Entertainment"]
cur.executemany("INSERT INTO categories(id,name) VALUES(?,?)", list(enumerate(cats, 1)))
txns = []
tid = 1
for m in range(1, 13):
    last = calendar.monthrange(2025, m)[1]
    for _ in range(int(rng.integers(12, 20))):
        cid = int(rng.integers(1, len(cats) + 1))
        amt = round(float(rng.uniform(6, 240)), 2)
        day = int(rng.integers(1, last + 1))
        ts = f"2025-{m:02d}-{day:02d} {int(rng.integers(7,23)):02d}:{int(rng.integers(0,60)):02d}"
        txns.append((tid, ts, f"merchant_{int(rng.integers(1,40))}", amt, cid)); tid += 1
cur.executemany("INSERT INTO txns VALUES(?,?,?,?,?)", txns)
con.commit()
# gold: Q4 spend by category (JOIN), top category
rows = cur.execute("""
  SELECT c.name, ROUND(SUM(t.amount),2) s, COUNT(*) n
  FROM txns t JOIN categories c ON c.id=t.category_id
  WHERE substr(t.ts,6,2) IN ('10','11','12')
  GROUP BY c.name ORDER BY s DESC""").fetchall()
G["S1_top_category"] = rows[0][0]
G["S1_top_category_q4_spend"] = round(rows[0][1], 2)
G["S1_q4_txn_count"] = int(cur.execute(
    "SELECT COUNT(*) FROM txns WHERE substr(ts,6,2) IN ('10','11','12')").fetchone()[0])
con.close()


# ---------------------------------------------------------------- nested JSON
items_pool = ["USB-C Cable", "Coffee Beans", "Notebook", "Phone Case", "T-Shirt",
              "Desk Lamp", "Water Bottle", "Batteries", "Sketchpad", "Headphones"]
orders = []
for i in range(40):
    n = int(rng.integers(1, 5))
    its = []
    for _ in range(n):
        its.append({"name": str(rng.choice(items_pool)),
                    "qty": int(rng.integers(1, 4)),
                    "price": round(float(rng.uniform(5, 90)), 2)})
    dt = (date(2025, 1, 1) + timedelta(days=int(rng.integers(0, 364)))).isoformat()
    orders.append({"id": f"ORD-{2000+i}", "date": dt,
                   "merchant": str(rng.choice(["ShopA", "ShopB", "ShopC"])), "items": its})
json.dump({"orders": orders}, open(os.path.join(d("shopping"), "orders.json"), "w"), indent=2)
# gold: grand total, top item by total qty, #orders with order-total > 100
grand = 0.0; qty = {}; over = 0
for o in orders:
    tot = sum(it["qty"] * it["price"] for it in o["items"])
    grand += tot
    if tot > 100: over += 1
    for it in o["items"]:
        qty[it["name"]] = qty.get(it["name"], 0) + it["qty"]
G["J1_grand_total"] = round(grand, 2)
G["J1_top_item_by_qty"] = max(qty, key=qty.get)
G["J1_orders_over_100"] = int(over)


# ---------------------------------------------------------------- mbox email
mp = os.path.join(d("email"), "inbox.mbox")
if os.path.exists(mp): os.remove(mp)
box = mailbox.mbox(mp)
order_total = {}; order_count = 0
for i in range(28):
    msg = EmailMessage()
    dt = datetime(2025, 1, 1) + timedelta(days=int(rng.integers(0, 360)), hours=int(rng.integers(0, 24)))
    msg["Date"] = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    if rng.random() < 0.7:  # order confirmation
        mer = str(rng.choice(["ShopA", "ShopB", "ShopC", "ShopD"]))
        amt = round(float(rng.uniform(12, 220)), 2)
        msg["From"] = f"orders@{mer.lower()}.com"
        msg["Subject"] = f"Your order from {mer} is confirmed"
        msg.set_content(f"Thanks for shopping with us!\nMerchant: {mer}\nOrder total: ${amt:.2f}\nShips in 3-5 days.")
        order_total[mer] = order_total.get(mer, 0.0) + amt
        order_count += 1
    else:  # noise
        msg["From"] = "news@listserv.example.com"
        msg["Subject"] = str(rng.choice(["Weekly newsletter", "Security alert", "We miss you!"]))
        msg.set_content("This is a marketing email. No purchase here.")
    box.add(msg)
box.flush(); box.close()
G["M1_order_email_count"] = int(order_count)
G["M1_total_spent"] = round(sum(order_total.values()), 2)
G["M1_top_merchant"] = max(order_total, key=order_total.get)


# ---------------------------------------------------------------- Apple-Health XML
recs = []
steps_oct = 0; days_10k = 0
for day in range(1, 32):
    s = int(rng.integers(3000, 16000))
    steps_oct += s
    if s >= 10000: days_10k += 1
    recs.append(f'  <Record type="HKQuantityTypeIdentifierStepCount" '
                f'startDate="2025-10-{day:02d} 23:59:00 -0700" value="{s}" unit="count"/>')
hrs = []
for day in range(1, 32):
    hr = int(round(float(rng.normal(62, 5))))
    hrs.append(hr)
    recs.append(f'  <Record type="HKQuantityTypeIdentifierRestingHeartRate" '
                f'startDate="2025-10-{day:02d} 08:00:00 -0700" value="{hr}" unit="count/min"/>')
xml = '<?xml version="1.0" encoding="UTF-8"?>\n<HealthData locale="en_US">\n' + "\n".join(recs) + "\n</HealthData>\n"
open(os.path.join(d("health"), "export.xml"), "w").write(xml)
G["X1_total_steps_october"] = int(steps_oct)
G["X1_days_over_10k"] = int(days_10k)
G["X1_avg_resting_hr"] = round(sum(hrs) / len(hrs), 1)


# ---------------------------------------------------------------- WhatsApp txt
people = ["Alice", "Me"]
snips = ["see you soon", "ok", "let's get dinner", "haha", "on my way", "call me",
         "dinner at 7?", "sounds good", "running late", "thanks!", "where are you",
         "lunch tomorrow?", "yes", "no worries", "dinner was great"]
lines = []
per_sender = {p: 0 for p in people}; dinner = 0; per_day = {}
dt = datetime(2025, 5, 1, 9, 0)
for _ in range(140):
    dt += timedelta(minutes=int(rng.integers(5, 220)))
    sender = str(rng.choice(people, p=[0.45, 0.55]))
    text = str(rng.choice(snips))
    lines.append(f"{dt.strftime('%m/%d/%y, %H:%M')} - {sender}: {text}")
    per_sender[sender] += 1
    if "dinner" in text.lower(): dinner += 1
    k = dt.strftime("%m/%d/%y"); per_day[k] = per_day.get(k, 0) + 1
open(os.path.join(d("messages"), "chat.txt"), "w").write("\n".join(lines) + "\n")
G["W1_msgs_alice"] = int(per_sender["Alice"])
G["W1_msgs_me"] = int(per_sender["Me"])
G["W1_top_sender"] = max(per_sender, key=per_sender.get)
G["W1_dinner_mentions"] = int(dinner)
G["W1_busiest_day"] = max(per_day, key=per_day.get)


# ---------------------------------------------------------------- PDF (lab report)
def make_pdf(path, lines):
    def esc(s): return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = "BT /F1 11 Tf 14 TL 1 0 0 1 54 740 Tm\n"
    for j, ln in enumerate(lines):
        content += (f"({esc(ln)}) Tj\n" if j == 0 else f"T* ({esc(ln)}) Tj\n")
    content += "ET"
    cb = content.encode()
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
            b"<< /Length %d >>\nstream\n" % len(cb) + cb + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out = b"%PDF-1.4\n"; offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offs: out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (len(objs) + 1, xref)
    open(path, "wb").write(out)

labvals = [("Total Cholesterol", 238, 125, 200), ("LDL Cholesterol", 168, 0, 100),
           ("HDL Cholesterol", 41, 40, 60), ("Triglycerides", 190, 0, 150),
           ("Glucose", 96, 70, 99), ("HbA1c", 6.0, 4.0, 5.6),
           ("Vitamin D", 24, 30, 100), ("TSH", 2.0, 0.4, 4.0)]
pdf_lines = ["QUEST DIAGNOSTICS - Comprehensive Metabolic + Lipid Panel",
             "Patient: J. Doe    Collected: 2025-11-05    Accession: 887-2231", ""]
for name, v, lo, hi in labvals:
    flag = "HIGH" if v > hi else ("LOW" if v < lo else "")
    pdf_lines.append(f"{name:<22} {v:>6}   ref {lo}-{hi}   {flag}")
make_pdf(os.path.join(d("labs"), "lab_report.pdf"), pdf_lines)
G["P1_out_of_range_count"] = int(sum(1 for _, v, lo, hi in labvals if v < lo or v > hi))
G["P1_ldl_value"] = next(v for n, v, lo, hi in labvals if n == "LDL Cholesterol")


# ---------------------------------------------------------------- zip archive
zp = os.path.join(d("export"), "takeout.zip")
ords = []
for i in range(30):
    ords.append({"date": (date(2025, 6, 1) + timedelta(days=int(rng.integers(0, 90)))).isoformat(),
                 "merchant": str(rng.choice(["A", "B", "C"])),
                 "amount": round(float(rng.uniform(10, 200)), 2)})
refunds = []
for o in ords:
    if rng.random() < 0.2:
        refunds.append({"order_date": o["date"], "amount": round(o["amount"] * 0.5, 2)})
buf = io.StringIO(); w = csv.writer(buf); w.writerow(["date", "merchant", "amount"])
for o in ords: w.writerow([o["date"], o["merchant"], o["amount"]])
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("orders.csv", buf.getvalue())
    z.writestr("refunds.json", json.dumps({"refunds": refunds}, indent=2))
G["Z1_total_orders"] = round(sum(o["amount"] for o in ords), 2)
G["Z1_total_refunds"] = round(sum(r["amount"] for r in refunds), 2)
G["Z1_net_spend"] = round(sum(o["amount"] for o in ords) - sum(r["amount"] for r in refunds), 2)


# ----------------------------------------------------------------
print(json.dumps(G, indent=2, default=str))
