#!/usr/bin/env bash
# Run the Qwen-Agent example against the local llama-server model.
# Extra args become the query: scripts/run_qwen_agent.sh "What is 19*23?"
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

VENV_DIR="${QWEN_VENV:-.venv}"
LLAMA_HOST="${LLAMA_HOST:-127.0.0.1}"
LLAMA_PORT="${LLAMA_PORT:-8080}"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Qwen-Agent venv missing. Run: make setup-qwen-agent" >&2
  exit 127
fi

if ! curl -fsS -m 3 "http://$LLAMA_HOST:$LLAMA_PORT/health" >/dev/null 2>&1; then
  echo "llama-server not reachable at http://$LLAMA_HOST:$LLAMA_PORT" >&2
  echo "Start it in another terminal with: make server" >&2
  exit 1
fi

exec "$VENV_DIR/bin/python" agents/qwen_agent/run.py "$@"
