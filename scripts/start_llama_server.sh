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

# Pick a model from config/stack.json by key: `make server MODEL=gemma-4-12b-qat`.
# This overrides any model pinned in .env; list options with `make list-models`.
if [[ -n "${MODEL:-}" ]]; then
  if ! resolved="$(python3 scripts/models.py resolve "$MODEL")"; then
    exit 2
  fi
  eval "$resolved"
fi

LLAMA_SERVER_BIN="${LLAMA_SERVER_BIN:-llama-server}"
LLAMA_HOST="${LLAMA_HOST:-127.0.0.1}"
LLAMA_PORT="${LLAMA_PORT:-8080}"
LLAMA_MODEL_ALIAS="${LLAMA_MODEL_ALIAS:-qwen3.5-9b-q4_k_m}"
LLAMA_MODEL_SOURCE="${LLAMA_MODEL_SOURCE:-url}"
LLAMA_HF_REPO="${LLAMA_HF_REPO:-bartowski/Qwen_Qwen3.5-9B-GGUF:Q4_K_M}"
LLAMA_MODEL_URL="${LLAMA_MODEL_URL:-https://huggingface.co/bartowski/Qwen_Qwen3.5-9B-GGUF/resolve/main/Qwen_Qwen3.5-9B-Q4_K_M.gguf}"
LLAMA_MODEL_PATH="${LLAMA_MODEL_PATH:-}"
LLAMA_CACHE_DIR="${LLAMA_CACHE_DIR:-.cache/llama.cpp}"
LLAMA_NO_MMPROJ="${LLAMA_NO_MMPROJ:-1}"

# Core runtime (agentic defaults for a 16 GB Apple Silicon Mac)
LLAMA_CTX_SIZE="${LLAMA_CTX_SIZE:-131072}"
LLAMA_N_GPU_LAYERS="${LLAMA_N_GPU_LAYERS:-auto}"
LLAMA_THREADS="${LLAMA_THREADS:-4}"
LLAMA_PARALLEL="${LLAMA_PARALLEL:-1}"
LLAMA_REASONING="${LLAMA_REASONING:-off}"

# Throughput / memory
LLAMA_FLASH_ATTN="${LLAMA_FLASH_ATTN:-on}"
LLAMA_CACHE_TYPE_K="${LLAMA_CACHE_TYPE_K:-q8_0}"   # q8_0 KV requires flash-attn on
LLAMA_CACHE_TYPE_V="${LLAMA_CACHE_TYPE_V:-q8_0}"
LLAMA_BATCH="${LLAMA_BATCH:-2048}"
LLAMA_UBATCH="${LLAMA_UBATCH:-1024}"

# Server-side sampling defaults (clients still override per request)
LLAMA_TEMP="${LLAMA_TEMP:-0.2}"
LLAMA_TOP_P="${LLAMA_TOP_P:-0.8}"
LLAMA_TOP_K="${LLAMA_TOP_K:-20}"
LLAMA_SEED="${LLAMA_SEED:-}"

# Optional endpoints
LLAMA_METRICS="${LLAMA_METRICS:-0}"

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
  --flash-attn "$LLAMA_FLASH_ATTN"
  --cache-type-k "$LLAMA_CACHE_TYPE_K"
  --cache-type-v "$LLAMA_CACHE_TYPE_V"
  --batch-size "$LLAMA_BATCH"
  --ubatch-size "$LLAMA_UBATCH"
  --temp "$LLAMA_TEMP"
  --top-p "$LLAMA_TOP_P"
  --top-k "$LLAMA_TOP_K"
  --jinja
)

if [[ -n "$LLAMA_SEED" ]]; then
  args+=(--seed "$LLAMA_SEED")
fi

if [[ "$LLAMA_METRICS" == "1" || "$LLAMA_METRICS" == "true" ]]; then
  args+=(--metrics)
fi

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
echo "Model: $LLAMA_MODEL_ALIAS (source: $LLAMA_MODEL_SOURCE)"
echo "Agentic profile: ctx=$LLAMA_CTX_SIZE flash_attn=$LLAMA_FLASH_ATTN kv=$LLAMA_CACHE_TYPE_K/$LLAMA_CACHE_TYPE_V threads=$LLAMA_THREADS ubatch=$LLAMA_UBATCH"
echo "Sampling defaults: temp=$LLAMA_TEMP top_p=$LLAMA_TOP_P top_k=$LLAMA_TOP_K"
exec "$LLAMA_SERVER_BIN" "${args[@]}"
