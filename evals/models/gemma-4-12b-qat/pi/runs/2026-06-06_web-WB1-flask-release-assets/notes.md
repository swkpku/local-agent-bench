# Assessment — Web WB1 (variant): Flask 3.0.0 release asset count

**Model:** gemma-4-12b-qat (UD-Q4_K_XL, thinking off) · **Harness:** pi 0.78.1 · **Date:** 2026-06-06 · **Wall:** 42 s · **Result: ✅ correct (asked sub-question).**

```
Q: How many release assets does the pallets/flask 3.0.0 release have?  (+ the API URL)
Tool: curl -sL -m 20 "https://api.github.com/repos/pallets/flask/releases/tags/3.0.0" | jq '.assets | length'
A: "The pallets/flask 3.0.0 release has 3 assets."     gold @asset_count[3]  ✅
```

## The important signal
This run **proves gemma can fetch the live web** when pointed at a concrete URL: it picked `curl … | jq '.assets | length'` unprompted and got the right answer. That directly contradicts the excuse it gives on the open-ended growth-strategy task ("I do not have access to a web search tool"). The blocker there is **open-ended *search* / URL discovery**, not network access or tool availability — see the growth-strategy run.

## Caveats (why this is a "variant", not a full WB1)
- The prompt was a **simplified single-question** rephrase, not the standard 3-key WB1. Only `asset_count` was asked; `published_date` (2023-09-30) and `asset_size_sum` (789847) were not.
- The answer was **free prose**, not the `@asset_count[3]` format the grader expects.
- **Action item:** re-run the canonical WB1 prompt (and WB2/WB3) for a clean exact-match web-task row.

## Scoring
Correct on the asked question. Recorded as a 1-key pass with a variant flag in `meta.json`.
