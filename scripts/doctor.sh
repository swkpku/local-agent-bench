#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "System:"
sw_vers
sysctl -n machdep.cpu.brand_string hw.memsize hw.logicalcpu 2>/dev/null || true
echo

echo "Tools:"
for bin in brew llama-server llama-cli node npm pi jq python3 curl; do
  if command -v "$bin" >/dev/null 2>&1; then
    printf "  %-14s %s\n" "$bin" "$(command -v "$bin")"
  else
    printf "  %-14s missing\n" "$bin"
  fi
done
echo

echo "Agents:"
if command -v pi >/dev/null 2>&1; then
  printf "  %-22s %s\n" "pi version" "$(pi --version </dev/null 2>&1 | head -1 || echo present)"
  if [[ -f "$HOME/.pi/agent/models.json" ]] && jq -e '.providers.localai' "$HOME/.pi/agent/models.json" >/dev/null 2>&1; then
    printf "  %-22s %s\n" "pi local provider" "configured"
  else
    printf "  %-22s %s\n" "pi local provider" "not configured (make setup-pi)"
  fi
else
  printf "  %-22s %s\n" "pi" "missing (make setup-pi)"
fi
if [[ -x ".venv/bin/python" ]]; then
  printf "  %-22s %s\n" "qwen-agent venv" "$(.venv/bin/python -c 'import qwen_agent; print(getattr(qwen_agent, "__version__", "present"))' 2>/dev/null || echo "present, qwen-agent missing (make setup-qwen-agent)")"
else
  printf "  %-22s %s\n" "qwen-agent venv" "missing (make setup-qwen-agent)"
fi
echo

echo "Disk:"
df -h .
