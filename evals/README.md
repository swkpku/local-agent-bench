# Evals

A store for local-model evaluation runs, **organized by model + harness**. Each model+harness combo has its own perf profile (prefill/decode speed) and a set of individual runs (the model's actual output + per-run metrics).

## Layout

```
evals/
  README.md
  index.md                              # leaderboard: one row per run
  bench_perf.sh                         # measure exact prefill/decode vs a live llama-server
  models/
    <model-id>/                         # e.g. qwen3.5-9b-q4_k_m
      <harness>/                        # e.g. pi
        perf.json                       # prefill/decode tok/s for THIS model+harness on this machine
        runs/
          <YYYY-MM-DD_slug>/
            meta.json                   # structured per-run metrics (source of truth)
            prompt.md                   # exact input prompt
            report.md                   # the model's deliverable / answer
            transcript.jsonl            # raw pi session (full reproducibility)
            notes.md                    # qualitative assessment + scoring
```

Adding a new model or harness = a new folder at the right level. Same task can be compared across models by diffing their run folders.

## Key metrics we record

**Speed (model+harness level → `perf.json`)**
- `prefill_tokens_per_sec` — prompt-processing (prefill) throughput
- `decode_tokens_per_sec` — generation (decode) throughput
- runtime settings that affect them (ctx, flash-attn, KV quant, ubatch, threads)

**Per-run (`meta.json` → `metrics`)**
- `wall_clock_seconds`, `assistant_turns`
- `tool_calls_total`, `tool_calls_web_fetch`, `tool_results_with_data` / `_empty_or_blocked`, `web_search_success_rate`
- `output_tokens_total`, `final_total_tokens`, `peak_context_tokens`
- `prefill_tokens_per_sec`, `decode_tokens_per_sec` (per-run estimate), `effective_tokens_per_sec` (end-to-end incl. tool waits)
- `cost_usd` (0 for local)

**Quality (`meta.json` → `quality` + `notes.md`)**
- `score_overall` (null until a rubric is agreed), `issues[]`, completion of task requirements

## Measuring speed

- **Exact** (preferred): start the server (`make server`), then `bash evals/bench_perf.sh`. It reads llama-server's `/completion` `timings` and prints `prompt_per_second` (prefill) + `predicted_per_second` (decode). Paste into the combo's `perf.json` and flip `exact_benchmark.status` to `done`.
- **Estimated** (when only a transcript exists): least-squares fit `dt ≈ input/prefill_rate + output/decode_rate` across assistant turns, cross-checked on generation-heavy turns. This is how the first run's numbers were derived (server wasn't up).

## Capturing a new pi run

pi stores sessions at `~/.pi/agent/sessions/<cwd-slug>/<timestamp>_<id>.jsonl`. To log one: copy the JSONL into a new `models/<model>/<harness>/runs/<date_slug>/` as `transcript.jsonl`, extract `prompt.md` + `report.md`, and compute `meta.json` from the transcript's `usage` blocks and timestamps. (Ask Claude: "store the latest pi run as an eval".)

## Relation to `bench/`

`bench/` = **task definitions + gold answers** (the questions). `evals/` = **run results** (what a model did). Exact-match `bench/` tasks yield pass/fail; open-ended tasks yield a qualitative score.
