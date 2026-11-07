#!/usr/bin/env bash
set -euo pipefail
SIM_URL="${1:?usage: ./run.sh <SIM_URL>}"
exec python controller.py "$SIM_URL" --db "${FORMI_DB:-state/controller.sqlite3}"
