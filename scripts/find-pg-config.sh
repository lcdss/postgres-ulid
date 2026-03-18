#!/bin/sh
set -eu

if [ "${PG_CONFIG_SKIP_PATH:-0}" != "1" ] && command -v pg_config >/dev/null 2>&1; then
  command -v pg_config
  exit 0
fi

search_roots=${PG_CONFIG_SEARCH_ROOTS:-"/usr/local/bin /usr/lib/postgresql /usr/local/pgsql/bin"}

if [ -n "${PG_MAJOR:-}" ]; then
  for root in $search_roots; do
    candidate="$root/$PG_MAJOR/bin/pg_config"
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      exit 0
    fi
  done
fi

for root in $search_roots; do
  for candidate in \
    "$root/pg_config" \
    "$root"/*/pg_config \
    "$root"/*/*/pg_config
  do
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      exit 0
    fi
  done
done

echo "pg_config not found" >&2
exit 1
