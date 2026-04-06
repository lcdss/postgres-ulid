#!/usr/bin/env bash
set -euo pipefail

psql_args=(
  -v ON_ERROR_STOP=1
  --username "${POSTGRES_USER:-postgres}"
)

declare -A databases=()

databases["postgres"]=1
databases["template1"]=1
databases["${POSTGRES_DB:-postgres}"]=1

for database in "${!databases[@]}"; do
  psql "${psql_args[@]}" --dbname "$database" <<'SQL'
CREATE EXTENSION IF NOT EXISTS pgx_ulid;
SQL
done
