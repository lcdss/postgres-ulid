#!/usr/bin/env bash
set -euo pipefail

image=${1:?usage: verify-image.sh <image>}
default_container="postgres-ulid-verify-default-$$"
preload_container="postgres-ulid-verify-preload-$$"

cleanup() {
  docker rm -f "$default_container" >/dev/null 2>&1 || true
  docker rm -f "$preload_container" >/dev/null 2>&1 || true
}

wait_for_ready() {
  local container=$1

  for attempt in $(seq 1 30); do
    if docker exec "$container" pg_isready -U postgres >/dev/null 2>&1; then
      return 0
    fi

    if ! docker ps --format '{{.Names}}' | grep -Fxq "$container"; then
      docker logs "$container"
      exit 1
    fi

    sleep 1

    if [ "$attempt" -eq 30 ]; then
      docker logs "$container"
      exit 1
    fi
  done
}

retry_psql_script() {
  local container=$1
  local database=$2
  local script=$3

  for attempt in $(seq 1 30); do
    if docker exec -i \
      "$container" \
      psql -v ON_ERROR_STOP=1 -U postgres -d "$database" >/dev/null 2>&1 <<<"$script"; then
      return 0
    fi

    if ! docker ps --format '{{.Names}}' | grep -Fxq "$container"; then
      docker logs "$container"
      exit 1
    fi

    sleep 1

    if [ "$attempt" -eq 30 ]; then
      docker logs "$container"
      exit 1
    fi
  done
}

trap cleanup EXIT

docker run -d \
  --name "$default_container" \
  -e POSTGRES_PASSWORD=postgres \
  "$image" >/dev/null

wait_for_ready "$default_container"

retry_psql_script "$default_container" postgres "
SELECT extname FROM pg_extension WHERE extname = 'pgx_ulid';
SELECT gen_ulid();
SELECT 'CREATE DATABASE verify_template1 TEMPLATE template1'
WHERE NOT EXISTS (
  SELECT 1
  FROM pg_database
  WHERE datname = 'verify_template1'
) \\gexec
\\connect verify_template1
SELECT extname FROM pg_extension WHERE extname = 'pgx_ulid';
SELECT gen_ulid();
"

docker run -d \
  --name "$preload_container" \
  -e POSTGRES_PASSWORD=postgres \
  "$image" \
  postgres -c shared_preload_libraries=pgx_ulid >/dev/null

wait_for_ready "$preload_container"

retry_psql_script "$preload_container" postgres "
SELECT gen_monotonic_ulid();
"
