#!/usr/bin/env bash
set -euo pipefail

image=${1:?usage: verify-image.sh <image>}
container="postgres-ulid-verify-$$"

cleanup() {
  docker rm -f "$container" >/dev/null 2>&1 || true
}

trap cleanup EXIT

docker run -d \
  --name "$container" \
  -e POSTGRES_PASSWORD=postgres \
  "$image" >/dev/null

for attempt in $(seq 1 30); do
  if docker exec "$container" pg_isready -U postgres >/dev/null 2>&1; then
    break
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

for attempt in $(seq 1 30); do
  if docker exec \
    "$container" \
    psql -v ON_ERROR_STOP=1 -U postgres -d postgres \
    -c "CREATE EXTENSION pgx_ulid; SELECT gen_ulid(); SELECT gen_monotonic_ulid();" >/dev/null 2>&1; then
    exit 0
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
