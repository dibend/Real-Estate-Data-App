#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python not found: $PYTHON_BIN" >&2
  exit 1
fi

"$PYTHON_BIN" -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install .

cat <<'EOF'

Setup complete.

Next steps:
  1. ./scripts/download-data.sh
  2. ./.venv/bin/python app.py

Optional:
  - ./scripts/generate-dev-cert.sh
  - ./.venv/bin/python app.py --http3 --host 0.0.0.0 --port 8443
EOF
