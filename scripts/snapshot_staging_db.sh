#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGING_ENV_FILE="$SCRIPT_DIR/../../sd-central-configs/backend/envs/staging.env"

read_database_url() {
  local env_file="$1"

  if [[ ! -f "$env_file" ]]; then
    echo "Missing env file: $env_file" >&2
    exit 1
  fi

  (
    set -a
    source "$env_file"
    set +a
    if [[ -z "${DATABASE_URL:-}" ]]; then
      echo "DATABASE_URL is not set in $env_file" >&2
      exit 1
    fi
    echo "$DATABASE_URL"
  )
}

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Error: python not found in PATH (required to generate snapshot filename)." >&2
  exit 1
fi

TIMESTAMP="$($PYTHON_BIN - <<'PY'
from datetime import datetime

def format_sortable_date(date=None):
    date = date or datetime.now()
    return date.strftime("%Y-%m-%d_%H-%M-%S")

print(format_sortable_date())
PY
)"

SNAPSHOT_DIR="$SCRIPT_DIR/../snapshots"
SNAPSHOT_FILE="$SNAPSHOT_DIR/${TIMESTAMP}.sql"

mkdir -p "$SNAPSHOT_DIR"

STAGING_DATABASE_URL="$(read_database_url "$STAGING_ENV_FILE")"

sh "$SCRIPT_DIR/dump_postgres_to_file.sh" "$STAGING_DATABASE_URL" "$SNAPSHOT_FILE"

echo "Snapshot created: $SNAPSHOT_FILE"
