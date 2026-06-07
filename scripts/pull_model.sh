#!/usr/bin/env bash
# Download the configured GGUF into the llama.cpp cache without starting a server.
# Reuses the same --model-url + cache as scripts/start_llama_server.sh, then
# generates a single token to force the download and confirm the model loads.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

# Pick a model from config/stack.json by key: `make pull-model MODEL=gemma-4-12b-qat`.
if [[ -n "${MODEL:-}" ]]; then
  if ! resolved="$(python3 scripts/models.py resolve "$MODEL")"; then
    exit 2
  fi
  eval "$resolved"
fi

LLAMA_CLI_BIN="${LLAMA_CLI_BIN:-llama-cli}"
LLAMA_MODEL_SOURCE="${LLAMA_MODEL_SOURCE:-url}"
LLAMA_MODEL_URL="${LLAMA_MODEL_URL:-https://huggingface.co/bartowski/Qwen_Qwen3.5-9B-GGUF/resolve/main/Qwen_Qwen3.5-9B-Q4_K_M.gguf}"
LLAMA_HF_REPO="${LLAMA_HF_REPO:-bartowski/Qwen_Qwen3.5-9B-GGUF:Q4_K_M}"
LLAMA_MODEL_PATH="${LLAMA_MODEL_PATH:-}"
LLAMA_CACHE_DIR="${LLAMA_CACHE_DIR:-.cache/llama.cpp}"

if ! command -v "$LLAMA_CLI_BIN" >/dev/null 2>&1; then
  echo "Missing $LLAMA_CLI_BIN. Install it with: make install" >&2
  exit 127
fi

mkdir -p "$LLAMA_CACHE_DIR"
export LLAMA_CACHE="$ROOT_DIR/$LLAMA_CACHE_DIR"

args=(--no-mmproj-auto -n 1 -no-cnv -p "ok")
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

echo "Downloading/validating model into $LLAMA_CACHE ..."
"$LLAMA_CLI_BIN" "${args[@]}" >/dev/null
echo "Model is cached and loads. Start serving with: make server"
