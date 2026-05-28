#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/Open Obsidian.alfredworkflow"
WF="$ROOT/workflow"

if [[ ! -f "$WF/info.plist" || ! -f "$WF/search.py" ]]; then
  echo "Missing workflow files in $WF" >&2
  exit 1
fi

rm -f "$OUT"
(
  cd "$WF"
  zip -qr "$OUT" . -x "*.DS_Store"
)

echo "Built: $OUT"
