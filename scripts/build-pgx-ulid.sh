#!/bin/sh
set -eux

pg_config_path="$(sh /usr/local/bin/find-pg-config.sh)"
export LIBCLANG_PATH="$(dirname "$(find /usr/lib -name 'libclang.so*' | head -n1)")"

git clone --depth 1 --branch "${PGX_ULID_REF}" "${PGX_ULID_REPO}" /tmp/pgx_ulid

cd /tmp/pgx_ulid
pgrx_version="$(sed -nE 's/^pgrx[[:space:]]*=[[:space:]]*"\^?([0-9]+\.[0-9]+\.[0-9]+)".*/\1/p' Cargo.toml | head -n1)"
cargo install cargo-pgrx --locked --version "${pgrx_version}"
cargo pgrx init --pg"${PG_MAJOR}"="${pg_config_path}"
cargo pgrx install --release --pg-config "${pg_config_path}"

sh /usr/local/bin/stage-extension-artifacts.sh "${pg_config_path}" /out
