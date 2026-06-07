# Web tasks — answer key

Captured from the pinned (immutable) URLs. Re-confirm anytime with `bash bench/web-tasks/verify.sh`. Grade `@key[value]`; don't put these in the prompt.

| Task | Source | Keys (gold) |
|---|---|---|
| **WB1** | Flask 3.0.0 release API | `@published_date[2023-09-30]`, `@asset_count[3]`, `@asset_size_sum[789847]` |
| **WB2** | Wikipedia revision 512000000 | `@page_title[Elvis Presley (album)]`, `@editor[Tomcat7]`, `@size[25780]` |
| **WB3** | seaborn-data tips.csv @ `799924f` | `@row_count[244]`, `@total_bill_sum[4827.77]`, `@mean_tip[3.0]` |

## What each task probes

- **WB1** — pure tool-use gate: the model cannot know a release's asset byte-sizes from memory, so a correct answer **proves it fetched**. Tests JSON traversal (`assets[].size` summed) vs. just reading a top-level field.
- **WB2** — the question deliberately doesn't name the article; the only way to get the title is to hit the fixed revision id. Distinguishes "the agent searched the live API" from "the agent guessed."
- **WB3** — web + analysis combined: fetch a remote CSV pinned to a commit SHA, then compute aggregates. The SHA pin means `master` can move without changing the answer.

## Why pinned URLs

Open-web "search for X" has no stable gold — the page changes, ranking changes, and the model may answer from parametric memory without searching. Pinning to a **release tag / fixed revision id / commit SHA** freezes the content forever, so:
1. the answer is exact-match gradable, and
2. the agent is *forced* to fetch (the value isn't in its training data, or isn't knowable without the specific pin).

## Notes / extending
- These require outbound network in the harness. If the agent can't reach the internet, that's a real capability boundary worth recording — not a task bug.
- For a true open-ended *search* test (formulate query → search engine → synthesize), grading needs either a manual check or a question with a single stable canonical answer. Say the word and I'll add a small set of those, with a rubric instead of exact-match.
- Sibling suites: `private-files/` (format/tool axis, offline), `private-tasks/` (private analysis on CSV), `dabench-mini` / `dabench-hard` (academic benchmark).
