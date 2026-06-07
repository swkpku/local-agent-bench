#!/usr/bin/env bash
# Measure EXACT prefill (prompt) and decode (generation) speed from a live
# llama-server via its /completion `timings` block. Start the server first
# (e.g. `make server`), then run this. Prints prefill/decode tok/s as JSON.
#
# Usage: bash evals/bench_perf.sh [HOST:PORT]   (default 127.0.0.1:8080)
set -euo pipefail
EP="${1:-127.0.0.1:8080}"
URL="http://$EP/completion"

if ! curl -fsS "http://$EP/health" >/dev/null 2>&1; then
  echo "llama-server not reachable at $EP — start it with: make server" >&2
  exit 1
fi

# A non-trivial prompt forces real prefill; n_predict forces real decode.
PROMPT="Write a detailed 400-word explanation of how unified memory bandwidth limits LLM token generation speed on Apple Silicon. Be specific and technical."
RESP=$(curl -fsS "$URL" -H 'Content-Type: application/json' -d @- <<JSON
{"prompt": "$PROMPT", "n_predict": 400, "temperature": 0.2, "cache_prompt": false}
JSON
)
echo "$RESP" | python3 -c '
import sys,json
t=json.load(sys.stdin).get("timings",{})
out={
  "prefill_tokens_per_sec": round(t.get("prompt_per_second",0),1),
  "decode_tokens_per_sec":  round(t.get("predicted_per_second",0),1),
  "prompt_n": t.get("prompt_n"),
  "predicted_n": t.get("predicted_n"),
  "prompt_ms": round(t.get("prompt_ms",0),1),
  "predicted_ms": round(t.get("predicted_ms",0),1),
}
print(json.dumps(out, indent=2))
'
