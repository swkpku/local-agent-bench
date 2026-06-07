#!/usr/bin/env bash
# Install the pi coding agent (if needed) and register the local llama-server
# model plus context/compaction settings sized for a small local window.
# Idempotent: existing providers/settings are preserved (timestamped backups).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PI_PACKAGE="${PI_PACKAGE:-@earendil-works/pi-coding-agent}"
PI_CONFIG_DIR="${PI_CONFIG_DIR:-$HOME/.pi/agent}"
MODELS_TEMPLATE="$ROOT_DIR/agents/pi/models.json"
SETTINGS_TEMPLATE="$ROOT_DIR/agents/pi/settings.json"

if ! command -v pi >/dev/null 2>&1; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm is required to install pi. Install Node.js (e.g. via nvm) first." >&2
    exit 127
  fi
  echo "Installing $PI_PACKAGE ..."
  npm install -g --ignore-scripts "$PI_PACKAGE"
fi
echo "pi: $(command -v pi) ($(pi --version </dev/null 2>&1 | head -1 || echo '?'))"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required to merge the pi config. Install jq and re-run." >&2
  exit 127
fi

mkdir -p "$PI_CONFIG_DIR"

# Deep-merge a template into an existing pi config file (template wins on
# conflicts), preserving any other keys. Backs up the original first.
merge_json() {
  local target="$1" template="$2"
  if [[ -f "$target" ]]; then
    local backup="$target.bak.$(date +%Y%m%d%H%M%S)"
    cp "$target" "$backup"
    local tmp
    tmp="$(mktemp)"
    jq -s '.[0] * .[1]' "$target" "$template" >"$tmp"
    mv "$tmp" "$target"
    echo "Merged $(basename "$template") into $target (backup: $backup)"
  else
    cp "$template" "$target"
    echo "Wrote $target"
  fi
}

# Provider + model (16K window, 4K max output to match the agentic server profile)
merge_json "$PI_CONFIG_DIR/models.json" "$MODELS_TEMPLATE"
# Context compaction sized for a local window (pi's defaults assume 200k-1M clouds)
merge_json "$PI_CONFIG_DIR/settings.json" "$SETTINGS_TEMPLATE"

echo
echo "Done. Start the server (make server), then run:"
echo "  make pi                          # interactive TUI on the local model"
echo "  scripts/run_pi.sh -p 'hello'     # one-shot, non-interactive"
