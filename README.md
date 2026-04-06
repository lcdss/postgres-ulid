# postgres-ulid

`lcdss/postgres-ulid` is a small wrapper around the official PostgreSQL Docker
image with the [`pgx_ulid`](https://github.com/pksunkara/pgx_ulid) extension
already installed.

If you already use the official Postgres image, this one should feel familiar:
the main difference is that you can enable `pgx_ulid` inside your database and
start generating ULIDs immediately.

Upstream projects:

- Official Postgres image: <https://hub.docker.com/_/postgres>
- Official Postgres image repository: <https://github.com/docker-library/postgres>
- `pgx_ulid`: <https://github.com/pksunkara/pgx_ulid>

## Available Tags

This repository mirrors selected tags from the official `postgres` image into
`lcdss/postgres-ulid`.

Current mirror policy:

- Exact major tags from `14` and newer
- The `alpine` and `trixie` image families
- The floating `alpine` and `trixie` tags

Examples:

- `lcdss/postgres-ulid:17-alpine`
- `lcdss/postgres-ulid:17-trixie`
- `lcdss/postgres-ulid:alpine`
- `lcdss/postgres-ulid:trixie`

## How To Use

Run a Postgres container the same way you normally would, but use one of the
`lcdss/postgres-ulid` tags instead of the upstream image:

```bash
docker run -d \
  --name postgres-ulid \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  lcdss/postgres-ulid:17-alpine
```

Then connect and enable the extension in the database where you want to use it:

```bash
docker exec -it postgres-ulid psql -U postgres -d postgres
```

```sql
SELECT gen_ulid();
```

On a fresh data directory, the image enables `pgx_ulid` automatically in the
default `postgres` database and in `template1`, so new databases inherit it as
well.

If you also want monotonic ULIDs, start PostgreSQL with an explicit preload
flag:

```bash
docker run -d \
  --name postgres-ulid-monotonic \
  -e POSTGRES_PASSWORD=postgres \
  lcdss/postgres-ulid:17-alpine \
  postgres -c shared_preload_libraries=pgx_ulid
```

Then:

```sql
SELECT gen_monotonic_ulid();
```

## What This Image Changes

This image keeps the behavior of the official Postgres image and adds the
`pgx_ulid` extension files during the build. On first initialization it also
enables the extension in `postgres` and `template1`, so the default database
and newly created databases have the native `ulid` type and can use
`gen_ulid()` immediately.

The image does not preload `pgx_ulid` by default. If you want
`gen_monotonic_ulid()`, pass `postgres -c shared_preload_libraries=pgx_ulid`
when starting the container.

## How This Repository Works

This repository is mostly automation. It rebuilds selected upstream Postgres
tags, installs `pgx_ulid`, verifies the result with Alpine and Debian-family
smoke builds, and publishes the matching image tags to Docker Hub.

If you only want to use the image, the sections above are the important part.

## Development

Run the test suite with:

```bash
python3 -m pytest -v
```

Run the local smoke test with:

```bash
bash tests/smoke/test_image.sh
```

That smoke script builds both:

- `Dockerfile.alpine` against `postgres:17-alpine`
- `Dockerfile.debian` against `postgres:17-trixie`
