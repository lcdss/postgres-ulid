ARG BASE_IMAGE
ARG SOURCE_DIGEST

FROM ${BASE_IMAGE} AS builder

ARG PGX_ULID_REPO=https://github.com/pksunkara/pgx_ulid.git
ARG PGX_ULID_REF=master

ENV CARGO_HOME=/usr/local/cargo
ENV RUSTUP_HOME=/usr/local/rustup
ENV PATH=/usr/local/cargo/bin:${PATH}

COPY scripts/install-build-deps.sh /usr/local/bin/install-build-deps.sh
COPY scripts/find-pg-config.sh /usr/local/bin/find-pg-config.sh
COPY scripts/stage-extension-artifacts.sh /usr/local/bin/stage-extension-artifacts.sh

RUN set -eux; \
    sh /usr/local/bin/install-build-deps.sh; \
    pg_config_path="$(sh /usr/local/bin/find-pg-config.sh)"; \
    export LIBCLANG_PATH="$(dirname "$(find /usr/lib -name 'libclang.so*' | head -n1)")"; \
    cargo install cargo-pgrx --locked; \
    git clone --depth 1 --branch "${PGX_ULID_REF}" "${PGX_ULID_REPO}" /tmp/pgx_ulid; \
    cd /tmp/pgx_ulid; \
    cargo pgrx init --pg"${PG_MAJOR}"="${pg_config_path}"; \
    cargo pgrx install --release --pg-config "${pg_config_path}"; \
    sh /usr/local/bin/stage-extension-artifacts.sh "${pg_config_path}" /out

FROM ${BASE_IMAGE}

ARG BASE_IMAGE
ARG SOURCE_DIGEST

LABEL org.opencontainers.image.base.name="${BASE_IMAGE}" \
      io.github.lcdss.postgres-ulid.source-digest="${SOURCE_DIGEST}"

COPY --from=builder /out/ /

CMD ["postgres", "-c", "shared_preload_libraries=pgx_ulid"]
