#!/usr/bin/env bash
set -euo pipefail

echo "System:"
sw_vers
sysctl -n machdep.cpu.brand_string hw.memsize hw.logicalcpu 2>/dev/null || true
echo

echo "Tools:"
for bin in brew llama-server llama-cli python3 curl; do
  if command -v "$bin" >/dev/null 2>&1; then
    printf "  %-14s %s\n" "$bin" "$(command -v "$bin")"
  else
    printf "  %-14s missing\n" "$bin"
  fi
done
echo

echo "Disk:"
df -h .

