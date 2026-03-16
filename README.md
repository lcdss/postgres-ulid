# postgres-ulid

Publish curated PostgreSQL Alpine images into `lcdss/postgres-ulid` with
`pgx-ulid` installed.

## What It Publishes

This repository publishes exact major upstream `postgres` Alpine tags from
`14-alpine` upward into the Docker Hub repository `lcdss/postgres-ulid`.

Examples:

- `postgres:17-alpine` -> `lcdss/postgres-ulid:17-alpine`
- `postgres:14-alpine` -> `lcdss/postgres-ulid:14-alpine`

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
  "minimum_major": 13,
  "families": ["alpine", "trixie"]
}
```

This mirrors exact major tags from `13` upward for those two families, plus the
floating `alpine` and `trixie` tags. Point-release tags such as
`17.6-alpine3.22` are not selected.
