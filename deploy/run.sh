#!/usr/bin/env bash
# Wrapper used by cron. Runs the export and appends output to a daily log file.
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"
mkdir -p logs

"$APP_DIR/venv/bin/python" main.py >> "logs/export_$(date +%F).log" 2>&1
