#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=$(which python3)

cd "$DIR"
$PYTHON mind.py >> "$DIR/cron.log" 2>&1

# Ergebnisse pushen
git add journal.md state.json >> "$DIR/cron.log" 2>&1
git diff --cached --quiet || git commit -m "local session $(date +%s)" >> "$DIR/cron.log" 2>&1
git push >> "$DIR/cron.log" 2>&1
