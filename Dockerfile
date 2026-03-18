ARG BASE_IMAGE

FROM ${BASE_IMAGE} AS builder

ARG PGX_ULID_REPO=https://github.com/pksunkara/pgx_ulid.git
ARG PGX_ULID_REF=master

ENV CARGO_HOME=/usr/local/cargo
ENV RUSTUP_HOME=/usr/local/rustup
ENV PATH=/usr/local/cargo/bin:${PATH}

COPY scripts/install-build-deps.sh /usr/local/bin/install-build-deps.sh

RUN set -eux; \
    sh /usr/local/bin/install-build-deps.sh; \
    export LIBCLANG_PATH="$(dirname "$(find /usr/lib -name 'libclang.so*' | head -n1)")"; \
    cargo install cargo-pgrx --locked; \
    git clone --depth 1 --branch "${PGX_ULID_REF}" "${PGX_ULID_REPO}" /tmp/pgx_ulid; \
    cd /tmp/pgx_ulid; \
    cargo pgrx init --pg"${PG_MAJOR}"=/usr/local/bin/pg_config; \
    cargo pgrx install --release --pg-config /usr/local/bin/pg_config; \
    install -d /out/lib /out/extension; \
    cp /usr/local/lib/postgresql/*ulid*.so /out/lib/; \
    cp /usr/local/share/postgresql/extension/*ulid* /out/extension/

FROM ${BASE_IMAGE}

COPY --from=builder /out/lib/ /usr/local/lib/postgresql/
COPY --from=builder /out/extension/ /usr/local/share/postgresql/extension/
