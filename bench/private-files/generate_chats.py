#!/usr/bin/env python3
"""
Generate a CORPUS of many realistic WhatsApp-style group chats whose file sizes
span a wide range (default: 50 groups, log-spread from 10 MB to ~1 GB), and
compute per-group + corpus-wide gold by STREAMING (so it scales to many GB
without ever holding a chat in memory). Writes a manifest.json (the answer key)
and an INDEX.md. Seeded -> reproducible for a given (--groups, --min-mb, --max-gb,
--seed). All data is synthetic.

This is the SCALE pressure test (task W2): dozens of exports, several too big to
open, so the agent must work across files with streaming tools (grep -rl, wc,
awk, du) — find the largest, aggregate counts, and locate a one-off fact that
lives in exactly ONE of the chats.

  Layout per file:  MM/DD/YY, HH:MM - Sender: message   (line 1 = system banner)
  Corpus dir:       messages/group_chats/NN_slug.txt + manifest.json + INDEX.md

Examples:
  python3 bench/private-files/generate_chats.py                 # 50 groups, 10MB..1GB (~11 GB)
  python3 bench/private-files/generate_chats.py --max-gb 0.2    # cap the biggest at 200 MB (~2.4 GB)
  python3 bench/private-files/generate_chats.py --groups 60 --min-mb 5
  python3 bench/private-files/generate_chats.py --groups 8 --min-mb 1 --max-gb 0.02  # tiny smoke test
Needs only the Python stdlib. The corpus dir is git-ignored (it can be tens of GB).
"""
import argparse, json, os, random, re, sys, time
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
AVG_BYTES = 42                                  # measured bytes/line -> size<->message-count
SPAN_SECONDS = int(4.5 * 365.25 * 86400)        # every chat spans ~4.5 yrs (2021->2025) so dates look real

GROUP_NAMES = [
    "Cabin Trip", "Family", "Work Eng Team", "College Crew", "Soccer Sundays", "Book Club",
    "Neighborhood Watch", "Wedding Planning", "Roommates", "Hiking Buddies", "Fantasy Football",
    "Moms Group", "DnD Party", "Gym Crew", "Foodies", "Travel Squad", "Class of 2015", "Cousins",
    "Poker Night", "Climbing Gym", "Band Practice", "Startup Founders", "PTA Volunteers",
    "Running Club", "Game Night", "Brunch Bunch", "Ski Trip 2024", "Apartment 4B", "Lake House",
    "Camping Crew", "Choir", "Coding Study Group", "New Parents", "Bridal Party", "Groomsmen",
    "Office Lunch", "Volleyball League", "Photography Club", "Wine Tasting", "Trivia Team",
    "Beach House", "Pet Owners", "Investment Club", "Garden Club", "Yoga Friends", "Movie Buffs",
    "Road Trip", "Knitting Circle", "Chess Club", "Dog Park Regulars", "High School Reunion",
    "Marathon Training", "Potluck Planning", "Karaoke Night", "Surf Crew", "Cycling Club",
    "Coffee Lovers", "Tech Meetup", "Hometown Friends", "Volunteer Squad",
]
NAME_POOL = ["Priya", "Marcus", "Lena", "Diego", "Aisha", "Tom", "Nina", "Sam", "Maya", "Leo",
             "Zoe", "Omar", "Hana", "Carlos", "Ruby", "Ethan", "Yuki", "Noah", "Ivy", "Raj",
             "Mia", "Ben", "Ada", "Kofi", "Sofia", "Liam", "Chen", "Tara", "Jose", "Ella",
             "Kai", "Anna", "Mateo", "Grace", "Hugo", "Nora", "Ravi", "Lily", "Theo", "Jade", "You"]
POOL = [
    "sounds good", "haha same", "on my way", "running 10 min late", "who's bringing snacks?",
    "can't wait!", "lol", "ok cool", "see you there", "thanks!", "did everyone pack?",
    "weather looks great this weekend", "I'll drive", "what time are we leaving?", "brunch first?",
    "anyone up for a hike?", "I booked it", "send me the address", "Venmo me when you can",
    "got the groceries 🛒", "so excited 🎉", "my back hurts from the drive", "the view is unreal 😍",
    "coffee run, want anything?", "movie night?", "I forgot my charger ugh", "be there in 20",
    "traffic is brutal", "almost home", "good morning ☀️", "night all", "that was fun!",
    "let's do this again", "pics please!", "who has the aux", "save me a seat", "call me when free",
    "yep", "nope", "maybe later", "sounds like a plan", "count me in", "I'll bring wine 🍷",
    "is it cold up there?", "bring a jacket", "see you at the trailhead", "great idea", "I'm down",
    "no worries", "dinner at 7?", "let's do dinner tomorrow", "I'm in for dinner",
    "leftovers for dinner tonight", "let's plan dinner for saturday", "I'm starving, dinner soon?",
    "dinner's ready!",
]
DINNER_SET = {i for i, m in enumerate(POOL) if "dinner" in m.lower()}
BANNER = ("Messages and calls are end-to-end encrypted. No one outside of this chat, "
          "not even WhatsApp, can read or listen to them.")
