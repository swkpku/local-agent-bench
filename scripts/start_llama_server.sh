#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

LLAMA_SERVER_BIN="${LLAMA_SERVER_BIN:-llama-server}"
LLAMA_HOST="${LLAMA_HOST:-127.0.0.1}"
LLAMA_PORT="${LLAMA_PORT:-8080}"
LLAMA_MODEL_ALIAS="${LLAMA_MODEL_ALIAS:-qwen3.5-9b-q4_k_m}"
LLAMA_MODEL_SOURCE="${LLAMA_MODEL_SOURCE:-url}"
LLAMA_HF_REPO="${LLAMA_HF_REPO:-bartowski/Qwen_Qwen3.5-9B-GGUF:Q4_K_M}"
LLAMA_MODEL_URL="${LLAMA_MODEL_URL:-https://huggingface.co/bartowski/Qwen_Qwen3.5-9B-GGUF/resolve/main/Qwen_Qwen3.5-9B-Q4_K_M.gguf}"
LLAMA_MODEL_PATH="${LLAMA_MODEL_PATH:-}"
LLAMA_CTX_SIZE="${LLAMA_CTX_SIZE:-8192}"
LLAMA_N_GPU_LAYERS="${LLAMA_N_GPU_LAYERS:-auto}"
LLAMA_THREADS="${LLAMA_THREADS:-8}"
LLAMA_PARALLEL="${LLAMA_PARALLEL:-1}"
LLAMA_CACHE_DIR="${LLAMA_CACHE_DIR:-.cache/llama.cpp}"
LLAMA_NO_MMPROJ="${LLAMA_NO_MMPROJ:-1}"
LLAMA_REASONING="${LLAMA_REASONING:-off}"

if ! command -v "$LLAMA_SERVER_BIN" >/dev/null 2>&1; then
  echo "Missing $LLAMA_SERVER_BIN. Install it with: brew install llama.cpp" >&2
  exit 127
fi

mkdir -p "$LLAMA_CACHE_DIR"
export LLAMA_CACHE="$ROOT_DIR/$LLAMA_CACHE_DIR"

args=(
  --host "$LLAMA_HOST"
  --port "$LLAMA_PORT"
  --alias "$LLAMA_MODEL_ALIAS"
  --ctx-size "$LLAMA_CTX_SIZE"
  --n-gpu-layers "$LLAMA_N_GPU_LAYERS"
  --threads "$LLAMA_THREADS"
  --parallel "$LLAMA_PARALLEL"
  --reasoning "$LLAMA_REASONING"
  --jinja
)

case "$LLAMA_MODEL_SOURCE" in
  url)
    args+=(--model-url "$LLAMA_MODEL_URL")
    ;;
  hf)
    args+=(--hf-repo "$LLAMA_HF_REPO")
    ;;
  path)
    if [[ -z "$LLAMA_MODEL_PATH" ]]; then
      echo "LLAMA_MODEL_SOURCE=path requires LLAMA_MODEL_PATH=/path/to/model.gguf" >&2
      exit 2
    fi
    args+=(--model "$LLAMA_MODEL_PATH")
    ;;
  *)
    echo "Unknown LLAMA_MODEL_SOURCE: $LLAMA_MODEL_SOURCE" >&2
    exit 2
    ;;
esac

if [[ "$LLAMA_NO_MMPROJ" == "1" || "$LLAMA_NO_MMPROJ" == "true" ]]; then
  args+=(--no-mmproj-auto)
fi

echo "Starting llama-server at http://$LLAMA_HOST:$LLAMA_PORT"
echo "Model alias: $LLAMA_MODEL_ALIAS"
echo "Model source: $LLAMA_MODEL_SOURCE"
exec "$LLAMA_SERVER_BIN" "${args[@]}"
