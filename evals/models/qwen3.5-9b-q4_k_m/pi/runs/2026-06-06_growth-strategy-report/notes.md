# Assessment — growth-strategy report run

**Model:** qwen3.5-9b-q4_k_m (Q4_K_M GGUF, thinking off) · **Harness:** pi 0.78.1 · **Date:** 2026-06-06 · **Wall clock:** ~72 min

## What it did well
- **Followed the structure.** Hit all 6 requested sections (market map, trends, code scoring model, top-5 opportunities, per-opportunity detail, final pick).
- **Actually wrote and ran code.** Built a 6-criteria weighted scoring framework in Python via the `bash` tool — the "quantitative model" requirement was met for real, not faked.
- **Reasonable output despite a 9B/Q4 model.** Coherent, on-topic, recommendation is defensible and well-argued (invoice automation: high pain, low data risk).

## Where it fell down (the important part for evals)
- **"Web search" was mostly theater.** The model has no real search tool, so it `curl`'d **guessed URLs** (crunchbase/statista/gartner/mckinsey/bcg/cbinsights/reddit/producthunt) and grepped the HTML. **5 of 14** tool calls returned nothing or "blocked". Only `api.github.com` returned real data (55 repos).
- **Fabricated precise statistics.** Figures like "+340% YoY", "67% of SMBs prefer industry-specific tools", "82% use 5+ disconnected tools" appear nowhere in any retrieved result — they're invented. This directly violates the prompt's "distinguish evidence from assumptions / avoid hype" instruction.
- **No citations**, though explicitly requested.

## Takeaway
A good test of *instruction-following + code use* (passes), but a poor test of *grounded research* on this harness — the local setup has no real search backend, so the model confabulates authority. **Action item:** give pi a genuine search/fetch tool (e.g. the pinned `web-tasks/` pattern, or a real search API) before trusting any "research" output. Until then, treat statistics in these reports as unsourced.

## Scoring
Left `score_overall` null in `meta.json` — set a 1–5 once we agree a rubric (suggest: structure 1–5, code 1–5, grounding 1–5, honesty 1–5). On grounding/honesty this run is a **2/5**; on structure/code a **4/5**.
