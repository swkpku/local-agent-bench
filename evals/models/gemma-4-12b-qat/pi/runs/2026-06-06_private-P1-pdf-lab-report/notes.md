# Assessment — Private-files P1 (PDF lab report via pdftotext)

**Model:** gemma-4-12b-qat (UD-Q4_K_XL, thinking off) · **Harness:** pi 0.78.1 · **Date:** 2026-06-06 · **Wall:** 11 s · **Result: ✅ 2/2 (exact).**

```
@out_of_range_count[5]   gold 5    ✅
@ldl_value[168]          gold 168  ✅
```

## Why this is a clean pass
- **Reached for the right CLI tool.** P1 is the real "different tool" test: there is **no PDF Python library** on the box, so a model that only tries `import pypdf` fails. gemma went straight to `pdftotext -layout <file> -` (poppler) in one `bash` call, parsed the rendered text, and answered.
- **Counted flags correctly.** 5 results flagged HIGH/LOW, and read the LDL value (168) off the layout. One tool call, 11 s — the fastest run in the set.

## Comparison
Not run on qwen3.5-9b. Together with S1 (SQLite) and H5 (pandas/sklearn) — all in the same session — this shows gemma **picks the correct tool per file format** and parses cleanly. Same `pdftotext -layout` skill is exercised at much larger scale (and partially breaks) in the R5 run.

## Scoring
Exact-match: **pass**.
