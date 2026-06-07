# Local-model working rules (appended to pi's defaults)

This model has no prompt caching: the entire conversation is re-read on every
turn, so keep context lean. Prioritize these rules.

## Data files are data, not context
- Never `read` dataset files into the conversation (.csv, .tsv, .parquet,
  .xlsx, .jsonl, large .json, .log). Reading them wastes context every turn.
- Inspect them with `bash` instead: `head -5 file.csv`, `wc -l file.csv`, or
  `python3 -c "import pandas as pd; d=pd.read_csv('f'); print(d.shape, d.head())"`.
- Answer data questions by computing with `bash` (pandas / duckdb / awk) and
  reporting only the result — never by loading the data into the prompt.
- (Small config files like package.json, tsconfig, *.yaml are fine to read.)

## Read narrowly
- Don't read a whole source file over ~300 lines. `grep` for the symbol or
  section first, then `read` with `offset`/`limit` for just those lines.
- Use `grep` / `find` / `ls` to navigate — don't open files to find things.
- Never re-read something already shown earlier in this conversation.

## Web access (use the `bash` tool with `curl`; you have no `web_search` function)
- Never reply that you can't access the web, and never guess article URLs.
- SEARCH first with DuckDuckGo (Google blocks curl with a JS wall). Run this,
  changing only the query; it prints the top hits as `title -> url`:

```
curl -sL -m 20 -A "Mozilla/5.0" -G --data-urlencode "q=YOUR QUERY" "https://html.duckduckgo.com/html/" | python3 -c 'import sys,re,html,urllib.parse as U;t=sys.stdin.read();[print("-",re.sub("<[^>]+>","",html.unescape(b)).strip(),"->",U.parse_qs(U.urlparse(html.unescape(a)).query).get("uddg",[a])[0]) for a,b in re.findall(r"result__a\" href=\"([^\"]+)\"[^>]*>(.*?)</a>",t,re.S)[:8]]'
```

- Then READ a chosen result URL as clean, capped text (never dump raw HTML):

```
curl -sL -m 20 -A "Mozilla/5.0" "RESULT_URL" | python3 -c 'import sys,re,html;t=sys.stdin.read();t=re.sub(r"(?is)<(script|style).*?</\1>"," ",t);print(html.unescape(re.sub("<[^>]+>"," ",t)).strip()[:3000])'
```

- If a page returns a block / "Not Acceptable" / login wall, skip it and try the next result.
- For JSON/data APIs, use `curl -sL -m 20 "<url>" | jq '<filter>'` and print only the fields you need.
- Parse with `python3` or `grep -Eo` — never `grep -P` (this is macOS / BSD grep).

## Be terse
- Keep replies short; don't restate the task or echo file contents back.
