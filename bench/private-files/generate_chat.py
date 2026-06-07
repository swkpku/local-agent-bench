#!/usr/bin/env python3
"""
Generate a REALISTIC, arbitrarily LARGE WhatsApp-style group-chat export and
compute the gold answers by STREAMING (so it works at 1 GB without ever holding
the chat in memory). Then it re-streams the written file to prove the on-disk
bytes reproduce the gold. Seeded -> reproducible for a given (--messages, --seed).

This is the "needle in a huge haystack" pressure test (task W2): the file is far
too big to read into a model's context, so the agent MUST reach for streaming
tools (grep / wc / awk / sort / a line-by-line loop) rather than slurping it.

  Format (WhatsApp Android export):  MM/DD/YY, HH:MM - Sender: message
  Line 1 is the system "end-to-end encrypted" banner (not a message).

Gold answers:
  total_messages   exact message count (system banner excluded)
  top_sender       most frequent sender (Priya, by construction)
  dinner_mentions  messages whose text contains 'dinner' (case-insensitive)
  busiest_day      MM/DD/YY with the most messages (a planted burst day)
  gate_code        a fact stated exactly once  -> grep 'gate code'
  flight_number    a fact stated exactly once  -> grep -i 'flight'

Examples:
  python3 bench/private-files/generate_chat.py                 # ~1,000,000 msgs (~85 MB)
  python3 bench/private-files/generate_chat.py --gb 1          # ~1 GB
  python3 bench/private-files/generate_chat.py --mb 200        # ~200 MB
  python3 bench/private-files/generate_chat.py --messages 5000 # tiny, for a quick check
Needs only the Python stdlib. Output is git-ignored (it can be huge).
"""
import argparse, os, random, sys, time
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
AVG_BYTES = 42                      # measured bytes/line; only maps --gb/--mb -> message count

SENDERS = ["Priya", "Marcus", "Lena", "Diego", "Aisha", "Tom", "Nina", "You"]
WEIGHTS = [22, 16, 14, 12, 10, 9, 9, 8]      # Priya dominant -> deterministic top_sender

# message pool (no 'flight', no 'gate code', no 'wifi', no 4-digit codes -> needles stay unique)
POOL = [
    "sounds good", "haha same", "on my way", "running 10 min late", "who's bringing snacks?",
    "can't wait!", "lol", "ok cool", "see you there", "thanks!", "did everyone pack?",
    "weather looks great this weekend", "I'll drive", "what time are we leaving?",
    "brunch first?", "anyone up for a hike?", "I booked the cabin", "send me the address",
    "Venmo me when you can", "got the groceries 🛒", "so excited 🎉", "my back hurts from the drive",
    "the view is unreal 😍", "coffee run, want anything?", "movie night?", "I forgot my charger ugh",
    "be there in 20", "traffic is brutal", "almost home", "good morning ☀️", "night all",
    "that was fun!", "let's do this again", "pics please!", "who has the aux",
    "save me a seat", "call me when free", "yep", "nope", "maybe later", "sounds like a plan",
    "count me in", "I'll bring wine 🍷", "is it cold up there?", "bring a jacket",
    "see you at the trailhead", "great idea", "I'm down", "no worries",
    # 'dinner' lines (the counted keyword):
    "dinner at 7?", "let's do dinner tomorrow", "I'm in for dinner", "leftovers for dinner tonight",
    "let's plan dinner for saturday", "I'm starving, dinner soon?", "dinner's ready!",
]
DINNER = [i for i, m in enumerate(POOL) if "dinner" in m.lower()]
DINNER_SET = set(DINNER)

BANNER = ("Messages and calls are end-to-end encrypted. No one outside of this chat, "
          "not even WhatsApp, can read or listen to them.")


def needles(n):
    """Plant 3 unique facts at deterministic positions (2 are graded)."""
    return {
        int(n * 0.21): ("Priya", "Reminder for the trip: the cabin gate code is 7392. "
                                 "Please don't post it anywhere public."),
        int(n * 0.50) - 1: ("Marcus", "Quick heads up, big planning push starting now 👇"),
        int(n * 0.58): ("Diego", "Just booked - my flight is DL 1474, arrives Friday 6:05pm. "
                                 "Can someone grab me from the airport?"),
        int(n * 0.83): ("Lena", "Cabin wifi password is granite-otter-58 once you get there."),
    }


def cum(weights):
    out, s = [], 0
    for w in weights:
        s += w
        out.append(s)
    return out, s


