# Web tasks — fetch + extract from the live web

3 tasks that force the agent to actually go to the internet — a fact it cannot answer from the local model's weights. Each target is an **immutable URL** (a release tag, a fixed Wikipedia revision id, a fixed commit SHA), so the answer is frozen forever and exact-match gradable, while the agent still has to fetch and parse it.

**Tool:** the agent needs network access (e.g. `curl`/`requests`) plus `jq` or Python to parse JSON/CSV. If your harness blocks outbound network, these won't run — that's itself a useful signal about the agent's capabilities. Grade `@key[value]` against `ANSWER_KEY.md`; re-confirm the pins anytime with `bash bench/web-tasks/verify.sh`.

| Task | Source | Format / tool |
|---|---|---|
| **WB1** | GitHub Releases API (pinned tag) | JSON / `curl`+`jq` |
| **WB2** | Wikipedia REST (fixed revision id) | JSON / `curl`+`jq` |
| **WB3** | raw CSV at a fixed commit SHA | CSV / `curl`+pandas |

---

## WB1 — GitHub release metadata (JSON API)
```text
You are a web research agent. Fetch the URL below and parse the JSON to answer. Follow constraints exactly; output each answer line in the exact format, nothing else.

URL: https://api.github.com/repos/pallets/flask/releases/tags/3.0.0
Question: On what date was this release published, how many release assets does it have, and what is the combined byte size of all its assets?
Constraints: published_date is the date part (YYYY-MM-DD) of the published_at field. asset_count is the number of items in the assets array. asset_size_sum is the sum of the "size" field over every asset (in bytes, an integer).
Answer format: @published_date[YYYY-MM-DD]
@asset_count[n]
@asset_size_sum[bytes]
where n and bytes are integers.
```

## WB2 — Wikipedia fixed revision (REST API)
```text
You are a web research agent. Fetch the URL below and parse the JSON to answer. Follow constraints exactly; output each answer line in the exact format.

URL: https://en.wikipedia.org/w/rest.php/v1/revision/512000000
Question: This is a specific frozen revision of a Wikipedia article. What is the title of the page it belongs to, the username of the editor who made this revision, and the byte size of this revision?
Constraints: page_title is the page.title field. editor is the user.name field. size is the size field (an integer, in bytes).
Answer format: @page_title[title]
@editor[username]
@size[bytes]
where title and username are strings exactly as returned and bytes is an integer.
```

## WB3 — pinned raw CSV, fetch + compute
```text
You are a web research agent. Download the CSV at the URL below (it is pinned to a fixed commit, so it never changes) and compute the answer with pandas. Follow constraints exactly; output each answer line in the exact format.

URL: https://raw.githubusercontent.com/mwaskom/seaborn-data/799924f46906146ad36b8b1c27d83e51dd8b411a/tips.csv
Question: How many rows are in this dataset, what is the sum of the total_bill column, and what is the mean of the tip column?
Constraints: row_count excludes the header. total_bill_sum and mean_tip are rounded to two decimal places.
Answer format: @row_count[n]
@total_bill_sum[amount]
@mean_tip[amount]
where n is an integer and the amounts are floats rounded to two decimals.
```
