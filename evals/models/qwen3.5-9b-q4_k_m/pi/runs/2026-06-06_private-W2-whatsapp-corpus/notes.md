# Assessment — Private-files W2 (50-chat corpus, ~10.8 GB) — DID NOT COMPLETE

**Model:** qwen3.5-9b-q4_k_m (Q4_K_M, thinking off) · **Harness:** pi 0.78.1 · **Date:** 2026-06-06 · **Wall:** 1088 s (~18 min) · **Tools:** 68 bash · **Result: ❌ no answer (0/8).**

qwen never produced the `@key[value]` lines. It ran **68 bash commands over ~18 minutes** and emitted **zero** final-answer text; the user interrupted ("are you doing the same thing?") and the run ended without a deliverable.

## The failure mode: a stuck loop
Of the 68 commands, **~67 were the same command** repeated:

```
find . -maxdepth 1 -name "*.txt" -exec wc -l {} +
```

- It tried to `wc -l` **every** file — including the ~1 GB ones — in one shot. Across **10.8 GB** that single call is very slow, and rather than adapt (stream per-file, sample, or move on) qwen **re-issued the identical command dozens of times**, never converging.
- **It ran `grep` zero times**, so it never even attempted the two needle facts (the gate code in one chat, the flight number in another) — the part of W2 that *requires* `grep -rl`.
- No final answer was ever assembled.

## Apple-to-apple — the opposite of gemma here
| | gemma-4-12b | qwen3.5-9b |
|---|---|---|
| tool calls | **8** | 68 |
| outcome | **5/8** (values right, 2 needle files mis-attributed, msg count doubled) | **0/8** — never answered |
| behavior | streamed efficiently, found needle *values* | looped on one slow `wc -l`, never grepped |

Same model class, same 10.8 GB task, **completely different agent behavior**: gemma got most of the way; qwen failed to converge. This is the clearest example in the set that, at 10 GB scale, **agent-loop robustness (recovering from a slow/failed command) matters as much as the model** — a small model that doesn't adapt its plan can burn the whole budget on one wrong approach.

## Scoring
**Incomplete — 0/8** (`status: DID NOT COMPLETE`). Not a wrong-answer failure but a no-answer failure: the loop never terminated with a deliverable. Worth a re-run with a tool-call cap + a nudge toward `grep -rl`/per-file streaming.