GATE_TEXT = "Reminder for the trip: the cabin gate code is 7392. Please don't post it anywhere public."
GATE_CODE = "7392"
FLIGHT_TEXT = "Just booked - my flight is DL 1474, arrives Friday 6:05pm. Can someone grab me from the airport?"
FLIGHT_NUMBER = "DL 1474"


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def gen_group(path, n, seed, plant_gate=False, plant_flight=False, progress=False):
    rnd = random.Random(seed)
    k = rnd.randint(4, 12)
    members = rnd.sample(NAME_POOL, k)                 # cast; members[0] is dominant
    weights = [30] + [max(2, 18 - 2 * i) for i in range(k - 1)]
    cw, tot = [], 0
    for w in weights:
        tot += w
        cw.append(tot)
    mean_gap = max(2, SPAN_SECONDS // max(n, 1))
    plant = {}
    if plant_gate:
        plant[int(n * 0.40)] = GATE_TEXT
    if plant_flight:
        plant[int(n * 0.62)] = FLIGHT_TEXT

    sender_ct = [0] * k
    day_ct, dinner = {}, 0
    dt = datetime(2021, 1, 1, 8, 0, 0)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"12/31/20, 23:59 - {BANNER}\n")
        buf = []
        for i in range(n):
            dt += timedelta(seconds=rnd.randint(1, 2 * mean_gap))
            r = rnd.random() * tot
            si = 0
            while cw[si] < r:
                si += 1
            sender_ct[si] += 1
            sender = members[si]
            if i in plant:
                text = plant[i]
            else:
                pi = rnd.randrange(len(POOL))
                text = POOL[pi]
                if pi in DINNER_SET:
                    dinner += 1
            dkey = f"{dt.month:02d}/{dt.day:02d}/{dt.year % 100:02d}"
            day_ct[dkey] = day_ct.get(dkey, 0) + 1
            buf.append(f"{dkey}, {dt.hour:02d}:{dt.minute:02d} - {sender}: {text}\n")
            if len(buf) >= 65536:
                f.write("".join(buf)); buf.clear()
                if progress:
                    sys.stderr.write(f"\r    {os.path.basename(path):28} {100*(i+1)/n:5.1f}%")
                    sys.stderr.flush()
        if buf:
            f.write("".join(buf))
    if progress:
        sys.stderr.write("\r" + " " * 48 + "\r")
    return {
        "file": os.path.basename(path),
        "bytes": os.path.getsize(path),
        "messages": n,
        "members": members,
        "top_sender": members[max(range(k), key=lambda j: sender_ct[j])],
        "dinner_mentions": dinner,
        "busiest_day": max(day_ct, key=day_ct.get),
        "has_gate": plant_gate,
        "has_flight": plant_flight,
    }


def reverify(path):
    line_re = re.compile(r"^\d\d/\d\d/\d\d, \d\d:\d\d - ([^:]+): (.*)$")
    total = dinner = 0
    sender_ct, day_ct = {}, {}
    gate = flight = None
    with open(path, encoding="utf-8") as f:
        next(f)
        for ln in f:
            m = line_re.match(ln)
            if not m:
                continue
            total += 1
            s, text = m.group(1), m.group(2)
            sender_ct[s] = sender_ct.get(s, 0) + 1
            if "dinner" in text.lower():
                dinner += 1
            day_ct[ln[:8]] = day_ct.get(ln[:8], 0) + 1
            if "gate code is" in text:
                gate = re.search(r"gate code is (\d+)", text).group(1)
            if "flight is" in text:
                flight = re.search(r"flight is ([A-Z]{2} \d+)", text).group(1)
    return {"messages": total, "top_sender": max(sender_ct, key=sender_ct.get),
            "dinner_mentions": dinner, "busiest_day": max(day_ct, key=day_ct.get),
            "gate": gate, "flight": flight}


