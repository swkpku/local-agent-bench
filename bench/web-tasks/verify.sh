#!/usr/bin/env bash
# Re-fetch the pinned sources and print the gold answers, to confirm the pins
# still resolve. All URLs are immutable (release tag / fixed revision id /
# fixed commit SHA), so these values should never change.
set -euo pipefail

echo "=== WB1: GitHub release API — Flask 3.0.0 ==="
curl -fsSL "https://api.github.com/repos/pallets/flask/releases/tags/3.0.0" \
  | jq -r '"published_date=\(.published_at[0:10])  asset_count=\(.assets|length)  asset_size_sum=\([.assets[].size]|add)"'

echo "=== WB2: Wikipedia fixed revision 512000000 ==="
curl -fsSL "https://en.wikipedia.org/w/rest.php/v1/revision/512000000" \
  | jq -r '"page=\(.page.title)  editor=\(.user.name)  size=\(.size)"'

echo "=== WB3: pinned raw CSV (seaborn-data tips.csv @ fixed SHA) ==="
SHA=799924f46906146ad36b8b1c27d83e51dd8b411a
curl -fsSL "https://raw.githubusercontent.com/mwaskom/seaborn-data/$SHA/tips.csv" \
  | python3 -c "import sys,pandas as pd; d=pd.read_csv(sys.stdin); print(f'rows={len(d)}  total_bill_sum={round(d[\"total_bill\"].sum(),2)}  mean_tip={round(d[\"tip\"].mean(),2)}')"
