#!/usr/bin/env bash
set -euo pipefail

docker build \
  --load \
  --build-arg BASE_IMAGE=docker.io/library/postgres:17-alpine \
  -t postgres-ulid:test .

./scripts/verify-image.sh postgres-ulid:test