def main():
    ap = argparse.ArgumentParser(description="Generate a corpus of group chats (task W2).")
    ap.add_argument("--groups", type=int, default=50)
    ap.add_argument("--min-mb", type=float, default=10.0)
    ap.add_argument("--max-gb", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=20260606)
    ap.add_argument("--outdir", default=os.path.join(BASE, "messages", "group_chats"))
    ap.add_argument("--verify", choices=["none", "sample", "all"], default="sample")
    a = ap.parse_args()

    n_groups = max(a.groups, 2)
    lo_b, hi_b = a.min_mb * 1e6, a.max_gb * 1e9
    # log-spread byte targets -> message counts
    counts = [max(100, int(round(lo_b * (hi_b / lo_b) ** (i / (n_groups - 1)) / AVG_BYTES)))
              for i in range(n_groups)]
    grnd = random.Random(a.seed)
    names = (GROUP_NAMES * (n_groups // len(GROUP_NAMES) + 1))[:n_groups]
    gate_idx = n_groups // 3              # one chat hides the gate code
    flight_idx = (2 * n_groups) // 3      # a different chat hides the flight number

    os.makedirs(a.outdir, exist_ok=True)
    for old in os.listdir(a.outdir):
        if old.endswith(".txt") or old in ("manifest.json", "INDEX.md"):
            os.remove(os.path.join(a.outdir, old))

    total_b = sum(counts) * AVG_BYTES
    print(f"# corpus: {n_groups} groups | sizes ~{counts[0]*AVG_BYTES/1e6:.0f} MB .. "
          f"{counts[-1]*AVG_BYTES/1e9:.2f} GB | est total ~{total_b/1e9:.1f} GB | seed {a.seed}")
    t0 = time.time()
    groups = []
    for i, (name, n) in enumerate(zip(names, counts)):
        fn = f"{i:02d}_{slug(name)}.txt"
        big = n * AVG_BYTES > 5e7
        g = gen_group(os.path.join(a.outdir, fn), n, a.seed + 1 + i,
                      plant_gate=(i == gate_idx), plant_flight=(i == flight_idx), progress=big)
        g["name"] = name
        groups.append(g)
        done_b = sum(x["bytes"] for x in groups)
        sys.stderr.write(f"  [{i+1:>2}/{n_groups}] {fn:30} {g['bytes']/1e6:8.1f} MB  "
                         f"({done_b/1e9:.2f} GB, {time.time()-t0:.0f}s)\n")

    largest = max(groups, key=lambda g: g["bytes"])
    gate_g = next(g for g in groups if g["has_gate"])
    flight_g = next(g for g in groups if g["has_flight"])
    corpus = {
        "group_count": len(groups),
        "total_messages": sum(g["messages"] for g in groups),
        "total_bytes": sum(g["bytes"] for g in groups),
        "total_dinner_mentions": sum(g["dinner_mentions"] for g in groups),
        "largest_group_file": largest["file"],
        "largest_group_name": largest["name"],
        "gate_code": GATE_CODE,
        "gate_code_file": gate_g["file"],
        "flight_number": FLIGHT_NUMBER,
        "flight_file": flight_g["file"],
    }
    manifest = {"corpus": corpus, "params": vars(a), "groups": groups}
    with open(os.path.join(a.outdir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    with open(os.path.join(a.outdir, "INDEX.md"), "w") as f:
        f.write(f"# Group-chat corpus ({len(groups)} groups)\n\n")
        f.write("| # | file | size | messages | top sender | dinner | needle |\n|--|--|--|--|--|--|--|\n")
        for i, g in enumerate(groups):
            nd = "GATE" if g["has_gate"] else ("FLIGHT" if g["has_flight"] else "")
            f.write(f"| {i} | {g['file']} | {g['bytes']/1e6:.1f} MB | {g['messages']:,} | "
                    f"{g['top_sender']} | {g['dinner_mentions']:,} | {nd} |\n")

    print("\n# CORPUS GOLD (task W2):")
    print(json.dumps(corpus, indent=2))
    print(f"# wrote {len(groups)} files + manifest.json + INDEX.md to {a.outdir}")
    print(f"# total {corpus['total_bytes']/1e9:.2f} GB in {time.time()-t0:.0f}s")

    if a.verify != "none":
        idxs = sorted(set([0, 1, len(groups) - 1, gate_idx, flight_idx]
                          if a.verify == "sample" else range(len(groups))))
        print(f"\n# re-verify ({a.verify}: {len(idxs)} files streamed back from disk):")
        ok = True
        for i in idxs:
            g = groups[i]
            got = reverify(os.path.join(a.outdir, g["file"]))
            checks = [got["messages"] == g["messages"], got["top_sender"] == g["top_sender"],
                      got["dinner_mentions"] == g["dinner_mentions"],
                      (got["gate"] == GATE_CODE) == g["has_gate"],
                      (got["flight"] == FLIGHT_NUMBER) == g["has_flight"]]
            good = all(checks)
            ok &= good
            print(f"#   {g['file']:30} msgs={got['messages']:>10,}  top={got['top_sender']:<7}  "
                  f"dinner={got['dinner_mentions']:>9,}  {'OK' if good else 'FAIL <<<'}")
        print("# ALL OK ✓" if ok else "# MISMATCH ✗")
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()
