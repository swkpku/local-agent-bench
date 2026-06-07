#!/usr/bin/env bash
# Launch pi against the local llama-server model. Extra args pass through to pi,
# e.g. scripts/run_pi.sh -p "Summarize README.md"
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

# Pick a model by registry key: `make pi MODEL=gemma-4-12b-qat`. This resolves the
# key in config/stack.json to its alias (the id pi talks to) and overrides PI_MODEL.
# The same model must be what `make server MODEL=<key>` is currently serving.
if [[ -n "${MODEL:-}" ]]; then
  if ! resolved="$(python3 scripts/models.py resolve "$MODEL")"; then
    exit 2
  fi
  eval "$resolved"
  PI_MODEL="$LLAMA_MODEL_ALIAS"
fi

PI_PROVIDER="${PI_PROVIDER:-localai}"
PI_MODEL="${PI_MODEL:-qwen3.5-9b-q4_k_m}"
PI_SYSTEM_PROMPT="${PI_SYSTEM_PROMPT:-$ROOT_DIR/agents/pi/system.md}"
LLAMA_HOST="${LLAMA_HOST:-127.0.0.1}"
LLAMA_PORT="${LLAMA_PORT:-8080}"

PI_MODELS_FILE="${PI_CONFIG_DIR:-$HOME/.pi/agent}/models.json"

# One-time bootstrap: if pi isn't installed or the local provider isn't
# configured yet, run setup once. (Use `make setup-pi` to re-apply the latest
# templates after editing them.)
if ! command -v pi >/dev/null 2>&1 || ! jq -e '.providers.localai' "$PI_MODELS_FILE" >/dev/null 2>&1; then
  echo "pi not set up yet — running scripts/setup_pi.sh ..." >&2
  "$ROOT_DIR/scripts/setup_pi.sh"
fi

if command -v jq >/dev/null 2>&1 && \
   ! jq -e --arg m "$PI_MODEL" '.providers.localai.models[]? | select(.id == $m)' "$PI_MODELS_FILE" >/dev/null 2>&1; then
  echo "Model '$PI_MODEL' is not registered in $PI_MODELS_FILE." >&2
  echo "Run 'make setup-pi' to register the latest models, then retry." >&2
  exit 1
fi

if ! curl -fsS -m 3 "http://$LLAMA_HOST:$LLAMA_PORT/health" >/dev/null 2>&1; then
  echo "llama-server not reachable at http://$LLAMA_HOST:$LLAMA_PORT" >&2
  echo "Start it in another terminal with: make server" >&2
  exit 1
fi

args=(--provider "$PI_PROVIDER" --model "$PI_MODEL")
if [[ -f "$PI_SYSTEM_PROMPT" ]]; then
  args+=(--append-system-prompt "$PI_SYSTEM_PROMPT")
fi
exec pi "${args[@]}" "$@"
