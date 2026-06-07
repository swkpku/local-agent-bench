# Assessment — DABench-hard H5 (abalone, feature engineering + ML compare)

**Model:** gemma-4-12b-qat (UD-Q4_K_XL, thinking off) · **Harness:** pi 0.78.1 · **Date:** 2026-06-06 · **Wall:** 69 s · **Result: ✅ 3/3 (exact).**

H5 is the hardest task in the DABench-hard set (the suite "tops out" here), and gemma one-shot it:

```
@correlation_coefficient[0.9253]   gold 0.9253  ✅
@original_model_rmse[2.2192]       gold 2.2192  ✅
@volume_feature_model_rmse[2.2092] gold 2.2092  ✅
```

## Why this is a clean pass
- **Hit the instruction-following trap.** The gold only reproduces with `train_test_split(random_state=42)` (stated in the *constraint*, not the question) and the exact 7-column base feature set. gemma used both, so its RMSEs match to 4 decimals.
- **Reported the tiny improvement correctly.** Volume helps only `2.2192 → 2.2092`; the model kept 4 decimals, so the improvement is visible rather than rounded away.
- **Efficient.** 2 tool calls — `head -n 5` to inspect, then a single pandas/sklearn script — no thrashing. Correct output format (`@key[value]`, brackets intact, unlike its R5 run).

## Comparison
qwen3.5-9b was not run on H5 (its DABench set was H1/H2/H4). On this task gemma is flawless. Pairs with its S1 and P1 passes (same session) to show gemma is **strong on constrained single-file/single-tool analysis** — matching qwen's profile on H1/H2/H4.

## Scoring
Exact-match: **pass**. No `score_overall` rubric needed.
