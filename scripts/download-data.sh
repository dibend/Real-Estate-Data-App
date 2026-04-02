#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

OUT_FILE="${1:-zillow-zip-data.csv}"
LOG_FILE="${2:-zillow-out.log}"
URL="https://files.zillowstatic.com/research/public_csvs/zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv"

if command -v curl >/dev/null 2>&1; then
  curl -fL "$URL" -o "$OUT_FILE"
elif command -v wget >/dev/null 2>&1; then
  wget -o "$LOG_FILE" "$URL" -O "$OUT_FILE"
else
  echo "Neither curl nor wget is available." >&2
  exit 1
fi

echo "Downloaded Zillow ZHVI ZIP dataset to $OUT_FILE"
