#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <source_postgres_url> <output_file>" >&2
  exit 1
fi

SOURCE_URL="$1"
OUTPUT_FILE="$2"

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
