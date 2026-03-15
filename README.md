# postgres-ulid

Mirror official PostgreSQL Alpine images into `lcdss/postgres-ulid` with
`pgx-ulid` installed.

## What It Publishes

This repository mirrors every upstream `postgres` tag containing `alpine` into
the Docker Hub repository `lcdss/postgres-ulid`.

Examples:

- `postgres:17-alpine` -> `lcdss/postgres-ulid:17-alpine`
- `postgres:17.6-alpine3.22` -> `lcdss/postgres-ulid:17.6-alpine3.22`

Each mirrored image behaves like the official Postgres image with the
`pgx_ulid` extension installed. The runtime smoke test verifies:

- `CREATE EXTENSION pgx_ulid;`
- `SELECT gen_ulid();`

## Daily Sync

The repository publishes new tags with GitHub Actions using
[`.github/workflows/daily-sync.yml`](.github/workflows/daily-sync.yml).

- Primary trigger: a daily cron run
- Backup trigger: `workflow_dispatch` for manual reruns
- Publish rule: discover upstream tags, filter by `mirror-policy.json`, group
  tags by upstream digest, build once per digest, verify locally, then push all
  matching mirror tags

If the planner finds no missing tags, the publish job is skipped cleanly.

## Required GitHub Secrets

Configure these GitHub Actions values before enabling the daily sync workflow:

- Repository variable: `DOCKERHUB_USERNAME`
- Repository secret: `DOCKERHUB_TOKEN`

The token must have permission to push tags to `lcdss/postgres-ulid`.

## Local Development

Run the unit test suite with:

```bash
python3 -m pytest -v
```

### Local smoke test

Run the image build and runtime verification locally with:

```bash
bash tests/smoke/test_image.sh
```

The smoke test builds from `postgres:17-alpine`, loads the image locally, starts
Postgres, creates `pgx_ulid`, and runs `gen_ulid()`.

## Manual Rerun

To force a sync outside the daily schedule:

1. Open the GitHub Actions tab for this repository
2. Select the `Daily Sync` workflow
3. Use the `Run workflow` button, which is enabled by `workflow_dispatch`

This is useful after credential changes or when you want to force a catch-up
publish run.

## Changing Mirror Scope

The current mirror policy file is [mirror-policy.json](mirror-policy.json):

```json
{
  "mode": "alpine-only"
}
```

To expand the mirror in the future without changing code, switch the mode to
`all-tags`:

```json
{
  "mode": "all-tags"
}
```
