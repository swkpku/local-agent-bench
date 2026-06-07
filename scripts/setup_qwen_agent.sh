#!/usr/bin/env bash
# Create a Python venv and install Qwen-Agent for talking to the local model.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VENV_DIR="${QWEN_VENV:-.venv}"
REQ="$ROOT_DIR/agents/qwen_agent/requirements.txt"

# Prefer a newer interpreter if present; fall back to python3.
PYBIN=""
for cand in python3.12 python3.11 python3.10 python3; do
  if command -v "$cand" >/dev/null 2>&1; then
    PYBIN="$cand"
    break
  fi
done
if [[ -z "$PYBIN" ]]; then
  echo "No python3 found." >&2
  exit 127
fi
echo "Using $("$PYBIN" --version) at $(command -v "$PYBIN")"

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYBIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install -U pip wheel
"$VENV_DIR/bin/python" -m pip install -U -r "$REQ"
"$VENV_DIR/bin/python" -c "import qwen_agent; print('qwen-agent', getattr(qwen_agent, '__version__', '(version n/a)'))"

echo
echo "Done. Start the server (make server), then run:"
echo "  make qwen-agent"
echo "  scripts/run_qwen_agent.sh 'What is 19*23?'"
