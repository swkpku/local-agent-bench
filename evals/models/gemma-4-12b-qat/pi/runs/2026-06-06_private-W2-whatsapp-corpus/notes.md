# Assessment — Private-files W2 (50-chat corpus, ~10.8 GB, streaming + needles)

**Model:** gemma-4-12b-qat (UD-Q4_K_XL, thinking off) · **Harness:** pi 0.78.1 · **Date:** 2026-06-06 · **Wall:** 1177 s (~20 min) · **Tools:** 8 bash · **Result: ⚠️ 5/8.**

```
@group_count           50                          gold 50                       ✅
@total_messages        526026957                   gold 263013454                ❌ (≈ 2×)
@largest_group_file    49_dog_park_regulars.txt    gold 49_dog_park_regulars.txt ✅
@total_dinner_mentions 32876080                    gold 32876080                 ✅ (exact)
@gate_code             7392                         gold 7392                     ✅
@gate_code_file        49_dog_park_regulars.txt     gold 16_class_of_2015.txt     ❌
@flight_number         DL 1474                      gold DL 1474                  ✅
@flight_file           49_dog_park_regulars.txt     gold 33_bridal_party.txt      ❌
```

## What it did well — and it's not trivial
The corpus is **~10.8 GB across 50 files**, several individually larger than any context window (the largest is ~0.98 GB). gemma worked it with **streaming tools only** and got the genuinely hard parts right:
- **`total_dinner_mentions = 32876080` — exact.** A `grep -ic 'dinner'` summed across 50 files, including the ~1 GB one, with no off-by-anything. That it streamed the giant files instead of trying to open them is the whole point of W2, and it passed.
- **Largest file** correct (`du`/`ls -S`), **group_count** correct, and it **found both needle values** — gate code `7392` and flight `DL 1474` — via grep across the corpus.

## The failure pattern (interesting)
gemma found the needle *values* but botched the *file attribution* and the *line arithmetic*:
- **`gate_code_file` and `flight_file` both = `49_dog_park_regulars.txt`** (the largest file) instead of the true `16_class_of_2015.txt` / `33_bridal_party.txt`. Same wrong answer for both ⇒ it grep'd the value without `grep -rl`/filename tracking and defaulted to reporting the largest file it had already identified. A `grep -rl 'gate code'` would have returned the right filename directly.
- **`total_messages` = 526026957 ≈ 2 × 263013454.** The ~2× ratio is the tell: it double-counted — most likely summed `wc -l` without subtracting the one banner line per file *and* counted twice, rather than `sum(line_count − 1)`.

## Takeaway
Scale handling is real (didn't choke on the 1 GB file; exact global `grep -ic`). The misses are (a) needle→file attribution and (b) banner-subtraction arithmetic — both fixable with `grep -rl` and a cleaner line-count formula. Bracket format was correct here (contrast R5).

## Scoring
**5/8** (pass=false). The three misses are `total_messages`, `gate_code_file`, `flight_file`.
