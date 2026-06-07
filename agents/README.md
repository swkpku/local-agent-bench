# Agents on the local model

Two agent frameworks are wired to the local `llama-server` running
`qwen3.5-9b-q4_k_m`. Both talk to the OpenAI-compatible endpoint at
`http://127.0.0.1:8080/v1`, so the server must be running first (`make server`).

| Agent | Type | Setup | Run |
| --- | --- | --- | --- |
| [pi](https://pi.dev) | CLI coding agent (Node) | `make setup-pi` | `make pi` |
| [Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) | Python agent framework | `make setup-qwen-agent` | `make qwen-agent` |

## pi

`make setup-pi` installs `@earendil-works/pi-coding-agent` globally and merges two
templates into `~/.pi/agent/` (existing keys kept; timestamped backups made):

- [`pi/models.json`](pi/models.json) → a `localai` provider with `contextWindow 131072`
  and `maxTokens 4096`, pointing at the local server.
- [`pi/settings.json`](pi/settings.json) → context **compaction** sized for a local
  window (`reserveTokens 4096`, `keepRecentTokens 49152`), so pi compacts only when
  nearly full instead of every turn — pi's defaults (`reserveTokens 16384`,
  `keepRecentTokens 20000`) assume 200k–1M-token cloud windows and would thrash on a
  16K local one.

```bash
make pi                         # interactive TUI, pinned to the local model
scripts/run_pi.sh -p "hello"    # one-shot, non-interactive
```

Inside the TUI, `/model` re-reads the config and lets you switch models; `/compact`
compacts context on demand.

`run_pi.sh` also appends [`pi/system.md`](pi/system.md) to pi's system prompt
(`--append-system-prompt`) — context-economy rules so this small, cache-less model
doesn't load whole files/datasets into context. Override the path with
`PI_SYSTEM_PROMPT=…`, or set it empty to skip.

## Qwen-Agent

`make setup-qwen-agent` creates a `.venv` and installs `qwen-agent`. The example
in [`qwen_agent/run.py`](qwen_agent/run.py) builds an `Assistant` pointed at the
local server and registers a small `calculator` tool to demonstrate real
function calling.

```bash
make qwen-agent                              # runs the default demo query
scripts/run_qwen_agent.sh "What is 19*23?"   # custom query
```

Override the target via env (see `.env.example`): `QWEN_BASE_URL`, `QWEN_MODEL`,
`QWEN_API_KEY` (use `EMPTY` for the local server).
