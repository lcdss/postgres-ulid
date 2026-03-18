#!/bin/sh
set -eu

if command -v apk >/dev/null 2>&1; then
  apk add --no-cache --virtual .build-deps \
    bash \
    build-base \
    clang \
    curl \
    git \
    llvm-dev \
    openssl-dev \
    pkgconf

  clang_pkg="$(apk info | grep -E '^clang[0-9]+$' | head -n1)"
  apk add --no-cache "${clang_pkg}-libclang"
  curl -fsSL https://sh.rustup.rs | sh -s -- \
    -y \
    --profile minimal \
    --default-toolchain stable \
    --component rustfmt
  exit 0
fi

if command -v apt-get >/dev/null 2>&1; then
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
    libssl-dev \
    llvm-dev \
    pkg-config
  curl -fsSL https://sh.rustup.rs | sh -s -- \
    -y \
    --profile minimal \
    --default-toolchain stable \
    --component rustfmt
  rm -rf /var/lib/apt/lists/*
  exit 0
fi

echo "unsupported package manager: expected apk or apt-get" >&2
exit 1
