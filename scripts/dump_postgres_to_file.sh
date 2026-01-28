#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <source_postgres_url> [output_file]" >&2
  exit 1
fi

SOURCE_URL="$1"
OUTPUT_FILE="${2:-}"

if [[ -z "$OUTPUT_FILE" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Error: python not found in PATH (required to generate output filename)." >&2
    exit 1
  fi

  TIMESTAMP="$("$PYTHON_BIN" - <<'PY'
from datetime import datetime

def format_sortable_date(date=None):
    date = date or datetime.now()
    return date.strftime("%Y-%m-%d_%H-%M-%S")

print(format_sortable_date())
PY
)"

  OUTPUT_DIR="replicas"
  OUTPUT_FILE="${OUTPUT_DIR}/${TIMESTAMP}.sql"
fi

USE_DOCKER_PG_DUMP="${USE_DOCKER_PG_DUMP:-1}"
DOCKER_IMAGE="${DOCKER_IMAGE:-postgres:16}"
DOCKER_SOURCE_URL="${DOCKER_SOURCE_URL:-}"

if [[ "$USE_DOCKER_PG_DUMP" != "1" ]]; then
  if ! command -v pg_dump >/dev/null 2>&1; then
    echo "Error: pg_dump not found in PATH." >&2
    echo "Tip: set USE_DOCKER_PG_DUMP=1 to use ${DOCKER_IMAGE}." >&2
    exit 1
  fi
fi

# Ensure output directory exists when using a relative path.
OUTPUT_DIRNAME="$(dirname "$OUTPUT_FILE")"
if [[ "$OUTPUT_DIRNAME" != "." ]]; then
  mkdir -p "$OUTPUT_DIRNAME"
fi

# Use plain SQL so psql can restore directly.
if [[ "$USE_DOCKER_PG_DUMP" == "1" ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker not found in PATH." >&2
    exit 1
  fi

  if [[ -z "$DOCKER_SOURCE_URL" ]]; then
    DOCKER_SOURCE_URL="$SOURCE_URL"
    DOCKER_SOURCE_URL="${DOCKER_SOURCE_URL/localhost/host.docker.internal}"
    DOCKER_SOURCE_URL="${DOCKER_SOURCE_URL/127.0.0.1/host.docker.internal}"
  fi

  docker run --rm "$DOCKER_IMAGE" \
    pg_dump --format=plain --no-owner --no-privileges "$DOCKER_SOURCE_URL" > "$OUTPUT_FILE"
else
  pg_dump --format=plain --no-owner --no-privileges "$SOURCE_URL" > "$OUTPUT_FILE"
fi
