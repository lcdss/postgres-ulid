#!/bin/sh
set -eu

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends \
  bash \
  build-essential \
  ca-certificates \
  clang \
  curl \
  git \
  libclang-dev \
  libpq-dev \
  libssl-dev \
  llvm-dev \
  pkg-config \
  postgresql-server-dev-${PG_MAJOR} \
  zlib1g-dev

curl -fsSL https://sh.rustup.rs | sh -s -- \
  -y \
  --profile minimal \
  --default-toolchain stable \
  --component rustfmt

rm -rf /var/lib/apt/lists/*
