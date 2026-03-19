#!/usr/bin/env bash
set -euo pipefail

docker build \
  --load \
  -f Dockerfile.alpine \
  --build-arg BASE_IMAGE=docker.io/library/postgres:17-alpine \
  -t postgres-ulid:test-alpine .

./scripts/verify-image.sh postgres-ulid:test-alpine

docker build \
  --load \
  -f Dockerfile.debian \
  --build-arg BASE_IMAGE=docker.io/library/postgres:17-trixie \
  -t postgres-ulid:test-debian .

./scripts/verify-image.sh postgres-ulid:test-debian
