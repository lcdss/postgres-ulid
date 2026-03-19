#!/bin/sh
set -eu

apk add --no-cache --virtual .build-deps \
  bash \
  build-base \
  clang \
  curl \
  git \
  llvm-dev \
  openssl-dev \
  pkgconf \
  rust \
  rustfmt \
  cargo

clang_pkg="$(apk info | grep -E '^clang[0-9]+$' | head -n1)"
apk add --no-cache "${clang_pkg}-libclang"
