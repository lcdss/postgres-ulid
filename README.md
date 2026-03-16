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

- Exact major tags from `13` and newer
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
CREATE EXTENSION IF NOT EXISTS pgx_ulid;
SELECT gen_ulid();
```

`CREATE EXTENSION` is still required per database. The image includes the
extension files, but Postgres does not enable extensions automatically.

## What This Image Changes

This image keeps the behavior of the official Postgres image and adds the
`pgx_ulid` extension files during the build. That means you still configure and
run PostgreSQL the usual way, but `pgx_ulid` is available to install with SQL.

## How This Repository Works

This repository is mostly automation. It rebuilds selected upstream Postgres
tags, installs `pgx_ulid`, verifies the result with a smoke test, and publishes
the matching image tags to Docker Hub.

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
