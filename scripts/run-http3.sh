#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
exec .venv/bin/python -m zhvi_dashboard --http3 --host 0.0.0.0 --port 8443 "$@"
