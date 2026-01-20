#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <source_postgres_url> <destination_postgres_url>" >&2
  exit 1
fi

SOURCE_URL="$1"
DEST_URL="$2"

if ! command -v pg_dump >/dev/null 2>&1; then
  echo "Error: pg_dump not found in PATH." >&2
  exit 1
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "Error: psql not found in PATH." >&2
  exit 1
fi

# Use plain SQL so psql can restore directly.
pg_dump --format=plain --no-owner --no-privileges "$SOURCE_URL" | psql "$DEST_URL"
