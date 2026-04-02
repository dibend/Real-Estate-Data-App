#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

CERT_DIR="${1:-certs}"
CERT_FILE="$CERT_DIR/dev-cert.pem"
KEY_FILE="$CERT_DIR/dev-key.pem"

mkdir -p "$CERT_DIR"

openssl req \
  -x509 \
  -newkey rsa:2048 \
  -sha256 \
  -days 365 \
  -nodes \
  -keyout "$KEY_FILE" \
  -out "$CERT_FILE" \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

chmod 600 "$KEY_FILE"

echo "Created $CERT_FILE and $KEY_FILE"