def gen(path, n, seed):
    rnd = random.Random(seed)
    cw, total_w = cum(WEIGHTS)
    plant = needles(n)
    burst_start = int(n * 0.50)
    burst_len = max(3000, n // 150)            # a clearly-busiest "event" day
    burst_end = burst_start + burst_len

    sender_ct = [0] * len(SENDERS)
    day_ct = {}
    dinner = 0
    gold_needle = {}
    dt = datetime(2021, 1, 1, 8, 0, 0)
    t0 = time.time()

    with open(path, "w", encoding="utf-8") as f:
        # WhatsApp banner line (a day before the first message; not a message)
        f.write(f"12/31/20, 23:59 - {BANNER}\n")
        buf = []
        for i in range(n):
            # advance the clock (tight gaps during the burst so they land on one day)
            if i == burst_start:
                dt = dt.replace(hour=9, minute=0, second=0)
            dt += timedelta(seconds=(2 if burst_start <= i < burst_end else rnd.randint(5, 180)))

            if i in plant:
                sender, text = plant[i]
                if "gate code" in text:
                    gold_needle["gate_code"] = "7392"
                if "flight is" in text:
                    gold_needle["flight_number"] = "DL 1474"
            else:
                r = rnd.random() * total_w
                si = 0
                while cw[si] < r:
                    si += 1
                sender = SENDERS[si]
                pi = rnd.randrange(len(POOL))
                text = POOL[pi]
                if pi in DINNER_SET:
                    dinner += 1
            si = SENDERS.index(sender)
            sender_ct[si] += 1

            dkey = f"{dt.month:02d}/{dt.day:02d}/{dt.year % 100:02d}"
            day_ct[dkey] = day_ct.get(dkey, 0) + 1
            buf.append(f"{dkey}, {dt.hour:02d}:{dt.minute:02d} - {sender}: {text}\n")

            if len(buf) >= 65536:
                f.write("".join(buf)); buf.clear()
                if n >= 2_000_000:
                    pct = 100 * (i + 1) / n
                    sys.stderr.write(f"\r  generating... {pct:5.1f}%  ({i + 1:,}/{n:,})")
                    sys.stderr.flush()
        if buf:
            f.write("".join(buf))
    if n >= 2_000_000:
        sys.stderr.write("\n")

    top = SENDERS[max(range(len(SENDERS)), key=lambda k: sender_ct[k])]
    busiest = max(day_ct, key=day_ct.get)
    gold = {
        "total_messages": n,
        "top_sender": top,
        "dinner_mentions": dinner,
        "busiest_day": busiest,
        "gate_code": gold_needle.get("gate_code"),
        "flight_number": gold_needle.get("flight_number"),
    }
    size = os.path.getsize(path)
    print(f"# wrote {path}")
    print(f"#   {n:,} messages | {size:,} bytes (~{size / 1e6:.1f} MB) | "
          f"{time.time() - t0:.1f}s | seed {seed}")
    print(f"#   sender counts: " + ", ".join(f"{s}={c:,}" for s, c in zip(SENDERS, sender_ct)))
    return gold


def reverify(path, gold):
    """Independently re-derive the gold by streaming the written file."""
    import re
    line_re = re.compile(r"^\d\d/\d\d/\d\d, \d\d:\d\d - ([^:]+): (.*)$")
    total = dinner = 0
    sender_ct, day_ct = {}, {}
    gate = flight = None
    with open(path, encoding="utf-8") as f:
        next(f)                                          # skip banner
        for ln in f:
            m = line_re.match(ln)
            if not m:
                continue
            total += 1
            sender, text = m.group(1), m.group(2)
            sender_ct[sender] = sender_ct.get(sender, 0) + 1
            if "dinner" in text.lower():
                dinner += 1
            day = ln[:8]
            day_ct[day] = day_ct.get(day, 0) + 1
            if "gate code is" in text:
                gate = re.search(r"gate code is (\d+)", text).group(1)
            if "flight is" in text:
                flight = re.search(r"flight is ([A-Z]{2} \d+)", text).group(1)
    got = {
        "total_messages": total,
        "top_sender": max(sender_ct, key=sender_ct.get),
        "dinner_mentions": dinner,
        "busiest_day": max(day_ct, key=day_ct.get),
        "gate_code": gate,
        "flight_number": flight,
    }
    print("\n# re-verify (streamed back from the file on disk):")
    ok = True
    for k in gold:
        match = gold[k] == got[k]
        ok &= match
        print(f"#   {k:<16} gold={str(gold[k]):<12} file={str(got[k]):<12} {'OK' if match else 'FAIL <<<'}")
    print("# ALL OK ✓" if ok else "# MISMATCH ✗")
    return ok


def main():
    ap = argparse.ArgumentParser(description="Generate a large WhatsApp-style group chat (task W2).")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--messages", type=int, help="exact number of messages (default 1,000,000)")
    g.add_argument("--gb", type=float, help="approximate target size in gigabytes")
    g.add_argument("--mb", type=float, help="approximate target size in megabytes")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default=os.path.join(BASE, "messages", "group_chat.txt"))
    ap.add_argument("--no-verify", action="store_true", help="skip the re-stream self-check")
    a = ap.parse_args()

    if a.gb is not None:
        n = int(a.gb * 1e9 / AVG_BYTES)
    elif a.mb is not None:
        n = int(a.mb * 1e6 / AVG_BYTES)
    else:
        n = a.messages or 1_000_000
    n = max(n, 100)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    gold = gen(a.out, n, a.seed)
    print("\n# GOLD (task W2):")
    import json
    print(json.dumps(gold, indent=2))
    if not a.no_verify:
        if not reverify(a.out, gold):
            sys.exit(1)


if __name__ == "__main__":
    main()
