#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVELOPMENT_ENV_FILE="$SCRIPT_DIR/../../sd-central-configs/backend/envs/development.env"
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

print_divider() {
  echo "------------------------------"
}

DEVELOPMENT_DATABASE_URL="$(read_database_url "$DEVELOPMENT_ENV_FILE")"
STAGING_DATABASE_URL="$(read_database_url "$STAGING_ENV_FILE")"

print_divider
echo "copying from staging: $STAGING_DATABASE_URL"
print_divider
echo "copying to development: $DEVELOPMENT_DATABASE_URL"
print_divider

read -r -p "Do you wanna proceed? [y/N] " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
  echo "Cancelled."
  exit 0
fi

sh scripts/copy_postgres.sh "$STAGING_DATABASE_URL" "$DEVELOPMENT_DATABASE_URL"
