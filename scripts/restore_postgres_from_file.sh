#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <input_file> <destination_postgres_url>" >&2
  exit 1
fi

INPUT_FILE="$1"
DEST_URL="$2"

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Error: input file not found: $INPUT_FILE" >&2
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "Error: psql not found in PATH." >&2
  exit 1
fi

psql "$DEST_URL" < "$INPUT_FILE"
